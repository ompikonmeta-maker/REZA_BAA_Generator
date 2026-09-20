# Design system: Material Design 3 · Expressive

This project uses a self-contained MD3 Expressive toolkit. **Always build UI with it** — never hand-roll components or hard-code colors.

## Files (keep at project root)
- `md3-tokens.css` — design tokens (color, type, shape, elevation, motion, spacing) + utility classes.
- `md3-dynamic-color.js` — dynamic color engine (`MD3` global).
- `md3-components.js` — Web Components (custom elements).

Include in every page:
```html
<link rel="stylesheet" href="md3-tokens.css">
<script src="md3-dynamic-color.js"></script>
<script src="md3-components.js" defer></script>
```

## Hard rules for any UI in this project
1. **Never write raw hex/rgb colors.** Use color tokens: `var(--md-sys-color-primary)`, `--md-sys-color-surface-container`, `--md-sys-color-on-surface`, etc. This keeps light/dark + dynamic color working.
2. **Use the Web Components** instead of raw `<button>`/`<input>`: `<md-button>`, `<md-icon-button>`, `<md-fab>`, `<md-chip>`, `<md-switch>`, `<md-checkbox>`, `<md-radio>`, `<md-slider>`, `<md-text-field>`, `<md-card>`, `<md-menu>`+`<md-menu-item>`, `<md-tabs>`+`<md-tab>`, `<md-list>`+`<md-list-item>`, `<md-divider>`, `<md-progress>`, `<md-dialog>`, `<md-segmented-button>`.
3. **Type** via utility classes (`.md-headline-small`, `.md-title-medium`, `.md-body-large`, `.md-label-large`, …) or `font: var(--md-sys-typescale-*)`.
4. **Spacing** via `var(--md-sys-spacing-N)` (4px scale); **radius** via `var(--md-sys-shape-corner-*)`; **shadow** via `var(--md-sys-elevation-levelN)`.
5. **Motion** via `var(--md-sys-motion-easing-*)` + `var(--md-sys-motion-duration-*)`, or the Expressive springs `var(--md-sys-motion-spring-*-spatial|effects)`. Never re-render a component's DOM to animate — toggle attributes/classes so CSS transitions the same element.
6. **Icons**: Material Symbols ligatures, e.g. `<md-button icon="add">`, `leading-icon="person"`.

## Theme & brand color (JS)
```js
MD3.applySeed('#6750A4', { style: 'expressive' }); // brand seed; style: expressive|vibrant|tonalSpot|content|neutral
MD3.setTheme('dark');   // 'light' | 'dark' | 'system'
MD3.getTheme();         // resolved 'light'|'dark'
MD3.reset();            // back to baseline tokens
```
Theme is also settable via `data-theme="light|dark"` on `<html>` (no attribute = follow OS).

## Token reference
```
--md-sys-color-{role}            primary, on-primary, primary-container, secondary*, tertiary*, error*,
                                 surface, on-surface, surface-container[-low|-high|-highest|-lowest],
                                 outline, outline-variant, inverse-surface, ...
--md-sys-typescale-{role}        display|headline|title|body|label -large|-medium|-small (+ -tracking)
--md-sys-shape-corner-{size}     none, extra-small, small, medium, large, large-increased,
                                 extra-large, extra-large-increased, extra-extra-large, full
--md-sys-elevation-level{0..5}
--md-sys-motion-easing-*         standard, standard-decelerate, standard-accelerate,
                                 emphasized, emphasized-decelerate, emphasized-accelerate, linear
--md-sys-motion-duration-*       short1..4 (50-200), medium1..4 (250-400), long1..4 (450-600), extra-long1..4 (700-1000)
--md-sys-motion-spring-*         {fast|default|slow}-{spatial|effects}
--md-sys-spacing-{0,1,2,3,4,5,6,7,8,9,10,12,14,16}   (×4px)
--md-sys-state-*-opacity         hover .08, focus/pressed .10, ...
```

