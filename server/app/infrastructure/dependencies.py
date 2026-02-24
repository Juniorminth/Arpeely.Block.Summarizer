from functools import lru_cache

from server.app.infrastructure.config import settings
from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgentFactory
from server.app.services.summarizer.summarizer_service import SummarizerService, SummarizeWithAgent


@lru_cache(maxsize=1)
def get_summarizer_service() -> SummarizerService:
    agent = SummarizerAgentFactory.create_agent(settings.openai_model)
    return SummarizeWithAgent(agent)

