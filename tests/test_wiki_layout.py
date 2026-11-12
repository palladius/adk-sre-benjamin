from pathlib import Path

# Resolve from this file so the tests pass regardless of pytest's working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = REPO_ROOT / "src" / "static"


def _read(name: str) -> str:
    path = STATIC_DIR / name
    assert path.exists(), f"{name} must exist"
    return path.read_text(encoding="utf-8")


def test_wiki_edit_active_css():
    content = _read("index.css")

    # Assert that the class exists to collapse layout
    assert ".app-container.wiki-edit-active" in content, "wiki-edit-active styling must be defined in index.css"

    # Assert that it targets sidebar and chat column to hide them
    assert "sidebar" in content, "sidebar styling should be present"
    assert "chat-column" in content, "chat-column styling should be present"

    # Assert wiki focus badge and responsive height rules
    assert "wiki-edit-badge" in content, "wiki-edit-badge should be defined in index.css"
    assert "calc(100vh - 280px)" in content, "expanded responsive editor height should be present"
    # Badge visibility is class-driven, not via inline style + !important
    assert ".wiki-panel.edit-mode .wiki-edit-badge" in content


def test_wiki_edit_active_js():
    content = _read("index.js")

    # Assert that index.js toggles wiki-edit-active
    assert "wiki-edit-active" in content, "index.js must reference and toggle wiki-edit-active"
    # Assert cancel handler is integrated
    assert "btnCancelWiki" in content, "btnCancelWiki must be handled in index.js"
    assert "wikiOriginalContent" in content, "original wiki content buffer must be maintained"
    # A failed save must not be reported as success
    assert "res.ok" in content, "wiki save must check the HTTP status"


def test_edit_mode_state_declared_before_router():
    """resetEditModes() is called from switchView(); its consts must be declared first (no TDZ)."""
    content = _read("index.js")
    assert content.index("const wikiPanel") < content.index("function switchView(")
    assert content.index("let wikiOriginalContent") < content.index("function switchView(")


def test_wiki_edit_html():
    content = _read("index.html")

    assert "btn-cancel-wiki" in content, "Cancel button must exist in index.html"
    assert "wiki-edit-badge" in content, "Wiki edit badge element must exist in index.html"
