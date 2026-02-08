import inspect

from src.v2 import routers as v2_routers
from src.v2.fsm import V2FormSteps
from src.v2.repo import submission as v2_submission
from src.v2.rendering.project_renderer import render_project_post_html


def test_v2_smoke_imports_and_render():
    assert callable(v2_routers.setup_v2_routers)
    assert V2FormSteps is not None
    assert inspect.iscoroutinefunction(v2_submission.get_submission)

    html = render_project_post_html({"title": "Title", "description": "Description"})
    assert "<b>" in html
