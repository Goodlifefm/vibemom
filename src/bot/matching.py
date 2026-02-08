"""Matching rules from SPEC 07. Scoring buyer_request -> projects."""

import re
from dataclasses import dataclass

STOP_WORDS = {
    "Рё", "РІ", "РІРѕ", "РЅРµ", "С‡С‚Рѕ", "РѕРЅ", "РЅР°", "СЏ", "СЃ", "СЃРѕ", "РєР°Рє", "Р°", "С‚Рѕ", "РІСЃРµ",
    "РѕРЅР°", "С‚Р°Рє", "РµРіРѕ", "РЅРѕ", "РґР°", "С‚С‹", "Рє", "Сѓ", "Р¶Рµ", "РІС‹", "Р·Р°", "Р±С‹", "РїРѕ",
    "С‚РѕР»СЊРєРѕ", "РµС‘", "РјРЅРµ", "Р±С‹Р»Рѕ", "РІРѕС‚", "РѕС‚", "РјРµРЅСЏ", "РµС‰С‘", "РЅРµС‚", "Рѕ", "РёР·", "РµРјСѓ",
    "С‚РµРїРµСЂСЊ", "РєРѕРіРґР°", "СѓР¶Рµ", "РІР°Рј", "РЅРё", "Р±С‹", "РґРѕ", "РІР°СЃ", "РЅРёР±СѓРґСЊ", "РѕРїСЏС‚СЊ",
    "РЅСѓ", "РёР»Рё", "СЌС‚Рѕ", "Рј", "РґР»СЏ", "РјС‹", "РїРѕРґ", "РµСЃС‚СЊ", "Р±РµР·", "СЂР°Р·", "Рґ", "Р»Рё",
}


def _tokenize(text: str) -> set[str]:
    text = (text or "").lower()
    # Keep "mojibake" Cyrillic (e.g. Р±Р°Р·Р°) as a single token by splitting on whitespace/punctuation only.
    text = re.sub(r"[\\t\\r\\n]+", " ", text)
    text = re.sub(r"""[\\.,;:!\\?\\(\\)\\[\\]\\{\\}<>\"'`]+""", " ", text)
    words = [w for w in text.split(" ") if w]
    return {w for w in words if len(w) > 1 and w not in STOP_WORDS}


@dataclass
class MatchResult:
    project_id: str
    score: int


def score_match(
    request_what: str,
    request_budget: str,
    project_title: str,
    project_description: str,
    project_price: str,
) -> int:
    """
    Keyword overlap: +10 per matching word (max +50).
    Budget mention: if request budget ~ project price: +20.
    Threshold for showing: >= 10.
    """
    score = 0
    req_tokens = _tokenize(request_what)
    proj_tokens = _tokenize(project_title + " " + project_description)
    overlap = req_tokens & proj_tokens
    keyword_score = min(len(overlap) * 10, 50)
    score += keyword_score

    budget_clean = (request_budget or "").strip().lower()
    price_clean = (project_price or "").strip().lower()
    # SPEC 07: never show random suggestions. Budget-only similarity must not pass the threshold.
    if keyword_score > 0 and budget_clean and budget_clean not in ("РЅРµ РІР°Р¶РЅРѕ", "РїРѕ Р·Р°РїСЂРѕСЃСѓ", "РЅРµРІР°¶РЅРѕ"):
        if any(c.isdigit() for c in budget_clean) and any(c.isdigit() for c in price_clean):
            score += 20
        elif "РїРѕ Р·Р°РїСЂРѕСЃСѓ" in price_clean or "РїРѕ Р·Р°РїСЂРѕСЃСѓ" in budget_clean:
            score += 10

    return score


def filter_and_sort_matches(
    request_what: str,
    request_budget: str,
    projects: list[dict],
    threshold: int = 10,
) -> list[dict]:
    """Return projects with score >= threshold, sorted by score desc."""
    scored: list[tuple[dict, int]] = []
    for p in projects:
        s = score_match(
            request_what,
            request_budget,
            p.get("title", ""),
            p.get("description", ""),
            p.get("price", ""),
        )
        if s >= threshold:
            scored.append((p, s))
    scored.sort(key=lambda x: -x[1])
    return [p for p, _ in scored]

