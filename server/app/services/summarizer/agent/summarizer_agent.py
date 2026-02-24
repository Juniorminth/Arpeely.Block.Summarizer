import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import TypedDict, NotRequired

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph


class SummarizeState(TypedDict):
	text_to_summarize:str
	sanitized_text:NotRequired[str]
	summary: NotRequired[str]
	
	
class NodeNames(str, Enum):
	SANITIZING = "sanitizing"
	SUMMARIZING = "summarizing"


class SummarizerAgent(ABC):
	def __init__(self, llm_config):
		self._llm_model = llm_config
		self._graph = self._build_graph()
		
	def _needs_sanitization(self, text: str) -> bool:
		# Flags non-standard characters that suggest HTML/markup or encoded content
		return bool(re.search(r"[^a-zA-Z0-9\s\-.,!?'\":;()]", text))

	def _decide_sanitization(self, state: SummarizeState):
		given_text = state.get("text_to_summarize", None)
		if given_text is None:
			return NodeNames.SUMMARIZING
		should_sanitize = self._needs_sanitization(given_text)
		return NodeNames.SANITIZING if should_sanitize else NodeNames.SUMMARIZING
		
	
	
	async def _sanitize_text_node(self, state: SummarizeState):
		text = state.get("text_to_summarize", "")
		prompt = f"""You are a text sanitization assistant.
		Your task is to clean the following text by:
		- Removing all HTML tags (e.g. <div>, <p>, <br>, etc.)
		- Removing HTML entities (e.g. &amp;, &nbsp;, &#39;, etc.)
		- Removing any code snippets, scripts, or markup language
		- Removing URLs and file paths
		- Keeping only natural readable text with standard punctuation (letters, digits, spaces, and: . , ! ? ' " : ; - ( ))
		- Preserving the original meaning and sentence structure
		- Do NOT summarize or rephrase — only clean the text

		Return ONLY the cleaned text, with no explanation or commentary.

		Text to sanitize:
		{text}"""
		result = await self._llm_model.ainvoke(input=[HumanMessage(content=prompt)])
		return {"sanitized_text": result.content}
	
	async def _summarize_text_node(self, state: SummarizeState):
		text = state.get("sanitized_text", state.get("text_to_summarize", ""))
		prompt = f"""You are a text summarization assistant.
		Your task is to summarize the following text while preserving its original meaning and key information.
		The summary should be concise, clear, and coherent, capturing the main points and essence of the text without losing important details.

		Text to summarize:
		{text}"""
		result = await self._llm_model.ainvoke(input=[HumanMessage(content=prompt)])
		return {"summary": result.content}
	
	def _build_graph(self) -> CompiledStateGraph:
		graph = StateGraph(SummarizeState)  # type: ignore[arg-type]

		graph.add_node(NodeNames.SANITIZING, self._sanitize_text_node)  # type: ignore[arg-type]
		graph.add_node(NodeNames.SUMMARIZING, self._summarize_text_node)  # type: ignore[arg-type]

		graph.add_conditional_edges(START, self._decide_sanitization, {
			NodeNames.SANITIZING: NodeNames.SANITIZING,
			NodeNames.SUMMARIZING: NodeNames.SUMMARIZING,
		})
		graph.add_edge(NodeNames.SANITIZING, NodeNames.SUMMARIZING)
		return graph.compile()
	
	@abstractmethod
	async def summarize_text(self, text:str) -> str:
		pass
	
	
	
class SummarizerAgentOpenAI(SummarizerAgent):

	def __init__(self, model: str):
		llm = ChatOpenAI(model=model, temperature=0.1)
		super().__init__(llm)

	async def summarize_text(self, text: str) -> str:
		try:
			state = {"text_to_summarize": text}
			result_state = await self._graph.ainvoke(state)  # type: ignore[arg-type]
			summary = result_state.get("summary", "")
			if not summary:
				raise RuntimeError("LLM returned an empty summary.")
			return summary
		except Exception as e:
			raise RuntimeError(f"Summarization failed: {e}") from e


_MODEL_REGISTRY: dict[str, type[SummarizerAgent]] = {
	"gpt": SummarizerAgentOpenAI,
}


class SummarizerAgentFactory:
	@staticmethod
	def create_agent(model: str) -> SummarizerAgent:
		for key, agent_class in _MODEL_REGISTRY.items():
			if key in model.lower():
				return agent_class(model=model)  # type: ignore[call-arg]
		raise NotImplementedError(f"No agent registered for model: '{model}'")
