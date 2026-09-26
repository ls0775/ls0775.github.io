# Copilot instructions for `ls0775.github.io`

## Build, test, and lint commands

This repository is a static site with no configured build, test, or lint toolchain in-repo (no package manager files, no test files).

- **Run locally:** `python3 -m http.server 8000` then open `http://localhost:8000`
- **Regenerate blog pages:** `python3 scripts/sync_blogs.py` (see `README.md`)
- **Automated tests/lint:** not configured
- **Single-test command:** not applicable (no test framework configured)

## Design system

**All visual decisions follow [`DESIGN.md`](../DESIGN.md).** Read it before touching any HTML or CSS. In short: calm, light, flat, one left-aligned column, plain underlined links, quiet hierarchy, no JavaScript, subtract first.

## High-level architecture

- The home page is `index.html`, styled by `style.css`. There is no JavaScript.
- The blog lives under `blog/`. Post and index pages are **generated** by `scripts/sync_blogs.py` from `ls0775/homelab` — edit the template in that script, not the generated HTML. `blog/blog.css` is a hand-maintained static stylesheet.
- Both stylesheets share the same `:root` tokens from `DESIGN.md` and self-host Outfit (weights 300 and 400 only) from `fonts/`.

## Key conventions in this codebase

- Semantic HTML in `index.html`; all styling in `style.css` / `blog/blog.css`. Do not add scripts unless the page cannot function without them.
- Colours live only in `:root`. Never hardcode a colour in a component rule; extend the tokens instead.
- No shadows, blur, gradients, glows, transforms, entrance animations or `@keyframes`. The only transition is `text-decoration-color`, disabled under `prefers-reduced-motion`.
- Links are underlined text, not buttons. Lists use `list-style: none` with hairline `var(--rule)` borders, not cards.
- Keep `overscroll-behavior: none`, `100svh`, and `max(..., env(safe-area-inset-*))` padding. The single responsive breakpoint is `600px`.
- Keep `theme-color` in `index.html` and the blog template equal to `--bg` (`#faf9f6`).
