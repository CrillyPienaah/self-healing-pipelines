from fastapi import FastAPI

app = FastAPI(
    title="Self-Healing Pipelines API",
    version="0.1.0"
)


@app.get("/")
async def root():
    return {"message": "Self-Healing Pipeline Platform API", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/v1/pipelines")
async def list_pipelines():
    return {"pipelines": [], "count": 0}
