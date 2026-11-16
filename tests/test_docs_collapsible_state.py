"""Documentation asset configuration tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_collapsible_state_script_is_loaded_by_mkdocs():
    """The documentation build includes the disclosure persistence script."""
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "extra_javascript:" in config
    assert "  - javascripts/collapsible-state.js" in config


def test_collapsible_state_is_saved_and_restored_per_page():
    """Disclosure preferences survive reloads without changing defaults."""
    script = (
        ROOT / "docs/javascripts/collapsible-state.js"
    ).read_text(encoding="utf-8")

    assert 'window.localStorage.setItem(key, event.target.open ? "open" : "closed")' in script
    assert 'window.localStorage.getItem(key)' in script
    assert "document$.subscribe(restoreDisclosureStates)" in script
    assert 'window.location.pathname' in script
    assert 'details.open = savedState === "open"' in script
