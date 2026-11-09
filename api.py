from fastapi import FastAPI

app = FastAPI(title="Game Mechanics RAG API")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "game-mechanics-rag-api",
    }
