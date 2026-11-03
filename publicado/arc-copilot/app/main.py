from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.api.users import router as users_router
from app.core.config import BASE_DIR, get_settings
from app.database import models  # noqa: F401
from app.database.session import Base, SessionLocal, engine, ensure_pgvector
from app.field import router as field_router
from app.seed import seed_demo
from app.web import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_pgvector(engine)
    Base.metadata.create_all(bind=engine)
    if get_settings().demo_mode:
        with SessionLocal() as db:
            seed_demo(db)
    yield


app = FastAPI(
    title="Arc Copilot API",
    version="1.0.0",
    description="Assistente de obras com confirmação humana, RDO e rastreabilidade.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.include_router(api_router)
app.include_router(users_router)
app.include_router(web_router)
app.include_router(field_router)


@app.get("/health")
def health():
    settings = get_settings()
    return {"status": "ok", "mode": "ai" if settings.ai_mode else "demo"}
