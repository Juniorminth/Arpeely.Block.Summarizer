import pytest
from httpx import AsyncClient


async def test_summarize_returns_200(client: AsyncClient):
    response = await client.post("/api/summarize/", json={"text": "This is a valid block of text."})
    assert response.status_code == 200


async def test_summarize_response_contains_mock_prefix(client: AsyncClient):
    response = await client.post("/api/summarize/", json={"text": "Hello world"})
    assert response.json()["summary"].startswith("mock summary of:")


async def test_summarize_response_shape(client: AsyncClient):
    response = await client.post("/api/summarize/", json={"text": "Some valid text"})
    assert set(response.json().keys()) == {"summary"}


async def test_summarize_empty_text_returns_422(client: AsyncClient):
    response = await client.post("/api/summarize/", json={"text": ""})
    assert response.status_code == 422


async def test_summarize_whitespace_only_returns_422(client: AsyncClient):
    response = await client.post("/api/summarize/", json={"text": "     "})
    assert response.status_code == 422


async def test_summarize_missing_field_returns_422(client: AsyncClient):
    response = await client.post("/api/summarize/", json={})
    assert response.status_code == 422


async def test_summarize_llm_failure_returns_502(failing_client: AsyncClient):
    response = await failing_client.post("/api/summarize/", json={"text": "Some valid text"})
    assert response.status_code == 502
    assert "LLM is down" in response.json()["detail"]


async def test_summarize_long_text(client: AsyncClient):
    long_text = "word " * 500
    response = await client.post("/api/summarize/", json={"text": long_text})
    assert response.status_code == 200
    assert "summary" in response.json()


async def test_summarize_timeout_returns_502(timeout_client: AsyncClient):
    response = await timeout_client.post("/api/summarize/", json={"text": "Some valid text"})
    assert response.status_code == 502
    assert "timed out" in response.json()["detail"]
