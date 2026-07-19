"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return service liveness and version."""
    return {"status": "ok", "version": "0.1.0"}
