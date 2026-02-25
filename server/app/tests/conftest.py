import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from server.app.main import app
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


class SlowSummarizerAgent(SummarizerAgent):
    """Simulates an LLM that never responds — used to test timeout handling."""

    def __init__(self):
        pass

    async def summarize_text(self, text: str) -> str:
        await asyncio.sleep(60)
        return "should never get here"


@pytest.fixture
def mock_service() -> SummarizerService:
    return SummarizeWithAgent(MockSummarizerAgent())


@pytest.fixture
def failing_service() -> SummarizerService:
    return SummarizeWithAgent(FailingSummarizerAgent())


@pytest.fixture
def timeout_service() -> SummarizerService:
    return SummarizeWithAgent(SlowSummarizerAgent(), timeout=0.1)


@pytest.fixture
async def client(mock_service: SummarizerService):
    app.state.summarizer_service = mock_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def failing_client(failing_service: SummarizerService):
    app.state.summarizer_service = failing_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def timeout_client(timeout_service: SummarizerService):
    app.state.summarizer_service = timeout_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
