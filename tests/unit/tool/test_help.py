from sequel.tool.help_pages import create_help

import pytest

HELP_PAGES = create_help()

@pytest.mark.parametrize("page_name", [page.name for page in HELP_PAGES.ordered_pages()])
def test_help_pages(page_name):
    HELP_PAGES.navigate(start_links=[page_name], interactive=False)
