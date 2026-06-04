# Specification: UI Navigation Deep Reload Bug (Track: ui_navigation_deep_reload_20260604)

## 1. Overview
This specification documents the resolution of the deep reload navigation bug (Issue #4). When reloading deep project URLs (such as `/projects/sre-next`), relative stylesheet and script paths caused assets to fail to load, resulting in unstyled pages.

---

## 2. Functional Requirements
* **Absolute Asset Resolution**: Ensure all global assets (`index.css`, `index.js`) are referenced with root-relative paths (`/index.css` and `/index.js`) inside `index.html`.
* **SPA Routing Fallback**: The HTTP server must fall back to serving `index.html` for deep routes while correctly serving absolute static asset paths directly from the static directory.

---

## 3. Acceptance Criteria
* Reloading the browser at `/projects/<id>` retrieves and renders all styles and interactive JS logic correctly.
* In-browser console does not report MIME-type or path resolution errors for assets during route transitions or reloads.
