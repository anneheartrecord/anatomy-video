// Video layer over a live figure page (an Anatomy figure, or any page whose motion runs on requestAnimationFrame).
// Needs clock.js loaded first, window.TL (timeline.js from timeline.py) and window.VIDEO (from video.json).
// It fits the figure card into the frame, draws the series pill, cover title, scene titles and subtitles on a
// transparent canvas above it, replays scheduled pointer / key actions on the virtual clock, and defines
// window.render(t). ?cover=1 hides subtitles, for exporting the cover image.
(() => {
  const V = window.VIDEO, TL = window.TL, SC = TL.scenes, COVER = location.search.includes('cover');
  const [W, H] = V.size || [1080, 1920];
  const C = {}; SC.forEach((s) => { C[s.name] = Object.assign({ _start: s.start }, s.cues); });
  const light = () => document.body.dataset.theme === 'light';
  const css = (name, fallback) => getComputedStyle(document.body).getPropertyValue(name).trim() || fallback;
  const RED = '#e5372b', YEL = '#ffd84d', CN = '"Noto Sans CJK SC","PingFang SC",sans-serif';

  // ---------- time of an action: seconds, "scene", "scene.cue", plus an optional "after" in seconds ----------
  function timeOf(a) {
    let t = a.at;
    if (typeof t === 'string') {
      const [s, c] = t.split('.');
      if (!C[s]) throw new Error(`overlay.js: unknown scene "${s}" in action at "${a.at}"`);
      t = c ? C[s][c] : C[s]._start;
      if (t === undefined) throw new Error(`overlay.js: unknown cue "${a.at}"`);
    }
    return (t + (a.after || 0)) * 1000;
  }
  const ACTIONS = (V.actions || []).map((a) => Object.assign({}, a, { ms: timeOf(a), done: false })).sort((x, y) => x.ms - y.ms);

  // ---------- synthetic input on the figure ----------
  // coordinates are fractions of the figure's stage (Anatomy pages name it .iso-stage or .<prefix>-stage)
  const target = () => document.querySelector(V.figure?.target || '.iso-stage, [class$="-stage"], [class*="-stage "], .iso-svg, svg');
  const chain = (el) => { const out = []; for (let n = el; n && n !== document.documentElement; n = n.parentElement) out.push(n); return out; };
  function pointAt([fx, fy]) { const b = target().getBoundingClientRect(); return [b.left + fx * b.width, b.top + fy * b.height]; }
  let lastHit = null;
  function pointer(type, xy, extra = {}) {
    const [x, y] = pointAt(xy), hit = document.elementFromPoint(x, y) || target();
    const init = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse', isPrimary: true, ...extra };
    if (type === 'pointermove' && hit !== lastHit) {      // enter / leave do not bubble: fire them along the ancestor chain, like a browser
      const was = lastHit ? chain(lastHit) : [], now = chain(hit);
      if (lastHit) { lastHit.dispatchEvent(new PointerEvent('pointerout', init)); was.filter((n) => !now.includes(n)).forEach((n) => n.dispatchEvent(new PointerEvent('pointerleave', { ...init, bubbles: false }))); }
      hit.dispatchEvent(new PointerEvent('pointerover', init));
      now.filter((n) => !was.includes(n)).reverse().forEach((n) => n.dispatchEvent(new PointerEvent('pointerenter', { ...init, bubbles: false })));
      lastHit = hit;
    }
    hit.dispatchEvent(new PointerEvent(type, init));
    if (type === 'pointermove') hit.dispatchEvent(new MouseEvent('mousemove', init));
    return hit;
  }
  function leave() {
    const el = lastHit || target();
    const init = { bubbles: true, composed: true, pointerId: 1, pointerType: 'mouse', isPrimary: true, clientX: -10, clientY: -10 };
    el.dispatchEvent(new PointerEvent('pointerout', init));
    chain(el).forEach((n) => { n.dispatchEvent(new PointerEvent('pointerleave', { ...init, bubbles: false })); n.dispatchEvent(new MouseEvent('mouseleave', { ...init, bubbles: false })); });
    lastHit = null;
  }
  function key(k) {
    const el = document.querySelector(V.figure?.keyTarget || '.iso-stage') || document.activeElement || document.body;
    el.focus?.({ preventScroll: true });
    ['keydown', 'keyup'].forEach((type) => el.dispatchEvent(new KeyboardEvent(type, { key: k, code: k, bubbles: true, cancelable: true })));
  }
  const easeIO = (x) => (x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x));
  window.__clock.onStep((ms) => {
    for (const a of ACTIONS) {
      if (a.do === 'glide' && ms >= a.ms && !a.done) {       // a slow pointer move from -> to over dur seconds
        const p = easeIO((ms - a.ms) / (1000 * (a.dur || 1)));
        pointer('pointermove', [a.from[0] + (a.to[0] - a.from[0]) * p, a.from[1] + (a.to[1] - a.from[1]) * p]);
        if (p >= 1) a.done = true;
        continue;
      }
      if (a.done || ms < a.ms) continue;
      a.done = true;
      if (a.do === 'hover') pointer('pointermove', [a.x, a.y]);
      else if (a.do === 'leave') leave();
      else if (a.do === 'click') { pointer('pointerdown', [a.x, a.y], { buttons: 1 }); pointer('pointerup', [a.x, a.y]); pointer('click', [a.x, a.y]); }
      else if (a.do === 'key') key(a.key);
      else if (a.do === 'eval') (0, eval)(a.js);
      else throw new Error(`overlay.js: unknown action "${a.do}"`);
    }
  });

  // ---------- layout: fit the card into the frame ----------
  const root = () => document.querySelector(V.figure?.root || '.iso-page, main, body > *');
  function layout() {
    const el = root(); el.style.transform = ''; el.style.transformOrigin = '0 0';
    // the legend / caption under the card is for web readers; the narration and subtitles carry it in a video
    if (V.figure?.caption !== true) document.querySelectorAll('figcaption, .iso-legend').forEach((n) => { n.style.display = 'none'; });
    const box = el.getBoundingClientRect(), f = V.figure || {};
    const top = f.top ?? 660, width = f.width ?? W * 0.92, maxH = f.height ?? 720;
    const s = Math.min(width / box.width, maxH / box.height);
    // transform-origin is the element's own top-left, so the translate is not scaled
    const x = (W - box.width * s) / 2 - box.left, y = top + (maxH - box.height * s) / 2 - box.top;
    el.style.transform = `translate(${x}px, ${y}px) scale(${s})`;
  }

  // ---------- overlay drawing ----------
  const cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  Object.assign(cv.style, { position: 'fixed', left: '0', top: '0', width: W + 'px', height: H + 'px', pointerEvents: 'none', zIndex: 2147483647 });
  const g = cv.getContext('2d');
  const ink = () => (light() ? '#17171a' : '#ececec');
  const soft = () => (light() ? 'rgba(23,23,26,.55)' : 'rgba(236,236,236,.6)');
  function txt(s, x, y, size, col, o = {}) { g.font = `${o.w || 900} ${size}px ${o.f || CN}`; g.fillStyle = col; g.textAlign = o.a || 'center'; g.globalAlpha = o.al ?? 1; g.fillText(s, x, y); g.globalAlpha = 1; return g.measureText(s).width; }
  function tw(s, size, w = 900) { g.font = `${w} ${size}px ${CN}`; return g.measureText(s).width; }
  function rr(x, y, w, h, r, col) { g.fillStyle = col; g.beginPath(); g.roundRect(x, y, w, h, r); g.fill(); }
  function strokeRR(x, y, w, h, r, col, lw) { g.strokeStyle = col; g.lineWidth = lw; g.beginPath(); g.roundRect(x, y, w, h, r); g.stroke(); }
  const ease = (x) => (x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x));
  const bump = (x) => (x > 0 && x < 0.45 ? Math.sin(x / 0.45 * Math.PI) : 0);
  function splitHalf(s) { const mid = Math.ceil(s.length / 2), bad = (i) => /[A-Za-z0-9.%×]/.test(s[i - 1] || '') && /[A-Za-z0-9.%×]/.test(s[i] || ''); for (let d = 0; d < mid; d++) for (const i of [mid + d, mid - d]) if (i > 0 && i < s.length && !bad(i) && s[i] !== ' ' && !'、，。'.includes(s[i])) return [s.slice(0, i).trim(), s.slice(i).trim()]; return [s]; }
  function subtitle(t) {
    const s = TL.subs.find((x) => t >= x[0] && t < x[1]); if (!s) return;
    const lines = s[2].length > 14 ? splitHalf(s[2]) : [s[2]], size = 54, h = lines.length * 74 + 34, w = Math.max(...lines.map((l) => tw(l, size, 800))) + 70, cx = W / 2 - 20, y = H * 0.776;
    rr(cx - w / 2, y - h / 2, w, h, 22, 'rgba(20,20,22,.88)'); lines.forEach((l, i) => txt(l, cx, y - h / 2 + 75 + i * 74, size, '#fff', { w: 800 }));
  }
  function header(t, i) {
    if (V.pill) { const pw = tw(V.pill, 42) + 76; rr(W / 2 - pw / 2, 196, pw, 80, 40, ink()); txt(V.pill, W / 2, 251, 42, light() ? YEL : '#17171a'); }
    const cur = SC[i], prev = SC[i - 1], k = i ? ease((t - cur.start) / 0.35) : 1;
    const draw = (name, a) => {
      if (a <= 0.003) return;
      g.save(); g.globalAlpha = a;
      if (name === SC[0].name && V.cover) {            // cover: two big lines, the second white on red
        const p = 1 + 0.04 * bump(t - (V.cover.pulse ? C[V.cover.pulse.split('.')[0]]?.[V.cover.pulse.split('.')[1]] ?? -9 : -9));
        g.save(); g.translate(W / 2, 430); g.scale(p, p); txt(V.cover.l1, 0, 0, V.cover.s1 || 140, ink()); g.restore();
        const s2 = V.cover.s2 || 108, w = tw(V.cover.l2, s2) + 110;
        g.save(); g.translate(W / 2, 560); g.rotate(-0.02); g.scale(p, p); rr(-w / 2, -s2 * 0.78, w, s2 * 1.36, 24, RED); txt(V.cover.l2, 0, s2 * 0.38, s2, '#fff'); g.restore();
      } else {
        const h = (V.titles || {})[name] || {};
        if (h.tag) { const w = tw(h.tag, 40) + 52; rr(W / 2 - w / 2, 300, w, 60, 30, h.tagColor || '#ff7a00'); txt(h.tag, W / 2, 344, 40, '#fff'); }
        if (h.title) txt(h.title, W / 2, 470, 86, ink());
        if (h.sub) txt(h.sub, W / 2, 540, 40, soft(), { w: 700 });
      }
      g.restore();
    };
    if (prev && k < 1) draw(prev.name, 1 - k);
    draw(cur.name, k);
    if ((i === 0 || (i === 1 && k < 1)) && V.chips) {   // teaser chips under the cover
      const a = i === 0 ? 1 : 1 - k, ws = V.chips.map((l) => tw(l, 42) + 70);
      let x = W / 2 - (ws.reduce((p, q) => p + q, 0) + 20 * (ws.length - 1)) / 2;
      g.globalAlpha = a; V.chips.forEach((l, j) => { strokeRR(x, 1605, ws[j], 88, 44, ink(), 6); txt(l, x + ws[j] / 2, 1663, 42, ink()); x += ws[j] + 20; }); g.globalAlpha = 1;
    }
  }
  function drawOverlay(t) {
    g.clearRect(0, 0, W, H);
    let i = 0; for (let k = 0; k < SC.length; k++) if (t >= SC[k].start) i = k;
    header(t, i);
    if (!COVER) subtitle(t);
  }

  window.ready = false;
  window.render = (t) => { window.__clock.advanceTo(t * 1000); drawOverlay(t); };
  addEventListener('load', () => {
    document.documentElement.style.cssText += `;width:${W}px;height:${H}px;overflow:hidden;background:${css('--anatomy-page', light() ? '#f4f1ea' : '#0b0b0b')}`;
    Object.assign(document.body.style, { margin: '0', width: W + 'px', height: H + 'px', overflow: 'hidden' });
    document.body.appendChild(cv);
    document.fonts.ready.then(() => { layout(); window.render(0); window.ready = true; });
  });
})();
