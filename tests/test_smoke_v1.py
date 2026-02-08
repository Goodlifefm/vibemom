import inspect

from src.bot import handlers as v1_handlers
from src.bot import services as v1_services
from src.bot.renderer import render_project_post


def test_v1_smoke_imports_and_render():
    assert callable(v1_handlers.setup_routers)
    assert inspect.iscoroutinefunction(v1_services.match_request_to_projects)

    text = render_project_post(
        title="Title",
        description="Description",
        stack="Stack",
        link="Link",
        price="Price",
        contact="Contact",
    )
    assert "Title" in text
