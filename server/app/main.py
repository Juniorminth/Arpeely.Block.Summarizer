import uvicorn
from fastapi import FastAPI

from server.app.api.summarize_controller import router as summarizer_router

app = FastAPI(
    title="Arpeely Block Summarizer",
    description="Summarizes web page content blocks using an LLM agent.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(summarizer_router)

if __name__ == "__main__":
    uvicorn.run("server.app.main:app", host="0.0.0.0", port=8000, reload=True)
