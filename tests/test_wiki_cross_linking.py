import os
import re
import urllib.parse
import html

def replace_double_brackets_py(text):
    # This emulates the JavaScript replaceDoubleBrackets(str) function
    def replacer(match):
        target = match.group(1).strip()
        prefix = ""
        id_val = target
        if target.startswith("/projects/"):
            id_val = target[len("/projects/") :].strip()
        elif target.startswith("p:"):
            prefix = "p:"
            id_val = target[2:].strip()
        elif target.startswith("d:"):
            prefix = "d:"
            id_val = target[2:].strip()
            
        display = id_val
        if prefix == "p:":
            display = f"☁️ GCP Project: {id_val}"
        elif prefix == "d:":
            display = f"🛡️ Domain: {id_val}"
        else:
            if id_val in ("sre-demo", "sre-demo-prod"):
                display = f"🛡️ Domain: {id_val}"
            else:
                display = f"☁️ GCP Project: {id_val}"
                
        encoded_id = urllib.parse.quote(id_val)
        escaped_id = html.escape(id_val)
        escaped_display = html.escape(display)
        return f'<a href="/projects/{encoded_id}" class="wiki-link" data-id="{escaped_id}">{escaped_display}</a>'

    return re.sub(r'\[\[(.*?)\]\]', replacer, text)

def test_wiki_cross_linking_logic():
    # Verify the emulated python logic on the specs inputs
    assert replace_double_brackets_py("[[/projects/sre-next]]") == '<a href="/projects/sre-next" class="wiki-link" data-id="sre-next">☁️ GCP Project: sre-next</a>'
    assert replace_double_brackets_py("[[/projects/sre-demo]]") == '<a href="/projects/sre-demo" class="wiki-link" data-id="sre-demo">🛡️ Domain: sre-demo</a>'
    assert replace_double_brackets_py("[[sre-demo-prod]]") == '<a href="/projects/sre-demo-prod" class="wiki-link" data-id="sre-demo-prod">🛡️ Domain: sre-demo-prod</a>'

def test_wiki_cross_linking_js_source():
    js_path = "src/static/index.js"
    assert os.path.exists(js_path), "index.js must exist"
    with open(js_path, "r") as f:
        content = f.read()

    # Assert that replaceDoubleBrackets exists
    assert "replaceDoubleBrackets" in content, "replaceDoubleBrackets function should be defined in index.js"
    
    # Assert regex pattern [[...]] replacement
    assert "[[(.*?" in content or "/\\[\\[(.*?)\\]\\]/g" in content, "index.js must replace double brackets using regex"
    
    # Assert prefix parsing logic
    assert "startsWith" in content, "index.js must handle prefixes with startsWith"
    assert "/projects/" in content, "index.js must match /projects/ link paths"
    
    # Assert that it produces links with class="wiki-link"
    assert "wiki-link" in content, "index.js must attach wiki-link class to the compiled anchors"
    
    # Assert click delegation for SPA routing matches the wiki link click interception
    assert "document.addEventListener(\"click\"" in content or 'document.addEventListener("click"' in content, "index.js must bind to document clicks"
    assert 'closest(".wiki-link")' in content or "closest('.wiki-link')" in content, "index.js click handler must delegate to .wiki-link"
