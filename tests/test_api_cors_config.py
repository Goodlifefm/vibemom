from __future__ import annotations

import re
import sys
from pathlib import Path


API_SERVICE_ROOT = Path(__file__).resolve().parents[1] / "services" / "api"
if str(API_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(API_SERVICE_ROOT))

from app.config import Settings  # noqa: E402


def test_cors_origins_include_first_party_vibemom_domains() -> None:
    settings = Settings(webapp_url="https://vibemom.vercel.app/")
    origins = settings.get_cors_origins()

    assert "https://vibemom.vercel.app" in origins
    assert "https://vibemom.ru" in origins
    assert "https://www.vibemom.ru" in origins
    assert "https://app.vibemom.ru" in origins


def test_cors_origin_regex_accepts_vibemom_and_vercel_origins() -> None:
    settings = Settings()
    regex = settings.get_cors_origin_regex()
    assert regex is not None

    allowed = (
        "https://vibemom.ru",
        "https://www.vibemom.ru",
        "https://app.vibemom.ru",
        "https://miniapp-preview.vercel.app",
    )
    blocked = (
        "https://vibemom.ru.evil.com",
        "https://evil-vercel.app.evil.com",
        "http://vibemom.ru",
    )

    for origin in allowed:
        assert re.match(regex, origin), f"Origin must be allowed: {origin}"

    for origin in blocked:
        assert not re.match(regex, origin), f"Origin must be blocked: {origin}"
