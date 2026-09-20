/* =====================================================================
   Material Design 3 · Expressive — Dynamic Color Engine
   ---------------------------------------------------------------------
   Self-contained (no dependencies). Generates a full Material color
   scheme from a single seed color, in the spirit of Material You.

   Tones are the CIELAB L* value (0–100) — this is exactly how HCT
   defines "tone", so tonal mapping is faithful. Hue/chroma use CIE LCh,
   with automatic sRGB gamut clamping (chroma is reduced until the tone
   is reproducible), matching the perceptual intent of HCT closely
   without shipping the full CAM16 model.

   Public API (global `MD3`):
     MD3.applySeed('#6750A4', { style: 'expressive' })
     MD3.setTheme('light' | 'dark' | 'system')
     MD3.getTheme()            -> resolved 'light' | 'dark'
     MD3.reset()               -> back to baseline tokens
     MD3.schemeFromSeed(hex, style) -> { light, dark } role maps
   ===================================================================== */
(function (global) {
  'use strict';

  /* ---------- sRGB <-> CIE Lab/LCh ---------- */
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

  function hexToRgb(hex) {
    hex = hex.replace('#', '').trim();
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    const n = parseInt(hex, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function rgbToHex(r, g, b) {
    const h = v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0');
    return '#' + h(r) + h(g) + h(b);
  }
  const lin = c => { c /= 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
  const gam = c => { const v = c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; return v * 255; };

  // D65 reference white
  const Xn = 95.047, Yn = 100.0, Zn = 108.883;

  function rgbToXyz(r, g, b) {
    r = lin(r); g = lin(g); b = lin(b);
    return [
      (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) * 100,
      (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) * 100,
      (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) * 100,
    ];
  }
  function xyzToRgb(x, y, z) {
    x /= 100; y /= 100; z /= 100;
    return [
      gam(x * 3.2404542 + y * -1.5371385 + z * -0.4985314),
      gam(x * -0.9692660 + y * 1.8760108 + z * 0.0415560),
      gam(x * 0.0556434 + y * -0.2040259 + z * 1.0572252),
    ];
  }
  const f = t => t > 0.008856 ? Math.cbrt(t) : (7.787 * t + 16 / 116);
  const fInv = t => { const t3 = t * t * t; return t3 > 0.008856 ? t3 : (t - 16 / 116) / 7.787; };

  function xyzToLab(x, y, z) {
    const fx = f(x / Xn), fy = f(y / Yn), fz = f(z / Zn);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }
  function labToXyz(L, a, b) {
    const fy = (L + 16) / 116, fx = fy + a / 500, fz = fy - b / 200;
    return [fInv(fx) * Xn, fInv(fy) * Yn, fInv(fz) * Zn];
  }
  function rgbToLch(r, g, b) {
    const [x, y, z] = rgbToXyz(r, g, b);
    const [L, A, B] = xyzToLab(x, y, z);
    const C = Math.sqrt(A * A + B * B);
    let H = Math.atan2(B, A) * 180 / Math.PI;
    if (H < 0) H += 360;
    return [L, C, H];
  }
  function lchToRgb(L, C, H) {
    const hr = H * Math.PI / 180;
    const a = Math.cos(hr) * C, b = Math.sin(hr) * C;
    const [x, y, z] = labToXyz(L, a, b);
    return xyzToRgb(x, y, z);
  }
  const inGamut = ([r, g, b]) => r >= -0.5 && r <= 255.5 && g >= -0.5 && g <= 255.5 && b >= -0.5 && b <= 255.5;

  /* ---------- Tonal color: color at a given tone (L*), hue, chroma ----------
     Reduces chroma until the requested tone is reproducible in sRGB.     */
  function toneColor(hue, chroma, tone) {
    let lo = 0, hi = chroma, best = lchToRgb(tone, 0, hue);
    // Binary search for the maximum in-gamut chroma at this tone.
    for (let i = 0; i < 24; i++) {
      const mid = (lo + hi) / 2;
      const rgb = lchToRgb(tone, mid, hue);
      if (inGamut(rgb)) { best = rgb; lo = mid; } else { hi = mid; }
    }
    return rgbToHex(best[0], best[1], best[2]);
  }

  /* ---------- Scheme styles: chroma per tonal palette (LCh units) ---------- */
  const STYLES = {
    // name: [primaryC, secondaryC, tertiaryC, tertiaryHueRotate, neutralC, neutralVariantC]
    tonalSpot:  [48, 18, 42, 60, 5, 12],
    vibrant:    [80, 32, 56, 48, 8, 16],
    expressive: [70, 34, 64, 90, 8, 18], // richer, playful — the Expressive default
    neutral:    [12, 8, 14, 60, 3, 6],
    content:    [60, 26, 48, 40, 6, 12],
  };
  const ERROR_HUE = 25, ERROR_CHROMA = 78;

  // Role -> [palette, tone] for light & dark. palette: p,s,t,e,n,nv
  const MAP = {
    light: {
      primary: ['p', 40], 'on-primary': ['p', 100], 'primary-container': ['p', 90], 'on-primary-container': ['p', 30],
      secondary: ['s', 40], 'on-secondary': ['s', 100], 'secondary-container': ['s', 90], 'on-secondary-container': ['s', 30],
      tertiary: ['t', 40], 'on-tertiary': ['t', 100], 'tertiary-container': ['t', 90], 'on-tertiary-container': ['t', 30],
      error: ['e', 40], 'on-error': ['e', 100], 'error-container': ['e', 90], 'on-error-container': ['e', 30],
      background: ['n', 98], 'on-background': ['n', 10],
      surface: ['n', 98], 'on-surface': ['n', 10],
      'surface-variant': ['nv', 90], 'on-surface-variant': ['nv', 30],
      'surface-dim': ['n', 87], 'surface-bright': ['n', 98],
      'surface-container-lowest': ['n', 100], 'surface-container-low': ['n', 96],
      'surface-container': ['n', 94], 'surface-container-high': ['n', 92], 'surface-container-highest': ['n', 90],
      outline: ['nv', 50], 'outline-variant': ['nv', 80],
      'inverse-surface': ['n', 20], 'inverse-on-surface': ['n', 95], 'inverse-primary': ['p', 80],
    },
    dark: {
      primary: ['p', 80], 'on-primary': ['p', 20], 'primary-container': ['p', 30], 'on-primary-container': ['p', 90],
      secondary: ['s', 80], 'on-secondary': ['s', 20], 'secondary-container': ['s', 30], 'on-secondary-container': ['s', 90],
      tertiary: ['t', 80], 'on-tertiary': ['t', 20], 'tertiary-container': ['t', 30], 'on-tertiary-container': ['t', 90],
      error: ['e', 80], 'on-error': ['e', 20], 'error-container': ['e', 30], 'on-error-container': ['e', 90],
      background: ['n', 6], 'on-background': ['n', 90],
      surface: ['n', 6], 'on-surface': ['n', 90],
      'surface-variant': ['nv', 30], 'on-surface-variant': ['nv', 80],
      'surface-dim': ['n', 6], 'surface-bright': ['n', 24],
      'surface-container-lowest': ['n', 4], 'surface-container-low': ['n', 10],
      'surface-container': ['n', 12], 'surface-container-high': ['n', 17], 'surface-container-highest': ['n', 22],
      outline: ['nv', 60], 'outline-variant': ['nv', 30],
      'inverse-surface': ['n', 90], 'inverse-on-surface': ['n', 20], 'inverse-primary': ['p', 40],
    },
  };
  // Fixed roles (identical in light & dark)
  const FIXED = {
    'primary-fixed': ['p', 90], 'primary-fixed-dim': ['p', 80], 'on-primary-fixed': ['p', 10], 'on-primary-fixed-variant': ['p', 30],
    'secondary-fixed': ['s', 90], 'secondary-fixed-dim': ['s', 80], 'on-secondary-fixed': ['s', 10], 'on-secondary-fixed-variant': ['s', 30],
    'tertiary-fixed': ['t', 90], 'tertiary-fixed-dim': ['t', 80], 'on-tertiary-fixed': ['t', 10], 'on-tertiary-fixed-variant': ['t', 30],
  };

  function palettesFromSeed(hex, style) {
    const [, seedC, seedH] = rgbToLch(...hexToRgb(hex));
    const s = STYLES[style] || STYLES.expressive;
    const pC = Math.max(seedC, s[0]);
    return {
      p:  { h: seedH, c: pC },
      s:  { h: seedH, c: s[1] },
      t:  { h: (seedH + s[3]) % 360, c: s[2] },
      e:  { h: ERROR_HUE, c: ERROR_CHROMA },
      n:  { h: seedH, c: s[4] },
      nv: { h: seedH, c: s[5] },
    };
  }

  function buildScheme(pal, roleMap) {
    const out = {};
    for (const role in roleMap) {
      const [pk, tone] = roleMap[role];
      out[role] = toneColor(pal[pk].h, pal[pk].c, tone);
    }
    return out;
  }

  function schemeFromSeed(hex, style) {
    const pal = palettesFromSeed(hex, style || 'expressive');
    const fixed = buildScheme(pal, FIXED);
    return {
      light: Object.assign(buildScheme(pal, MAP.light), fixed),
      dark: Object.assign(buildScheme(pal, MAP.dark), fixed),
    };
  }

  /* ---------- Applying to the document ---------- */
  let _scheme = null; // { light, dark } currently applied from a seed

  function resolveTheme() {
    const t = document.documentElement.getAttribute('data-theme');
    if (t === 'dark') return 'dark';
    if (t === 'light') return 'light';
    return global.matchMedia && global.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function paint() {
    if (!_scheme) return;
    const roles = _scheme[resolveTheme()];
    const root = document.documentElement;
    for (const role in roles) root.style.setProperty('--md-sys-color-' + role, roles[role]);
  }

  const MD3 = {
    schemeFromSeed,
    applySeed(hex, opts) {
      _scheme = schemeFromSeed(hex, (opts && opts.style) || 'expressive');
      paint();
      return _scheme;
    },
    setTheme(mode) {
      const root = document.documentElement;
      if (mode === 'system') root.removeAttribute('data-theme');
      else root.setAttribute('data-theme', mode);
      paint();
      return this.getTheme();
    },
    getTheme: resolveTheme,
    reset() {
      _scheme = null;
      const root = document.documentElement;
      // Remove any inline overrides so the stylesheet baseline returns.
      [...root.style].filter(p => p.startsWith('--md-sys-color-')).forEach(p => root.style.removeProperty(p));
    },
  };

  // Keep dynamic scheme correct when the OS theme flips under "system".
  if (global.matchMedia) {
    global.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);
  }

  global.MD3 = MD3;
})(window);