## Templates
- **`claude/sidebar-template.html`** — floating MD3 sidebar layout: floating left nav panel that collapses to an icon rail (Expressive spatial-spring motion, staggered label fade), a work canvas on the right, and a built-in **Tuner** panel (width, rail width, card radius 16px / control radius 11px, spatial-spring duration & overshoot, panel elevation). Toolkit is inlined, so the file is in *Artifact-content* format (no `<!doctype>/<html>/<head>/<body>` — the Artifact tool wraps it at publish). **To reuse:** start from this file, swap the nav items / canvas content, and republish as an Artifact. For a standalone `.html` page instead, wrap it and `<link>`/`<script>` the toolkit files like `starter.html`.

- **`claude/theme-transition-template.html`** — animated **light ↔ dark theme transition** on the floating-sidebar layout. Uses the **View Transitions API** (`document.startViewTransition`) driving the whole page via MD3 color tokens. Three styles, switchable via `data-anim` on `<html>`:
  - `circular` — new theme grows as a circle from the toggle button's center.
  - `crossfade` — themes cross-dissolve (CSS keyframes on `::view-transition-old/new(root)`).
  - `wipe` — new theme sweeps in diagonally (clip-path polygon).
  For `circular` & `wipe` the reveal is driven by the **Web Animations API** on `document.documentElement.animate(kf, { pseudoElement: '::view-transition-new(root)' })` inside `transition.ready`, which enables a **two-stage pause**: reveal to a pause point (`cfg.half`) → hold (`cfg.pause`) → finish fast (`cfg.d2`), timed with keyframe `offset`s (segment easing `linear` during the hold). Config object `cfg = { dur, ease, twoStage, half, d1, pause, d2 }`; the canvas exposes all of these as live controls (style picker, duration, easing segmented buttons, initial theme, and the two-stage panel with a timeline preview). `circular`/`wipe` origin = the trigger element's bounding-box center; radius = farthest viewport corner. Fallback: browsers without View Transitions, or `prefers-reduced-motion`, swap the theme instantly (no animation). Toolkit inlined → *Artifact-content* format. **To reuse:** copy the `<style>` view-transition block + the `animateThemeSwitch`/`clipFor`/`wipeAt` JS into any MD3 page, keep `MD3.setTheme` as the swap inside `startViewTransition`.

