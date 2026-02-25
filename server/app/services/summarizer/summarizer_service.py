import asyncio
import logging
from abc import ABC, abstractmethod

from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgent

logger = logging.getLogger("arpeely.service")


class SummarizerService(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")


class SummarizeWithAgent(SummarizerService):
    def __init__(self, agent: SummarizerAgent, timeout: float = 30.0):
        self._agent = agent
        self._timeout = timeout

    async def summarize(self, text: str) -> str:
        try:
            return await asyncio.wait_for(
                self._agent.summarize_text(text),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            logger.error("LLM timed out after %ss", self._timeout)
            raise RuntimeError(f"Summarization timed out after {self._timeout}s")
