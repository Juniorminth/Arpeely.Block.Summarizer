import logging
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import TypedDict, NotRequired

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

logger = logging.getLogger("arpeely.agent")


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
		
	# Matches http/https/ftp URLs — checked before the character allowlist
	_URL_RE = re.compile(r"https?://|ftp://", re.IGNORECASE)

	# Matches characters that suggest HTML/markup or encoded content.
	# Uses \w (Unicode-aware in Python 3) so accented letters from any
	# script (French é, German ö, Spanish ñ, etc.) are treated as clean text.
	# Explicitly allows typographic punctuation common in normal web prose:
	#   \u2013  en dash       –
	#   \u2014  em dash       —
	#   \u2018  left single quote   '
	#   \u2019  right single quote  '  (also used as apostrophe)
	#   \u201c  left double quote   "
	#   \u201d  right double quote  "
	#   \u2026  ellipsis       …
	#   /       slash (prose use: "and/or", fractions)
	#   %       percent
	_DIRTY_CHARS_RE = re.compile(r"[^\w\s\-\u2013\u2014.,!?''\u2018\u2019\"\u201c\u201d:;()/\u2026%]")

	def _needs_sanitization(self, text: str) -> bool:
		if self._URL_RE.search(text):
			logger.info("Sanitization triggered — reason=url_detected")
			return True
		match = self._DIRTY_CHARS_RE.search(text)
		if match:
			# Collect up to 5 unique offending characters for the log
			dirty = set(self._DIRTY_CHARS_RE.findall(text))
			sample = list(dirty)[:5]
			logger.info("Sanitization triggered — reason=dirty_chars, chars=%r", sample)
			return True
		return False

	def _decide_sanitization(self, state: SummarizeState):
		given_text = state.get("text_to_summarize", None)
		if given_text is None:
			return NodeNames.SUMMARIZING
		should_sanitize = self._needs_sanitization(given_text)
		route = NodeNames.SANITIZING if should_sanitize else NodeNames.SUMMARIZING
		logger.info("Routing decision — sanitize=%s, text_length=%d", should_sanitize, len(given_text))
		return route
		
	
	
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
		if not text:
			return {"summary": "I'm sorry but I can't summarize an empty text"}
		prompt = f"""You are a summarization assistant. Your task is to compress the text below into the shortest possible statement that captures its single core idea.

		Rules:
		- Output 4 sentences for short inputs, 8 sentences maximum for long ones — never more
		- DO NOT restate every point; identify the one thing the text is really saying
		- DO NOT paraphrase sentence by sentence — that is not a summary
		- No filler openers like "The text discusses..." or "The author states..."
		- If the input is already short and focused, your summary must be noticeably shorter than the input
		- Output only the summary, nothing else

		Text:
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
		llm = ChatOpenAI(model=model, temperature=0.1, max_tokens=400)
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
