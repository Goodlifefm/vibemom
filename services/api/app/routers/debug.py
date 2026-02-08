"""
Debug endpoints (temporary).

This router is intentionally minimal and must never echo secrets.
It exists to identify the real Origin / preflight headers coming from Telegram WebView.
"""

import json
import uuid
from datetime import datetime, timezone

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

MAX_CLIENT_LOG_BYTES = 16 * 1024


_SUSPICIOUS_VALUE_SUBSTRINGS = [
    # Telegram WebApp initData fragment and related parameters.
    "tgwebappdata=",
    "auth_date=",
    "signature=",
    "hash=",
    # Generic auth material that must never end up in logs.
    "authorization",
    "bearer ",
]


def _redact(value: object) -> object:
    if isinstance(value, str):
        lower = value.lower()
        if any(s in lower for s in _SUSPICIOUS_VALUE_SUBSTRINGS):
            return "[redacted]"
        return value
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        out: dict[str, object] = {}
        for key, nested in value.items():
            lower = str(key).lower()
            if (
                "initdata" in lower
                or "authorization" in lower
                or "token" in lower
                or "cookie" in lower
                or "password" in lower
            ):
                out[str(key)] = "[redacted]"
                continue
            out[str(key)] = _redact(nested)  # type: ignore[arg-type]
        return out
    return value


def _coerce_str(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _safe_tap(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None

    allow = ["ts", "type", "x", "y", "targetTag", "targetId"]
    out: dict[str, object] = {}
    for key in allow:
        if key in value:
            out[key] = value[key]
    return out or None


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


@router.options("/debug/client-log", include_in_schema=False)
async def debug_client_log_options(request: Request) -> Response:
    response = Response(status_code=204)
    _apply_permissive_cors(request, response)
    return response


@router.post(
    "/debug/client-log",
    summary="Receive client diagnostic log (no auth, no secrets)",
    description=(
        "Accepts a small JSON payload from the webapp for debugging Telegram WebView issues. "
        "No auth. No cookies. Payload is size-limited and redacted in logs."
    ),
)
async def debug_client_log(request: Request) -> JSONResponse:
    request_id = str(uuid.uuid4())
    received_at = datetime.now(timezone.utc).isoformat()

    raw = await request.body()
    origin = request.headers.get("origin")
    user_agent = request.headers.get("user-agent")
    if user_agent:
        user_agent = user_agent[:160]

    if raw and len(raw) > MAX_CLIENT_LOG_BYTES:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Payload too large", "code": "PAYLOAD_TOO_LARGE"},
        )
        _apply_permissive_cors(request, response)
        return response

    data: object
    if not raw:
        data = {}
    else:
        try:
            data = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception as exc:
            data = {
                "_parse_error": str(exc)[:200],
                "_raw_snippet": raw[:512].decode("utf-8", errors="replace"),
            }

    build_sha: str | None = None
    tap: dict[str, object] | None = None
    if isinstance(data, dict):
        build_sha = _coerce_str(data.get("build_sha")) or None
        if not build_sha:
            build = data.get("build")
            if isinstance(build, dict):
                build_sha = _coerce_str(build.get("sha")) or _coerce_str(build.get("git_sha")) or None

        tap_value = data.get("lastTap") or data.get("tap")
        tap = _safe_tap(tap_value) if tap_value is not None else None

    # Required verification line: easy to grep and correlate with UI.
    print(
        json.dumps(
            {
                "tag": "CLIENT_LOG",
                "request_id": request_id,
                "origin": origin,
                "ua": user_agent,
                "build_sha": build_sha,
                "tap": tap,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ),
        flush=True,
    )

    # Never log the full payload (even redacted). Keep only a small safe summary.
    parse_error: str | None = None
    if isinstance(data, dict) and isinstance(data.get("_parse_error"), str):
        parse_error = str(data.get("_parse_error"))[:200]

    keys: list[str] | None = None
    if isinstance(data, dict):
        keys = sorted([str(k) for k in data.keys()])[:60]

    logger.info(
        "Client log",
        extra={
            "extra": {
                "request_id": request_id,
                "origin": origin or "-",
                "method": request.method,
                "path": request.url.path,
                "user_agent": user_agent or "-",
                "bytes": len(raw or b""),
                "build_sha": (build_sha[:12] if isinstance(build_sha, str) else None),
                "tap": _redact(tap) if tap else None,
                "keys": keys,
                "parse_error": parse_error,
            }
        },
    )

    response = JSONResponse(
        content={
            "ok": True,
            "request_id": request_id,
            "received_at": received_at,
        }
    )
    _apply_permissive_cors(request, response)
    return response
