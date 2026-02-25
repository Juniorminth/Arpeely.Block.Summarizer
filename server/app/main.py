from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from server.app.api.summarize_controller import router as summarizer_router
from server.app.infrastructure.config import settings
from server.app.services.summarizer.agent.summarizer_agent import SummarizerAgentFactory
from server.app.services.summarizer.summarizer_service import SummarizeWithAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = SummarizerAgentFactory.create_agent(settings.openai_model)
    app.state.summarizer_service = SummarizeWithAgent(agent, timeout=settings.llm_timeout_seconds)
    yield


app = FastAPI(
    title="Arpeely Block Summarizer",
    description="Summarizes web page content blocks using an LLM agent.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summarizer_router)
@app.get("/", include_in_schema=False)
def health_check():
    return  JSONResponse(status_code=200, content={"status": "healthy"})

@app.get("/ready", include_in_schema=False)
def ready_check():
    return  JSONResponse(status_code=200, content={"status": "ready"})

if __name__ == "__main__":
    uvicorn.run("server.app.main:app", host="0.0.0.0", port=8000, reload=True)
