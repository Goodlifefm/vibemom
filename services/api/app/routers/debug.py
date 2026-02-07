"""
Debug endpoints (temporary).

This router is intentionally minimal and must never echo secrets.
It exists to identify the real Origin / preflight headers coming from Telegram WebView.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
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

def _apply_permissive_cors(request: Request, response: Response) -> None:
    """
    Maximally permissive CORS for /debug/echo to diagnose Telegram WebView.

    Always active: this endpoint is temporary and never returns secrets.
    Overrides any CORSMiddleware headers so that even unknown / null origins
    get a valid Access-Control-Allow-Origin.
    """
    origin = request.headers.get("origin")
    # If origin is missing, use '*' (safe here: this endpoint never returns secrets).
    response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"

    acr_headers = request.headers.get("access-control-request-headers")
    response.headers["Access-Control-Allow-Headers"] = acr_headers or "*"
    # 10 minutes
    response.headers["Access-Control-Max-Age"] = "600"


@router.options("/debug/echo", include_in_schema=False)
async def debug_echo_options(request: Request) -> Response:
    response = Response(status_code=204)
    _apply_permissive_cors(request, response)
    return response


@router.get(
    "/debug/echo",
    response_model=DebugEchoResponse,
    response_model_exclude_none=True,
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

    # Apply permissive CORS to help diagnose Telegram WebView behavior.
    # Overrides CORSMiddleware for this endpoint so even exotic origins work.
    response = JSONResponse(content=payload.model_dump(exclude_none=True))
    _apply_permissive_cors(request, response)
    return response  # type: ignore[return-value]
