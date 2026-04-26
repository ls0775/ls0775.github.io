# Copilot instructions for `ls0775.github.io`

## Build, test, and lint commands

This repository is a static site with no configured build, test, or lint toolchain in-repo (no package manager files, no test files, no CI workflows).

- **Run locally:** `python3 -m http.server 8000` then open `http://localhost:8000`
- **Automated tests/lint:** not configured
- **Single-test command:** not applicable (no test framework configured)

## High-level architecture

- The site is a single static page in `index.html`, styled by `style.css`, with background animation logic in `script.js`.
- `index.html` provides the core content and metadata, plus a full-screen `<canvas id="bg-canvas">` behind the centered glassmorphism content card.
- `script.js` renders and animates a particle field on that canvas:
  - particle positions and velocity updates
  - edge bouncing
  - mouse-proximity particle growth
  - particle-to-particle connecting lines based on distance
  - resize re-initialization (debounced)
- `style.css` defines the visual system:
  - `@font-face` loading from `fonts/`
  - color/theme tokens in `:root`
  - content card, responsive link layout, animation, and viewport/safe-area behavior

## Key conventions in this codebase

- Keep the architecture dependency simple: semantic HTML in `index.html`, all styling in `style.css`, all dynamic behavior in `script.js`.
- Preserve the canvas/content contract: `#bg-canvas` is fixed, full-viewport, and layered behind `main.content`; changes to one must keep z-index and sizing aligned with the other.
- Mobile behavior is intentionally tuned in both CSS and JS:
  - CSS switches link layout at `max-width: 600px`
  - JS reduces particle density/speed and line distance under `768px`
  Keep both layers in sync when adjusting responsive behavior.
- Visual theme is centralized via CSS custom properties in `:root`; extend these variables instead of hardcoding new palette values in component rules.
