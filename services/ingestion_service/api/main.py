import uvicorn
from fastapi import FastAPI

from api.router import router

app = FastAPI(title="RiteCare Ingestion Service", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8005, reload=False)
