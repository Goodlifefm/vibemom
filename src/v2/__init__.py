"""V2 namespace: repo layer, FSM, routers, services, keyboards. Wired under feature flag."""
from src.v2.rendering.project_renderer import (
    render_project_post_html,
    render_submission_to_html,
    submission_answers_to_blocks,
    render_post,
    render_for_feed,
    project_to_feed_answers,
)
from src.v2.services.renderers.post_text import (
    render_price,
    render_price_from_answers,
    render_post_text,
)

__all__ = [
    # Rendering
    "render_project_post_html",
    "render_submission_to_html",
    "submission_answers_to_blocks",
    "render_post",
    "render_for_feed",
    "project_to_feed_answers",
    # Services
    "render_price",
    "render_price_from_answers",
    "render_post_text",
]
