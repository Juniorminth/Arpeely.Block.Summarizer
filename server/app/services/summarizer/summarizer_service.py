from abc import ABC, abstractmethod

from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgent


class SummarizerService(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class SummarizeWithAgent(SummarizerService):
    def __init__(self, agent: SummarizerAgent):
        self._agent = agent

    async def summarize(self, text: str) -> str:
        return await self._agent.summarize_text(text)
