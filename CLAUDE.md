# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A single, framework-free **Material Design 3 · Expressive** front-end toolkit, living entirely
under `docs/material-design-3-project/`. There is **no build step, no package manager, no test
suite, and no linter** — the source is plain CSS, vanilla JS (Web Components), and HTML that runs
directly in the browser. "Running" means opening a file, or serving the folder over static HTTP.

```bash
# From docs/material-design-3-project/, serve the folder so relative <link>/<script> resolve:
python3 -m http.server 8000     # then open http://localhost:8000/index.html
```

`index.html` (multi-file, links the toolkit) and `artifact.html` (everything inlined, self-contained)
are two builds of the same showcase — keep them in sync when you change tokens or components.

## Architecture

The toolkit is three layers, meant to be loaded in this order on every page:

```html
<link rel="stylesheet" href="md3-tokens.css">   <!-- 1. design tokens (CSS custom properties) -->
<script src="md3-dynamic-color.js"></script>    <!-- 2. dynamic-color engine, exposes window.MD3 -->
<script src="md3-components.js" defer></script> <!-- 3. Web Components (custom elements) -->
```

- **`md3-tokens.css`** — the source of truth for all design values as `--md-sys-*` custom properties
  (color roles for light *and* dark, type scale, shape, elevation, motion easings/durations/springs,
  spacing, state layers) plus typography/elevation utility classes. Everything downstream reads these.
- **`md3-dynamic-color.js`** — computes a full Material You scheme from one seed color (tone = CIELAB L*,
  no CAM16 dependency) and **overwrites the token custom properties at runtime**. Global API: `MD3.applySeed`,
  `MD3.setTheme` / `MD3.getTheme`, `MD3.reset`, `MD3.schemeFromSeed`.
- **`md3-components.js`** — `<md-*>` custom elements (button, fab, chip, switch, text-field, card, menu,
  tabs, list, dialog, segmented-button, …). Components style themselves purely from the CSS tokens, which
  is why theming and dynamic color propagate to them for free.

Theme is driven by `data-theme="light|dark"` on `<html>` (absent = follow OS `prefers-color-scheme`);
`MD3.setTheme()` sets that attribute and repaints any active dynamic scheme.

## Hard rules when building or editing UI (from the toolkit's own CLAUDE.md)

`docs/material-design-3-project/CLAUDE.md` is the authoritative design-system contract, and
`README.md` beside it lists every component's attributes and events. In short:

1. **Never write raw hex/rgb.** Use color tokens (`var(--md-sys-color-primary)`, `…-surface-container`,
   `…-on-surface`, …) so light/dark and dynamic color keep working.
2. **Use the `<md-*>` Web Components**, not raw `<button>`/`<input>`.
3. Type via utility classes / `font: var(--md-sys-typescale-*)`; spacing via `var(--md-sys-spacing-N)`
   (4px scale); radius via `var(--md-sys-shape-corner-*)`; shadow via `var(--md-sys-elevation-levelN)`;
   motion via the easing/duration/spring tokens.
4. **Animate by toggling attributes/classes** so CSS transitions the *same* element — never re-render a
   component's DOM to animate it.

## The `claude/` templates

`docs/material-design-3-project/claude/*.html` are reusable, self-contained layout/interaction demos
(floating sidebar, light↔dark view-transition, per-card reveal, full dropdown-menu engine). They are in
**Artifact-content format** — no `<!doctype>/<html>/<head>/<body>`, because the Artifact tool wraps them
at publish time, and the toolkit is inlined rather than linked. To reuse one as a standalone `.html` file,
wrap it and `<link>`/`<script>` the toolkit files the way `starter.html` does. The subproject CLAUDE.md
documents each template's engine API and config knobs in detail — read it before modifying one.
