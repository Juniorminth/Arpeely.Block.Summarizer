from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from server.app.services.summarizer.summarizer_service import SummarizerService
from server.app.infrastructure.dependencies import get_summarizer_service

router = APIRouter(prefix="/api/summarize", tags=["text_summarization"])


class SummarizeRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class SummarizeResponse(BaseModel):
    summary: str


@router.post("/", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    service: SummarizerService = Depends(get_summarizer_service),
) -> SummarizeResponse:
    try:
        summary = await service.summarize(request.text)
        return SummarizeResponse(summary=summary)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

