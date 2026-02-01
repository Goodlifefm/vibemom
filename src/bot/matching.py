"""Matching rules from SPEC 07. Scoring buyer_request -> projects."""

import re
from dataclasses import dataclass

STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все",
    "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по",
    "только", "её", "мне", "было", "вот", "от", "меня", "ещё", "нет", "о", "из", "ему",
    "теперь", "когда", "уже", "вам", "ни", "бы", "до", "вас", "нибудь", "опять",
    "ну", "или", "это", "м", "для", "мы", "под", "есть", "без", "раз", "д", "ли",
}


def _tokenize(text: str) -> set[str]:
    text = (text or "").lower()
    words = re.findall(r"[а-яёa-z0-9]+", text)
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
    if budget_clean and budget_clean not in ("не важно", "по запросу", "неважно"):
        if any(c.isdigit() for c in budget_clean) and any(c.isdigit() for c in price_clean):
            score += 20
        elif "по запросу" in price_clean or "по запросу" in budget_clean:
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
