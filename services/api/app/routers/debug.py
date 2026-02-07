"""
Debug endpoints (temporary).

This router is intentionally minimal and must never echo secrets.
It exists to identify the real Origin / preflight headers coming from Telegram WebView.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.logging_config import get_logger


logger = get_logger(__name__)


class DebugEchoResponse(BaseModel):
    origin: str | None = None
    method: str
    path: str
    access_control_request_method: str | None = None
    access_control_request_headers: str | None = None
    user_agent: str | None = None


router = APIRouter(tags=["Debug"])


@router.get(
    "/debug/echo",
    response_model=DebugEchoResponse,
    summary="Echo safe request metadata (no secrets)",
    description=(
        "Returns only a small allowlisted subset of request headers "
        "to diagnose Telegram WebView CORS issues."
    ),
)
async def debug_echo(request: Request) -> DebugEchoResponse:
    # Only allowlisted headers. Do NOT add authorization/cookies/initData here.
    origin = request.headers.get("origin")
    acr_method = request.headers.get("access-control-request-method")
    acr_headers = request.headers.get("access-control-request-headers")

    user_agent = request.headers.get("user-agent")
    if user_agent:
        user_agent = user_agent[:120]

    payload = DebugEchoResponse(
        origin=origin,
        method=request.method,
        path=request.url.path,
        access_control_request_method=acr_method,
        access_control_request_headers=acr_headers,
        user_agent=user_agent,
    )

    # Safe to log: allowlisted values only.
    logger.info(
        "Debug echo",
        extra={
            "extra": {
                "origin": origin or "-",
                "method": request.method,
                "path": request.url.path,
                "acr_method": acr_method or "-",
                "acr_headers": acr_headers or "-",
                "user_agent": user_agent or "-",
            }
        },
    )

    return payload

