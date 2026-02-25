import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from server.app.services.summarizer.summarizer_service import SummarizerService
from server.app.infrastructure.dependencies import get_summarizer_service

logger = logging.getLogger("arpeely.api")

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
    text_len = len(request.text)
    logger.info("Summarize request received — text_length=%d", text_len)
    try:
        summary = await service.summarize(request.text)
        logger.info("Summarize success — text_length=%d, summary_length=%d", text_len, len(summary))
        return SummarizeResponse(summary=summary)
    except RuntimeError as e:
        logger.error("Summarize failed — text_length=%d, error=%s", text_len, e)
        raise HTTPException(status_code=502, detail=str(e))
