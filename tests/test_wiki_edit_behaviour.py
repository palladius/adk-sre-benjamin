"""Behavioural tests for the wiki Focus Edit Mode (issue #10).

Loads the real src/static/index.html + index.js in headless Chromium, with every
network request intercepted (static files served from disk, /api/* mocked), and
drives Edit / Cancel / Save / navigation like a user would.

Skipped automatically when Playwright or a Chromium binary is unavailable.
Set PLAYWRIGHT_CHROMIUM_EXECUTABLE to point at a specific browser binary.
"""
import glob
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

STATIC_DIR = Path(__file__).resolve().parent.parent / "src" / "static"
BASE = "http://benji.test"
PROJECT = "demo-proj"
ORIGINAL = "# Original wiki\n\nhello"
WIKI_URL = f"/api/projects/{PROJECT}/wiki"

CONTENT_TYPES = {".js": "application/javascript", ".css": "text/css", ".html": "text/html"}


def _launch(pw):
    # Explicit override first, then Playwright's bundled browser, then any cached headless shell
    # (useful when the installed playwright package and cached browser revisions differ).
    env_exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    candidates = ([env_exe] if env_exe else []) + [None]
    candidates += sorted(glob.glob(os.path.expanduser(
        "~/.cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")), reverse=True)
    errors = []
    for exe in candidates:
        try:
            return pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
        except Exception as e:  # noqa: BLE001 - try the next candidate
            errors.append(f"{exe or 'bundled'}: {str(e).splitlines()[0]}")
    pytest.skip("No usable Chromium for Playwright: " + " | ".join(errors))


class FakeBackend:
    """Mocks the Benjamin HTTP API; tests tweak `save_status` / `save_hold`."""

    def __init__(self):
        self.wiki = ORIGINAL
        self.save_status = 200
        self.saved_bodies = []
        self.held = []  # routes held back to simulate an in-flight save
        self.save_hold = False

    def handle(self, route):
        req = route.request
        url = urlparse(req.url)
        if url.netloc != "benji.test":
            ctype = "text/css" if url.path.endswith(".css") else "application/javascript"
            return route.fulfill(status=200, body="", content_type=ctype)
        path = url.path
        if path == WIKI_URL:
            if req.method == "POST":
                if self.save_hold:
                    self.held.append(route)
                    return None
                return self._answer_save(route)
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"content": self.wiki}))
        if path == "/api/config":
            return route.fulfill(status=200, content_type="application/json",
                                 body=json.dumps({"project_id": PROJECT, "version": "test"}))
        if path.startswith("/api/"):
            return route.fulfill(status=200, content_type="application/json", body="{}")
        static = STATIC_DIR / path.lstrip("/")
        if path not in ("", "/") and static.is_file():
            return route.fulfill(status=200, body=static.read_bytes(),
                                 content_type=CONTENT_TYPES.get(static.suffix, "application/octet-stream"))
        # SPA routes (/, /projects/<id>, /clouds) all serve index.html
        return route.fulfill(status=200, body=(STATIC_DIR / "index.html").read_bytes(), content_type="text/html")

    def _answer_save(self, route):
        body = json.loads(route.request.post_data or "{}")
        self.saved_bodies.append(body.get("content"))
        if self.save_status != 200:
            return route.fulfill(status=self.save_status, content_type="application/json",
                                 body=json.dumps({"error": "disk on fire"}))
        self.wiki = body.get("content", "")
        return route.fulfill(status=200, content_type="application/json",
                             body=json.dumps({"project_id": PROJECT, "content": self.wiki}))

    def release_held(self):
        while self.held:
            self._answer_save(self.held.pop(0))


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        b = _launch(pw)
        yield b
        b.close()


@pytest.fixture
def ctx(browser):
    backend = FakeBackend()
    context = browser.new_context(viewport={"width": 1600, "height": 1000})
    context.route("**/*", backend.handle)
    page = context.new_page()
    page.goto(f"{BASE}/projects/{PROJECT}")
    page.wait_for_function(f"document.getElementById('project-id-input')?.value === '{PROJECT}'")
    page.click(".project-tab-btn[data-tab='wiki']")
    page.wait_for_function(f"document.getElementById('wiki-editor').value === {json.dumps(ORIGINAL)}")
    yield page, backend
    context.close()


def _state(page):
    return page.evaluate("""() => ({
        editing: document.querySelector('.wiki-panel').classList.contains('edit-mode'),
        focus: document.querySelector('.app-container').classList.contains('wiki-edit-active'),
        editor: document.getElementById('wiki-editor').value,
        preview: document.getElementById('wiki-preview').innerText,
        status: document.getElementById('wiki-save-status').textContent,
        badge: getComputedStyle(document.getElementById('wiki-edit-badge')).display,
    })""")


