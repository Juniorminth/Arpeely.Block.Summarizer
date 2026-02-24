import pytest
from httpx import AsyncClient, ASGITransport

from server.app.main import app
from server.app.infrastructure.dependencies import get_summarizer_service
from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgent
from server.app.services.summarizer.summarizer_service import SummarizerService, SummarizeWithAgent


class MockSummarizerAgent(SummarizerAgent):
    """Bypasses LLM and graph entirely — returns a deterministic summary."""

    def __init__(self):
        pass  # skip llm + graph build

    async def summarize_text(self, text: str) -> str:
        return f"mock summary of: {text[:30]}"


class FailingSummarizerAgent(SummarizerAgent):
    """Always raises RuntimeError — used to test 502 handling."""

    def __init__(self):
        pass

    async def summarize_text(self, text: str) -> str:
        raise RuntimeError("LLM is down")


@pytest.fixture
def mock_service() -> SummarizerService:
    return SummarizeWithAgent(MockSummarizerAgent())


@pytest.fixture
def failing_service() -> SummarizerService:
    return SummarizeWithAgent(FailingSummarizerAgent())


@pytest.fixture
async def client(mock_service: SummarizerService):
    app.dependency_overrides[get_summarizer_service] = lambda: mock_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def failing_client(failing_service: SummarizerService):
    app.dependency_overrides[get_summarizer_service] = lambda: failing_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