- **`claude/card-reveal-template.html`** — per-card **"ease reveal"** entrance on the floating-sidebar layout. Cards animate via the **Web Animations API**; `framesFor(style, el)` returns `{ kf, dur }` per style and `revealEl` runs `el.animate(spec.kf, { duration: spec.dur, delay, fill:'both' })`. **Four reveal styles** (live picker in the canvas *and* the tuner, kept in sync):
  - `circular` — clip-path circle grows from card center (radius = card half-diagonal × 1.05).
  - `rise` — translateY(22→0) + scale(0.965→1) + fade.
  - `curtain` — clip-path `inset` uncovering top→bottom (rounded to `--card-r`).
  - `pop` = **"Fade + spring"** — opacity 0→1 + scale 0.88→1 **only**; no ease stage, no two-stage pause; runs on its **own duration** `cfg.springDur`.
  The first three use the **two-stage** motion shared with the theme transition: keyframes at offsets `o1=d1/total`, `o2=(d1+pause)/total`, progress `[0, half, half, 1]`, `linear` easing across the hold (reveal to `cfg.half` → hold `cfg.pause` → finish `cfg.d2`; defaults `half 50% · d1 600 · pause 250 · d2 430ms`, total 1280ms). **Spring finish**: stage 2 (and stage 1 when `springScope==='both'`) uses a spring easing `cubic-bezier(0.38, bounce, 0.22, 1)` — p1y = `cfg.bounce` > 1 overshoots past the target then settles; `pop` applies the same spring to its single segment. An **IntersectionObserver** (root = the scrolling canvas body, `threshold 0.15`, `rootMargin '0 0 -8% 0'`) reveals cards **as they become visible**: visible-on-load cards fire together (batch sorted top→bottom, offset by `stagger`), off-screen cards reveal on scroll; each card is `unobserve`d after it fires. On finish the inline `clipPath/transform/opacity` are cleared so shadows aren't clipped. `armReveals()` re-adds `.pending` + re-observes → runs on **page load, menu click, style change, and the tuner's replay**, so the reveal re-runs on every navigation. Live **Tuner** (FAB, bottom-right): style, half, d1/pause/d2 (timeline preview), stagger (0 = fully simultaneous), and a **Pegas (spring)** group — overshoot/bounce slider **1.00–2.60** with an **auto-scaling** curve preview (vertical scale grows with the peak so big overshoots aren't clipped), scope segmented (`Tahap 2` finish-only vs `Kedua tahap`), and `springDur` (duration slider that drives the `pop` style). Config `cfg = { style, half, d1, pause, d2, stagger, bounce, springScope, springDur }`. `prefers-reduced-motion` → cards shown instantly. Toolkit inlined → *Artifact-content* format. **To reuse:** swap the `STAT`/`PROJ`/`NOTES` data arrays + nav items, keep the `framesFor`/`revealEl`/`armReveals` + IntersectionObserver block, and republish as an Artifact.

- **`claude/dropdown-menu-template.html`** — full **MD3 Expressive menu** system (built from the official m3.material.io menu guidelines + specs), covering four patterns in one page: **(1) dropdown** from a button / icon-button / split-button, **(2) cascading submenus** up to 3 levels deep, **(3) context menu** on right-click, **(4) single- & multi-select** with a long scrolling menu. The toolkit's baseline `<md-menu>` is square-cornered and flat; this template ships a purpose-built engine (`window.MDMenu`) instead — the `<md-menu>` component is left untouched. **Engine API:** `MDMenu.open(openerEl, items, {viaKeyboard, onSelect})` (anchored), `MDMenu.openAt({x,y}, items, opts)` (context), `MDMenu.close()`, `MDMenu.config({style,group,radius,density,motion,instant})`, `MDMenu.getConfig()`. **Item model** (array): `{label, icon, trailingIcon, trailingText, badge, support, swatch, disabled, submenu:[…], select:'single'|'multi', group, selected, onSelect}`, plus `{divider:true}` and `{header:'…'}`. **Behavior faithful to spec:** two switchable **enter animations** — `expressive` (default; the surface + its content `scaleY` from the TOP edge — `transform-origin:top`, `scaleY(.40)→1` on a spatial spring `cubic-bezier(0.42,1.67,0.21,0.90)` (duration `--m-dur`) + fade — so the text visibly expands downward as the menu grows, matching the M3 guidelines video; a transform is used, not `clip-path` or a height animation, so the drop shadow scales WITH the box and is present the whole time instead of appearing late) and `pop` (the original single uniform scale+fade). The **exit mirrors the enter**: expressive → `mdm-close-exp` collapses `scaleY(1)→.40` toward the top edge + fade (reverse of the grow-down, `emphasized-accelerate`, duration `--m-dur`), pop → the quick `mdm-close` scale-down; instant/reduced-motion close immediately. Instant option for dense desktop — plus **edge auto-reposition** — dropdown flips above when it would clip the bottom, submenu flips to the left when it would clip the right; **scroll** with a persistent scrollbar when taller than the viewport; **shape-morph focus** — the focused (deepest) submenu gets more-rounded corners while ancestors flatten (`applyRadii`); disabled items shown, not removed. **Keyboard:** ↑/↓ move, Home/End, →/← open/close submenu, Enter/Space activate, Esc closes the current level, typeahead, Tab dismisses; roles `menu`/`menuitem`/`menuitemradio`/`menuitemcheckbox` + `aria-haspopup`/`aria-expanded`/`aria-checked`. **Color styles:** Standard (surface-container-low / on-surface, tertiary-container selected) and Vibrant (tertiary-container / on-tertiary-container, tertiary selected) — spec's two mappings. **Measurements** honor the baseline spec (item height 48dp, 12dp side padding, 24dp icons, 8dp divider padding, 112–320dp width). Live **Tuner** (FAB): color style, group treatment (divider vs gap), corner radius, density (0…−3), spring vs instant motion, and brand seed swatches. Toolkit inlined → *Artifact-content* format. **To reuse:** copy the `<style>` `.mdm-*` block + the engine `<script>` (`window.MDMenu`) into any MD3 page, then call `MDMenu.open(...)` from your triggers with your own item arrays; swap the demo item arrays in the last `<script>`.

See `index.html` (showcase) for a live example of every token and component, and `README.md` for full component attributes.
