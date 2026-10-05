import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .errors import register_exception_handlers
from .routers import admin, assessments, auth, concepts, sessions

settings = get_settings()

if settings.jwt_secret == "change_me_jwt_secret":
    logging.getLogger("dbcas").warning(
        "JWT_SECRET is the development default — set a real secret for "
        "any deployment reachable by others."
    )

app = FastAPI(title="DBCAS API", version="0.1.0")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Baseline hardening headers on every response (NFR security)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(concepts.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/ping")
def ping():
    return {"message": "pong"}