def _enter_and_type(page, text):
    page.click("#btn-edit-wiki")
    page.fill("#wiki-editor", text)


def test_edit_enters_focus_mode(ctx):
    page, _ = ctx
    assert _state(page)["badge"] == "none"
    page.click("#btn-edit-wiki")
    s = _state(page)
    assert s["editing"] and s["focus"]
    assert s["badge"] != "none"


def test_cancel_restores_original_after_confirm(ctx):
    page, _ = ctx
    _enter_and_type(page, "# scribbles")
    page.once("dialog", lambda d: d.accept())
    page.click("#btn-cancel-wiki")
    s = _state(page)
    assert not s["editing"] and not s["focus"]
    assert s["editor"] == ORIGINAL
    assert "Original wiki" in s["preview"] and "scribbles" not in s["preview"]


def test_cancel_dismissed_keeps_edits(ctx):
    page, _ = ctx
    _enter_and_type(page, "# keep me")
    page.once("dialog", lambda d: d.dismiss())
    page.click("#btn-cancel-wiki")
    s = _state(page)
    assert s["editing"] and s["editor"] == "# keep me"


def test_view_toggle_and_escape_do_not_leave_unsaved_text(ctx):
    page, _ = ctx
    _enter_and_type(page, "# unsaved")
    page.once("dialog", lambda d: d.accept())
    page.click("#btn-edit-wiki")  # now labelled "👁️ View Wiki"
    assert _state(page)["editor"] == ORIGINAL

    _enter_and_type(page, "# unsaved again")
    page.once("dialog", lambda d: d.accept())
    page.keyboard.press("Escape")
    s = _state(page)
    assert not s["editing"] and s["editor"] == ORIGINAL


def test_save_success_auto_exits(ctx):
    page, backend = ctx
    _enter_and_type(page, "# Saved v2")
    page.click("#btn-save-wiki")
    page.wait_for_function("!document.querySelector('.wiki-panel').classList.contains('edit-mode')", timeout=3000)
    s = _state(page)
    assert backend.wiki == "# Saved v2"
    assert s["editor"] == "# Saved v2" and not s["focus"]
    # Baseline moved: re-entering and cancelling with no edits must not prompt nor revert.
    page.click("#btn-edit-wiki")
    page.click("#btn-cancel-wiki")
    assert _state(page)["editor"] == "# Saved v2"


def test_save_failure_stays_in_edit_mode(ctx):
    page, backend = ctx
    backend.save_status = 500
    _enter_and_type(page, "# will fail")
    page.click("#btn-save-wiki")
    page.wait_for_function("document.getElementById('wiki-save-status').textContent.includes('failed')")
    page.wait_for_timeout(1200)  # longer than the auto-exit delay
    s = _state(page)
    assert s["editing"] and s["focus"]
    assert s["editor"] == "# will fail"
    assert "Successfully" not in s["status"]
    # Baseline untouched: Cancel still restores the server content.
    page.once("dialog", lambda d: d.accept())
    page.click("#btn-cancel-wiki")
    assert _state(page)["editor"] == ORIGINAL


def test_typing_during_inflight_save_is_not_lost(ctx):
    page, backend = ctx
    backend.save_hold = True
    _enter_and_type(page, "# sent")
    page.click("#btn-save-wiki")
    page.wait_for_function("document.getElementById('btn-cancel-wiki').disabled")
    assert page.is_disabled("#btn-edit-wiki")
    page.evaluate("""() => { const e = document.getElementById('wiki-editor');
        e.value = '# sent + more'; e.dispatchEvent(new Event('input')); }""")
    backend.release_held()
    page.wait_for_function("!document.getElementById('btn-cancel-wiki').disabled")
    page.wait_for_timeout(1200)
    s = _state(page)
    assert backend.saved_bodies == ["# sent"]
    # Still dirty -> no auto-exit, extra text preserved.
    assert s["editing"] and s["editor"] == "# sent + more"


def test_navigation_asks_and_resets(ctx):
    page, _ = ctx
    _enter_and_type(page, "# dirty")
    # Declined: tab switch is aborted, edits kept.
    page.once("dialog", lambda d: d.dismiss())
    page.click(".project-tab-btn[data-tab='audit']")
    s = _state(page)
    assert s["editing"] and s["editor"] == "# dirty"
    # Accepted: switchView resets focus mode and reverts the editor.
    page.once("dialog", lambda d: d.accept())
    page.evaluate("history.pushState(null, '', '/clouds'); history.back();")
    page.wait_for_function("!document.querySelector('.app-container').classList.contains('wiki-edit-active')")
    s = _state(page)
    assert not s["editing"] and s["editor"] == ORIGINAL
