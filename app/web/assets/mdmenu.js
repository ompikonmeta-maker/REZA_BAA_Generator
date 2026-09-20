/* =====================================================================
   MD3 Dropdown Menu — engine
   A token-driven, accessible menu system: anchored dropdowns, cascading
   submenus (with shape-morph focus), context menus, single/multi-select,
   edge auto-reposition (flip), and scroll. Keyboard + pointer.
   ===================================================================== */
(function () {
  'use strict';

  const CFG = { style: 'standard', group: 'divider', radius: 12, density: 0, motion: true, instant: false, enterStyle: 'expressive', duration: 520, closeDuration: 300, closeFade: true, closeFadeLead: 0.45, elevation: 3 };

  let layer = null, scrim = null, hoverTimer = null;
  let stack = [];            // open panels, index 0 = root
  let onSelectCb = null;     // per-open callback

  /* ---------- layer + theming ---------- */
  function ensureLayer() {
    if (layer) return;
    layer = document.createElement('div');
    layer.className = 'mdm-layer';
    document.body.appendChild(layer);
  }
  const itemHeight = () => 48 + CFG.density * 4;   // 48 / 44 / 40 / 36

  function styleVars(el) {
    if (CFG.style === 'vibrant') {
      el.style.setProperty('--m-bg', 'var(--md-sys-color-tertiary-container)');
      el.style.setProperty('--m-fg', 'var(--md-sys-color-on-tertiary-container)');
      el.style.setProperty('--m-icon', 'var(--md-sys-color-on-tertiary-container)');
      el.style.setProperty('--m-sel-bg', 'var(--md-sys-color-tertiary)');
      el.style.setProperty('--m-sel-fg', 'var(--md-sys-color-on-tertiary)');
    } else {
      el.style.setProperty('--m-bg', 'var(--md-sys-color-surface-container-low)');
      el.style.setProperty('--m-fg', 'var(--md-sys-color-on-surface)');
      el.style.setProperty('--m-icon', 'var(--md-sys-color-on-surface-variant)');
      el.style.setProperty('--m-sel-bg', 'var(--md-sys-color-tertiary-container)');
      el.style.setProperty('--m-sel-fg', 'var(--md-sys-color-on-tertiary-container)');
    }
    el.style.setProperty('--m-item-h', itemHeight() + 'px');
    el.style.setProperty('--m-dur', CFG.duration + 'ms');
    el.style.setProperty('--m-cdur', CFG.closeDuration + 'ms');
    // fade leads: collapse waits --m-coldelay, then runs for the remainder
    const lead = Math.round(CFG.closeDuration * CFG.closeFadeLead);
    el.style.setProperty('--m-coldelay', lead + 'ms');
    el.style.setProperty('--m-coldur', (CFG.closeDuration - lead) + 'ms');
    el.style.setProperty('--m-shadow', 'var(--md-sys-elevation-level' + CFG.elevation + ')');
  }

  /* ---------- build ---------- */
  function buildPanel(items) {
    const panel = document.createElement('div');
    panel.className = 'mdm-panel';
    panel.setAttribute('role', 'menu');
    panel.tabIndex = -1;
    styleVars(panel);
    const list = document.createElement('div');
    list.className = 'mdm-list';
    panel.appendChild(list);
    const itemEls = [];

    items.forEach(node => {
      if (node.divider) {
        const sep = document.createElement(CFG.group === 'gap' ? 'div' : 'hr');
        sep.className = CFG.group === 'gap' ? 'mdm-gap' : 'mdm-divider';
        if (CFG.group !== 'gap') sep.setAttribute('role', 'separator');
        list.appendChild(sep); itemEls.push(null); return;
      }
      if (node.header) {
        const h = document.createElement('div');
        h.className = 'mdm-grouplabel'; h.textContent = node.header;
        list.appendChild(h); itemEls.push(null); return;
      }
      const it = document.createElement('div');
      it.className = 'mdm-item' + (node.disabled ? ' disabled' : '') + (node.selected ? ' selected' : '');
      const selectable = node.select === 'single' || node.select === 'multi';
      it.setAttribute('role', node.select === 'multi' ? 'menuitemcheckbox' : (node.select === 'single' ? 'menuitemradio' : 'menuitem'));
      if (selectable) it.setAttribute('aria-checked', node.selected ? 'true' : 'false');
      if (node.submenu) { it.setAttribute('aria-haspopup', 'menu'); it.setAttribute('aria-expanded', 'false'); }
      if (node.disabled) it.setAttribute('aria-disabled', 'true');

      let html = '<span class="state"></span>';
      if (selectable) html += `<span class="check md-ic-lig">check</span>`;
      if (node.swatch) html += `<span class="swatch" style="background:${node.swatch}"></span>`;
      else if (node.icon) html += `<span class="lead">${node.icon}</span>`;
      else if (selectable) { /* check occupies lead slot already */ }
      html += `<span class="body"><span class="label">${node.label || ''}</span>` +
              (node.support ? `<span class="support">${node.support}</span>` : '') + `</span>`;
      if (node.trailingText) html += `<span class="trail-text">${node.trailingText}</span>`;
      if (node.badge) html += `<span class="badge">${node.badge}</span>`;
      if (node.trailingIcon) html += `<span class="trail-ic">${node.trailingIcon}</span>`;
      if (node.submenu) html += `<span class="submenu-arrow">chevron_right</span>`;
      it.innerHTML = html;
      // check glyph needs the icon font
      const chk = it.querySelector('.check'); if (chk) chk.style.fontFamily = "'Material Symbols Outlined'";
      list.appendChild(it); itemEls.push(it);
    });

    panel._itemEls = itemEls;
    return panel;
  }

  /* ---------- geometry ---------- */
  function positionPanel(panel, ref, mode) {
    const pw = panel.offsetWidth, ph = panel.offsetHeight;
    const vw = innerWidth, vh = innerHeight, m = 8, gap = 4;
    let x, y, ox = 'left', oy = 'top';

    if (mode === 'bottom') {
      x = ref.left; y = ref.bottom + gap;
      if (y + ph > vh - m && ref.top - ph - gap >= m) { y = ref.top - ph - gap; oy = 'bottom'; }
      if (x + pw > vw - m) { x = Math.max(m, ref.right - pw); ox = 'right'; }
      x = Math.max(m, x);
    } else if (mode === 'right') {                 // submenu, ref = parent item rect
      x = ref.right; y = ref.top - 8;
      if (x + pw > vw - m) { x = ref.left - pw; ox = 'right'; }        // flip to left
      x = Math.max(m, x);
      if (y + ph > vh - m) { y = Math.max(m, vh - m - ph); oy = 'bottom'; }
      y = Math.max(m, y);
    } else {                                        // context, ref = point
      x = ref.left; y = ref.top;
      if (x + pw > vw - m) { x = Math.max(m, ref.left - pw); ox = 'right'; }
      if (y + ph > vh - m) { y = Math.max(m, ref.top - ph); oy = 'bottom'; }
      x = Math.max(m, x); y = Math.max(m, y);
    }

    if (ph > vh - 2 * m) {                          // too tall → scroll
      panel.style.maxHeight = (vh - 2 * m) + 'px';
      panel.classList.add('scrollable');
      y = m; oy = 'top';
    }
    panel.style.left = x + 'px';
    panel.style.top = y + 'px';
    panel.style.transformOrigin = ox + ' ' + oy;
  }

  function applyRadii() {
    stack.forEach((e, i) => {
      let r = CFG.radius;
      if (stack.length > 1) r = (i === stack.length - 1) ? Math.min(28, CFG.radius + 8) : Math.max(4, CFG.radius - 4);
      e.el.style.setProperty('--m-radius', r + 'px');
    });
  }

  function animateIn(panel) {
    if (CFG.instant || !CFG.motion) return;
    // expressive = scaleY from the top (content expands downward + shadow
    // scales with the box); pop = uniform scale. Class is removed on finish so
    // no transform lingers on the resting menu.
    const cls = CFG.enterStyle === 'expressive' ? 'enter-exp' : 'enter';
    panel.classList.add(cls);
    panel.addEventListener('animationend', () => panel.classList.remove(cls), { once: true });
  }

  /* ---------- navigation helpers ---------- */
  const navigable = e => e.items.map((n, i) => (!n.divider && !n.header && !n.disabled) ? i : -1).filter(i => i >= 0);
  const firstNav = e => { const n = navigable(e); return n.length ? n[0] : -1; };
  const lastNav = e => { const n = navigable(e); return n.length ? n[n.length - 1] : -1; };

  function setFocus(e, idx, fromHover) {
    if (idx == null || idx < 0) return;
    e.itemEls.forEach((el, j) => { if (el) el.classList.toggle('focused', j === idx); });
    e.focusIdx = idx;
    const el = e.itemEls[idx];
    if (el) { try { el.focus({ preventScroll: !!fromHover }); } catch (_) { el.focus(); } if (!fromHover) el.scrollIntoView({ block: 'nearest' }); }
  }
  function moveFocus(e, dir) {
    const nav = navigable(e); if (!nav.length) return;
    let pos = nav.indexOf(e.focusIdx);
    pos = pos < 0 ? (dir > 0 ? 0 : nav.length - 1) : (pos + dir + nav.length) % nav.length;
    setFocus(e, nav[pos]);
  }
  function typeahead(e, ch) {
    const nav = navigable(e); const c = ch.toLowerCase();
    const start = nav.indexOf(e.focusIdx);
    for (let k = 1; k <= nav.length; k++) {
      const idx = nav[(start + k + nav.length) % nav.length];
      const lbl = (e.items[idx].label || '').toLowerCase();
      if (lbl.startsWith(c)) { setFocus(e, idx); return; }
    }
  }

  /* ---------- open / close ---------- */
  function openRoot(items, opts) {
    opts = opts || {};
    if (stack.length && stack[0].openerEl && stack[0].openerEl === opts.openerEl) { closeAll(); return; } // toggle off
    closeAll(true);
    ensureLayer();
    layer.classList.toggle('instant', CFG.instant);
    onSelectCb = opts.onSelect || null;

    scrim = document.createElement('div');
    scrim.className = 'mdm-scrim';
    layer.appendChild(scrim);
    scrim.addEventListener('pointerdown', () => closeAll());
    scrim.addEventListener('contextmenu', ev => { ev.preventDefault(); closeAll(); });

    const panel = buildPanel(items);
    layer.appendChild(panel);
    const entry = { el: panel, items, itemEls: panel._itemEls, focusIdx: -1, level: 0, ownerItemEl: null, openerEl: opts.openerEl || null };
    stack.push(entry);
    wire(entry);

    let ref, mode;
    if (opts.point) { ref = { left: opts.point.x, top: opts.point.y, right: opts.point.x, bottom: opts.point.y }; mode = 'point'; }
    else { ref = opts.openerEl.getBoundingClientRect(); mode = 'bottom'; }
    positionPanel(panel, ref, mode);
    applyRadii();
    animateIn(panel);
    if (opts.openerEl) opts.openerEl.setAttribute('data-menu-open', '');
    document.addEventListener('keydown', globalKey, true);
    if (opts.viaKeyboard) setFocus(entry, firstNav(entry)); else panel.focus({ preventScroll: true });
  }

  function openSubmenu(parent, idx) {
    const node = parent.items[idx], itemEl = parent.itemEls[idx];
    if (!node.submenu) return null;
    if (parent.openChildIdx === idx && stack[parent.level + 1]) return stack[parent.level + 1];
    closeDeeperThan(parent.level);
    const panel = buildPanel(node.submenu);
    layer.appendChild(panel);
    const entry = { el: panel, items: node.submenu, itemEls: panel._itemEls, focusIdx: -1, level: parent.level + 1, ownerItemEl: itemEl, ownerEntry: parent };
    stack.push(entry);
    wire(entry);
    parent.openChildIdx = idx;
    itemEl.classList.add('branch-open');
    itemEl.setAttribute('aria-expanded', 'true');
    positionPanel(panel, itemEl.getBoundingClientRect(), 'right');
    applyRadii();
    animateIn(panel);
    return entry;
  }

  function closeDeeperThan(level) {
    while (stack.length - 1 > level) {
      const e = stack.pop();
      if (e.ownerItemEl) { e.ownerItemEl.classList.remove('branch-open'); e.ownerItemEl.setAttribute('aria-expanded', 'false'); }
      if (e.ownerEntry) e.ownerEntry.openChildIdx = null;
      e.el.remove();
    }
    applyRadii();
  }

  function closeAll(immediate) {
    clearTimeout(hoverTimer);
    if (!stack.length && !scrim) return;
    const opener = stack[0] && stack[0].openerEl;
    const panels = stack.map(e => e.el);
    stack.forEach(e => { if (e.ownerItemEl) e.ownerItemEl.classList.remove('branch-open'); });
    stack = [];
    const finish = () => { panels.forEach(p => p.remove()); if (scrim) { scrim.remove(); scrim = null; } };
    const reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (immediate || CFG.instant || !CFG.motion || reduce) { finish(); }
    else {
      const exp = CFG.enterStyle === 'expressive';
      const exitCls = exp ? 'exit-exp' : 'exit';   // exit mirrors the enter style
      panels.forEach(p => {
        p.classList.remove('enter', 'enter-exp');
        p.classList.add(exitCls);
        if (exp && !CFG.closeFade) p.classList.add('no-fade');
      });
      if (scrim) { scrim.remove(); scrim = null; }
      setTimeout(finish, exp ? CFG.closeDuration : 160);
    }
    if (opener) { opener.removeAttribute('data-menu-open'); if (!immediate) { try { opener.focus(); } catch (_) {} } }
    document.removeEventListener('keydown', globalKey, true);
  }

  /* ---------- activation ---------- */
  function ripple(el) {
    if (CFG.instant) return;
    const r = el.getBoundingClientRect(), s = Math.max(r.width, r.height);
    const rp = document.createElement('span'); rp.className = 'mdm-ripple';
    rp.style.width = rp.style.height = s + 'px';
    rp.style.left = (r.width / 2 - s / 2) + 'px';
    rp.style.top = (r.height / 2 - s / 2) + 'px';
    el.appendChild(rp); rp.addEventListener('animationend', () => rp.remove());
  }

  function activate(entry, idx) {
    const node = entry.items[idx], el = entry.itemEls[idx];
    if (!node || node.disabled) return;
    ripple(el);
    if (node.submenu) { const sub = openSubmenu(entry, idx); if (sub) setFocus(sub, firstNav(sub)); return; }

    if (node.select === 'multi') {
      node.selected = !node.selected;
      el.classList.toggle('selected', node.selected);
      el.setAttribute('aria-checked', node.selected ? 'true' : 'false');
      if (node.onSelect) node.onSelect(node, entry.items);
      if (onSelectCb) onSelectCb(node, { keepOpen: true, items: entry.items });
      return;                                   // multi-select stays open
    }
    if (node.select === 'single') {
      entry.items.forEach((n, j) => {
        if (n !== node && n.group === node.group && n.select === 'single') {
          n.selected = false; const e2 = entry.itemEls[j];
          if (e2) { e2.classList.remove('selected'); e2.setAttribute('aria-checked', 'false'); }
        }
      });
      node.selected = true; el.classList.add('selected'); el.setAttribute('aria-checked', 'true');
      if (node.onSelect) node.onSelect(node, entry.items);
      if (onSelectCb) onSelectCb(node, { items: entry.items });
      closeAll();
      return;
    }
    if (node.onSelect) node.onSelect(node);
    if (onSelectCb) onSelectCb(node, {});
    closeAll();
  }

  /* ---------- wiring per panel ---------- */
  function wire(entry) {
    entry.itemEls.forEach((el, idx) => {
      if (!el) return;
      const node = entry.items[idx];
      el.addEventListener('click', ev => { ev.stopPropagation(); activate(entry, idx); });
      el.addEventListener('mouseenter', () => {
        if (node.disabled) { clearTimeout(hoverTimer); return; }
        setFocus(entry, idx, true);
        clearTimeout(hoverTimer);
        if (entry.openChildIdx != null && entry.openChildIdx !== idx) closeDeeperThan(entry.level);
        if (node.submenu) hoverTimer = setTimeout(() => openSubmenu(entry, idx), 140);
      });
    });
  }

  /* ---------- keyboard ---------- */
  function globalKey(e) {
    if (!stack.length) return;
    const entry = stack[stack.length - 1];
    const k = e.key;
    if (k === 'Escape') { e.preventDefault(); if (stack.length > 1) closeDeeperThan(entry.ownerEntry.level); else closeAll(); return; }
    if (k === 'ArrowDown') { e.preventDefault(); moveFocus(entry, 1); return; }
    if (k === 'ArrowUp') { e.preventDefault(); moveFocus(entry, -1); return; }
    if (k === 'Home') { e.preventDefault(); setFocus(entry, firstNav(entry)); return; }
    if (k === 'End') { e.preventDefault(); setFocus(entry, lastNav(entry)); return; }
    if (k === 'ArrowRight') {
      const node = entry.items[entry.focusIdx];
      if (node && node.submenu) { e.preventDefault(); const sub = openSubmenu(entry, entry.focusIdx); if (sub) setFocus(sub, firstNav(sub)); }
      return;
    }
    if (k === 'ArrowLeft') { if (stack.length > 1) { e.preventDefault(); closeDeeperThan(entry.ownerEntry.level); } return; }
    if (k === 'Enter' || k === ' ') { e.preventDefault(); if (entry.focusIdx >= 0) activate(entry, entry.focusIdx); return; }
    if (k === 'Tab') { e.preventDefault(); closeAll(); return; }
    if (k.length === 1 && /\S/.test(k)) typeahead(entry, k);
  }

  /* reposition strategy: dismiss on scroll / resize (standard anchored behavior) */
  addEventListener('scroll', () => { if (stack.length) closeAll(true); }, true);
  addEventListener('resize', () => { if (stack.length) closeAll(true); });

  /* ---------- public API ---------- */
  window.MDMenu = {
    open(openerEl, items, opts) { openRoot(items, Object.assign({ openerEl }, opts || {})); },
    openAt(point, items, opts) { openRoot(items, Object.assign({ point }, opts || {})); },
    close() { closeAll(); },
    config(patch) { Object.assign(CFG, patch); },
    getConfig() { return Object.assign({}, CFG); },
  };
})();
