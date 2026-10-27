from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import BASE_DIR, get_settings
from app.database import models  # noqa: F401
from app.database.session import Base, engine
from app.field import router as field_router
from app.web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Arc Copilot API",
    version="1.0.0",
    description="Assistente de obras com confirmação humana, RDO e rastreabilidade.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.include_router(api_router)
app.include_router(web_router)
app.include_router(field_router)


@app.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "mode": "ai" if settings.ai_mode else "demo"}
