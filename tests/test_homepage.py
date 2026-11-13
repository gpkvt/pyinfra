"""Regression tests for Homepage's custom bookmark column layout."""

from conftest import ROOT


def test_homepage_bookmark_columns_are_controlled_by_custom_css():
    """The CSS targets each bookmark group without changing service rows."""
    css = (ROOT / "files/homepage/custom.css").read_text()
    assert ".bookmark-group" in css
    assert "flex-basis: 25%" in css



def test_homepage_task_deploys_custom_css_and_restarts_on_change():
    """The custom stylesheet is deployed to Homepage's bind-mounted config."""
    task = (ROOT / "tasks/docker/homepage.py").read_text()
    assert 'src="files/homepage/custom.css"' in task
    assert 'config/custom.css' in task
    assert "restart_if=[homepage_icons, homepage_custom_css]" in task
