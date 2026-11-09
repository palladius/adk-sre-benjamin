import os

def test_wiki_edit_active_css():
    css_path = "src/static/index.css"
    assert os.path.exists(css_path), "index.css must exist"
    with open(css_path, "r") as f:
        content = f.read()
    
    # Assert that .wiki-edit-active rules are implemented
    assert "wiki-edit-active" in content, "wiki-edit-active class should be defined in index.css"
    
    # Assert that it targets sidebar to hide it
    assert "sidebar" in content, "sidebar styling should be present"
    # Assert that it targets chat column to hide it
    assert "chat-column" in content, "chat-column styling should be present"

    # Assert wiki focus badge and responsive height rules
    assert "wiki-edit-badge" in content, "wiki-edit-badge should be defined in index.css"
    assert "calc(100vh - 280px)" in content, "expanded responsive editor height should be present"

def test_wiki_edit_active_js():
    js_path = "src/static/index.js"
    assert os.path.exists(js_path), "index.js must exist"
    with open(js_path, "r") as f:
        content = f.read()
    
    # Assert that index.js toggles wiki-edit-active
    assert "wiki-edit-active" in content, "index.js must reference and toggle wiki-edit-active"
    # Assert cancel handler is integrated
    assert "btnCancelWiki" in content, "btnCancelWiki must be handled in index.js"
    assert "wikiOriginalContent" in content, "original wiki content buffer must be maintained"

def test_wiki_edit_html():
    html_path = "src/static/index.html"
    assert os.path.exists(html_path), "index.html must exist"
    with open(html_path, "r") as f:
        content = f.read()
    
    assert "btn-cancel-wiki" in content, "Cancel button must exist in index.html"
    assert "wiki-edit-badge" in content, "Wiki edit badge element must exist in index.html"
