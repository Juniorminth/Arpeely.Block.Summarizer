from fastapi import Request

from server.app.services.summarizer.summarizer_service import SummarizerService


def get_summarizer_service(request: Request) -> SummarizerService:
    return request.app.state.summarizer_service

