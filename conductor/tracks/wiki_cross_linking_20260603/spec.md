# Specification: Wiki Project Cross-Linking (Track: wiki_cross_linking_20260603)

## 1. Overview
Supports cross-linking project wiki pages together using `[[/projects/project-id]]` notation. The compiler maps it to an anchor tag that triggers smooth SPA router transitions rather than full page reloads.

---

## 2. Functional Requirements
* **Regex Expansion**: Update `renderMarkdown` to replace `[[/projects/id]]` with dynamic router links.
* **Router Transitions**: Catch link click events to transition SPA state via `history.pushState` or `switchView`.

---

## 3. Acceptance Criteria
* Inputting `[[/projects/sre-next]]` compiles to a clickable link.
* Clicking does not trigger full browser page reload; it shifts Explorer view to `sre-next` assets smoothly.
