# Material Design 3 · Expressive — Toolkit

Fondasi MD3 Expressive tanpa framework: **CSS custom properties** untuk design token + **Web Components** untuk komponen, dengan dukungan **Light / Dark / Dynamic color**. Dibuat berdasarkan spesifikasi m3.material.io (styles + components) dan pembaruan Expressive 2025.

## Isi

| File | Fungsi |
|---|---|
| `md3-tokens.css` | Semua design token: color roles (light+dark), type scale, shape, elevation, motion (easing/duration + spring), spacing, state layers. Termasuk utility class typografi & elevasi. |
| `md3-dynamic-color.js` | Engine warna dinamis: generate skema penuh dari satu warna seed (tonal palette, tone = CIELAB L*), plus pengaturan tema. Tanpa dependensi. |
| `md3-components.js` | Library Web Components (custom elements). |
| `index.html` | Halaman showcase interaktif (seed picker, style, toggle tema, demo semua token & komponen). |
| `artifact.html` | Versi showcase yang self-contained (semua di-inline) — untuk dibuka langsung / dipublikasikan. |

## Cara pakai di tool kamu

```html
<link rel="stylesheet" href="md3-tokens.css">
<script src="md3-dynamic-color.js"></script>
<script src="md3-components.js" defer></script>
```

Lalu pakai komponen sebagai tag HTML biasa:

```html
<md-button variant="filled" icon="add">Simpan</md-button>
<md-text-field variant="outlined" label="Email" trailing-icon="mail"></md-text-field>
<md-switch selected></md-switch>
<md-slider min="0" max="100" value="40" labeled></md-slider>
```

## Dynamic color (Material You)

```js
// Generate seluruh skema (light & dark) dari satu seed:
MD3.applySeed('#006A6A', { style: 'expressive' });

// style: 'expressive' | 'vibrant' | 'tonalSpot' | 'content' | 'neutral'
MD3.setTheme('dark');     // 'light' | 'dark' | 'system'
MD3.getTheme();           // -> 'light' | 'dark' (resolved)
MD3.reset();              // kembali ke token baseline

// Butuh skema tanpa menerapkan ke DOM (mis. simpan preferensi):
const scheme = MD3.schemeFromSeed('#6750A4', 'expressive'); // { light:{...}, dark:{...} }
```

Tone diturunkan sebagai nilai **CIELAB L\*** (persis definisi "tone" pada HCT), dengan clamping gamut sRGB otomatis — hasilnya setia pada Material You tanpa perlu memuat model CAM16 penuh.

## Tema

Tema dikontrol lewat atribut pada `<html>`:

- `data-theme="light"` — paksa terang
- `data-theme="dark"` — paksa gelap
- tanpa atribut — ikuti `prefers-color-scheme` OS

`MD3.setTheme()` mengatur ini untukmu dan mengecat ulang skema dinamis yang aktif.

## Token — konvensi penamaan

```
--md-sys-color-{role}          --md-sys-color-primary, --md-sys-color-surface-container-high, ...
--md-sys-typescale-{role}      --md-sys-typescale-headline-large (font shorthand) + -tracking
--md-sys-shape-corner-{size}   none, extra-small, small, medium, large, large-increased,
                               extra-large, extra-large-increased, extra-extra-large, full
--md-sys-elevation-level{0-5}
--md-sys-motion-easing-*       standard, emphasized, emphasized-decelerate, ...
--md-sys-motion-duration-*     short1..4, medium1..4, long1..4, extra-long1..4
--md-sys-motion-spring-*       {fast|default|slow}-{spatial|effects}
--md-sys-spacing-{n}           0,1,2,3,4,5,6,7,8,9,10,12,14,16 (kelipatan 4px)
--md-sys-state-*-opacity
```

## Komponen & atribut utama

| Elemen | Atribut penting |
|---|---|
| `<md-button>` | `variant` filled\|tonal\|elevated\|outlined\|text · `size` xs\|s\|m\|l\|xl · `icon` · `trailing-icon` · `href` · `disabled` |
| `<md-icon-button>` | `variant` standard\|filled\|tonal\|outlined · `toggle` · `selected` |
| `<md-fab>` | `size` small\|medium\|large · `variant` surface\|primary\|secondary\|tertiary · `extended` · `icon` · `label` |
| `<md-chip>` | `variant` assist\|filter\|input\|suggestion · `selected` · `removable` · `icon` |
| `<md-switch>` | `selected` · `icons` · `disabled` |
| `<md-checkbox>` | `checked` · `indeterminate` · `disabled` |
| `<md-radio>` | `name` · `value` · `checked` |
| `<md-slider>` | `min` · `max` · `value` · `step` · `labeled` |
| `<md-text-field>` | `variant` filled\|outlined · `label` · `type` · `leading-icon` · `trailing-icon` · `supporting-text` · `error` · `error-text` |
| `<md-card>` | `variant` elevated\|filled\|outlined |
| `<md-menu>` + `<md-menu-item icon>` | `MD3Menu.attach(anchorEl, menuEl)` untuk membuka |
| `<md-tabs>` + `<md-tab value icon active>` | event `change` `{detail.value}` |
| `<md-list>` + `<md-list-item icon supporting-text trailing interactive>` | — |
| `<md-divider inset>` | — |
| `<md-progress>` | `variant` linear\|circular · `value` (0–100) · `indeterminate` |
| `<md-dialog>` | `.show()` / `.close()` · slot `headline`, default, `actions` |
| `<md-segmented-button>` | anak `<button data-value selected>` · atribut `multi` |

Event umum: komponen selection memancarkan `change`; chip removable memancarkan `remove`; menu-item memancarkan `select`; slider/text-field memancarkan `input`.

## Ikon

Menggunakan **Material Symbols Outlined** (dimuat via Google Fonts di `md3-tokens.css`). Nama ikon = ligatur, mis. `icon="add"`, `leading-icon="person"`. Butuh koneksi internet untuk memuat font; jika offline, tambahkan file font lokal.

## Aksesibilitas & motion

- Peran ARIA & `aria-label`/`aria-checked`/`aria-pressed` sudah ditanam pada komponen interaktif.
- Pasangan warna `on-*` diuji kontras (≥ 4.5:1 untuk teks pada baseline).
- Menghormati `prefers-reduced-motion` (animasi dinonaktifkan).
- Target sentuh mengikuti panduan (tinggi ≥ 40–48px).

## Catatan spesifikasi

- Type scale, shape scale, elevation, easing/duration mengikuti nilai token resmi MD3.
- Motion physics (spring) Expressive diaproksimasi ke CSS `cubic-bezier` (web tidak punya spring native); spatial spring memiliki overshoot, effect spring tidak.
- Shape morph saat ditekan diaproksimasi via transisi `border-radius`.
