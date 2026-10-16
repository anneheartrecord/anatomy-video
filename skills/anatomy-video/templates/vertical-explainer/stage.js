// Vertical explainer stage (1080×1920): frame 0 is the cover, scenes cross-fade, one-line hard subtitles.
// index.html loads timeline.js and this file, defines EP = { pill, chips, HEAD, BODY } and calls startSeries(EP).
// HEAD[name](t, c) draws the title area, BODY[name](t, c) the content area (y 560–1380); c holds the scene's cue times.
// ?cover=1 hides subtitles, for exporting the cover image (out/<topic>-封面.png).
const cv = document.getElementById('c'), g = cv.getContext('2d');
const W = 1080, H = 1920;
cv.width = innerWidth * (devicePixelRatio || 1); cv.height = innerHeight * (devicePixelRatio || 1);
const TL = window.TL, SC = TL.scenes, COVER = location.search.includes('cover');
const C = {}; SC.forEach((s, i) => { C[s.name] = Object.assign({ _start: s.start, _i: i }, s.cues); });

const BG = '#f4f1ea', INK = '#17171a', GRAY = '#8b877f', RED = '#e5372b', BLUE = '#2e6cff', GREEN = '#15a058', YEL = '#ffd84d', ORANGE = '#ff7a00', DARK = '#1c1c20', SOFT = '#e9e6df';
const CN = '"Noto Sans CJK SC","PingFang SC",sans-serif', NUM = '"Avenir Next Condensed","Noto Sans CJK SC",sans-serif';

// ---------- helpers ----------
const clamp = x => x < 0 ? 0 : x > 1 ? 1 : x;
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
function spring(x, w = 16, z = .72) { if (x <= 0) return 0; const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * x) * (Math.cos(wd * x) + (z * w / wd) * Math.sin(wd * x)); }
const pop = (t, t0) => spring(t - t0, 18, .5), rise = (t, t0) => spring(t - t0, 11, .9);
const bump = x => x > 0 && x < .45 ? Math.sin(x / .45 * Math.PI) : 0;
function rnd(s) { s = Math.sin(s * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
let ALPHA = 1;
function txt(s, x, y, size, col, o = {}) { g.font = `${o.w || 900} ${size}px ${o.f || CN}`; g.fillStyle = col; g.textAlign = o.a || 'left'; g.globalAlpha = (o.al == null ? 1 : o.al) * ALPHA; g.fillText(s, x, y); g.globalAlpha = ALPHA; return g.measureText(s).width; }
function tw(s, size, o = {}) { g.font = `${o.w || 900} ${size}px ${o.f || CN}`; return g.measureText(s).width; }
function rr(x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function fillRR(x, y, w, h, r, c) { g.fillStyle = c; rr(x, y, w, h, r); g.fill(); }
function strokeRR(x, y, w, h, r, c, lw) { g.strokeStyle = c; g.lineWidth = lw; rr(x, y, w, h, r); g.stroke(); }
function withAlpha(a, fn) { const old = ALPHA; ALPHA = old * a; if (ALPHA > .003) { g.save(); g.globalAlpha = ALPHA; fn(); g.restore(); } ALPHA = old; }
function enter(k, cx, cy, fn) { if (k <= .001) return; g.save(); g.translate(cx, cy + (1 - Math.min(k, 1)) * 30); const s = .85 + .15 * k; g.scale(s, s); g.translate(-cx, -cy); withAlpha(clamp(k * 1.6), fn); g.restore(); }
function stamp(t, t0, label, cx, cy, size, col = RED, rot = -.1) {
  if (t < t0) return; const k = spring(t - t0, 22, .62), s = 1 + 1.2 * (1 - k);
  g.save(); g.translate(cx, cy); g.rotate(rot); g.scale(s, s);
  withAlpha(clamp((t - t0) / .08), () => { const w = tw(label, size) + size * .9, h = size * 1.7; fillRR(-w / 2, -h / 2, w, h, size * .22, 'rgba(255,255,255,.85)'); strokeRR(-w / 2, -h / 2, w, h, size * .22, col, size * .1); txt(label, 0, size * .36, size, col, { a: 'center' }); });
  g.restore();
}
// pill label, x is the left edge; returns the width
function chip(k, x, y, label, bg, fg = '#fff', size = 46) { const w = tw(label, size) + size * 1.3; enter(k, x + w / 2, y, () => { fillRR(x, y - size * .95, w, size * 1.5, size * .75, bg); txt(label, x + size * .65, y + size * .2, size, fg); }); return w; }
// centered pill
function chipC(k, cx, y, label, bg, fg = '#fff', size = 46) { const w = tw(label, size) + size * 1.3; return chip(k, cx - w / 2, y, label, bg, fg, size); }
// chat bubble: side -1 left (AI), 1 right (you)
function bubble(k, side, y, label, bg, fg, size = 40) { const w = tw(label, size, { w: 700 }) + size * 1.4, x = side < 0 ? 110 : 970 - w; enter(k, x + w / 2, y, () => { fillRR(x, y - size * 1.15, w, size * 1.75, size * .87, bg); txt(label, x + size * .7, y + size * .05, size, fg, { w: 700 }); }); }
// wide card: colour bar on the left + text
function card(k, y, label, col, opt = {}) { const h = opt.h || 120, size = opt.size || 46; enter(k, 540, y, () => { fillRR(100, y - h / 2, 880, h, 24, opt.bg || '#fff'); fillRR(100, y - h / 2, 18, h, 9, col); if (opt.icon) txt(opt.icon, 150, y + size * .36, size, col); txt(label, opt.icon ? 215 : 150, y + size * .36, size, opt.fg || INK); }); }
function mark(ok, x, y, s) { g.lineCap = 'round'; g.lineWidth = s * .16; g.strokeStyle = ok ? GREEN : RED; g.beginPath(); if (ok) { g.moveTo(x - s * .4, y); g.lineTo(x - s * .1, y + s * .3); g.lineTo(x + s * .45, y - s * .35); } else { g.moveTo(x - s * .35, y - s * .35); g.lineTo(x + s * .35, y + s * .35); g.moveTo(x + s * .35, y - s * .35); g.lineTo(x - s * .35, y + s * .35); } g.stroke(); }
function coin(x, y, r) { g.fillStyle = YEL; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.strokeStyle = '#c99a00'; g.lineWidth = r * .12; g.stroke(); txt('¥', x, y + r * .38, r * 1.1, '#9a7300', { a: 'center' }); }
// cover title: line 1 black, line 2 white on a red banner
function coverTitle(t, l1, l2, s1 = 150, s2 = 116, pulseAt = -9) {
  const p = 1 + .04 * bump(t - pulseAt);
  g.save(); g.translate(540, 450); g.scale(p, p); txt(l1, 0, 0, s1, INK, { a: 'center' }); g.restore();
  g.save(); g.translate(540, 590); g.rotate(-.02); g.scale(p, p); const w = tw(l2, s2) + 110; fillRR(-w / 2, -s2 * .78, w, s2 * 1.36, 24, RED); txt(l2, 0, s2 * .38, s2, '#fff', { a: 'center' }); g.restore();
}
// scene title: small tag + big title
function sceneTitle(tag, title, tagCol = ORANGE) { if (tag) chipC(1, 540, 330, tag, tagCol, '#fff', 40); txt(title, 540, 455, 86, INK, { a: 'center' }); }
// progress row: items[cur] highlighted
function tracker(items, cur, y = 590) {
  const n = items.length, gap = 880 / n;
  items.forEach((s, i) => { const x = 100 + gap * i + gap / 2, on = i === cur, done = i < cur;
    fillRR(x - gap / 2 + 6, y - 34, gap - 12, 64, 32, on ? INK : done ? '#d7d2c7' : SOFT);
    txt(s, x, y + 10, 30, on ? YEL : done ? '#6d6a63' : GRAY, { a: 'center' }); });
}

function splitHalf(s) { const mid = Math.ceil(s.length / 2), bad = i => /[A-Za-z0-9.%×]/.test(s[i - 1] || '') && /[A-Za-z0-9.%×]/.test(s[i] || ''); for (let d = 0; d < mid; d++) for (const i of [mid + d, mid - d]) if (i > 0 && i < s.length && !bad(i) && s[i] !== ' ' && !'、，。'.includes(s[i])) return [s.slice(0, i).trim(), s.slice(i).trim()]; return [s]; }
function subtitle(t) {
  const s = TL.subs.find(x => t >= x[0] && t < x[1]); if (!s) return;
  const lines = s[2].length > 14 ? splitHalf(s[2]) : [s[2]], size = 54, h = lines.length * 74 + 34, w = Math.max(...lines.map(l => tw(l, size, { w: 800 }))) + 70, cx = 520, y = 1490;
  fillRR(cx - w / 2, y - h / 2, w, h, 22, 'rgba(20,20,22,.88)'); lines.forEach((l, i) => txt(l, cx, y - h / 2 + 75 + i * 74, size, '#fff', { a: 'center', w: 800 }));
}

function startSeries(EP) {
  const sceneAt = t => { let i = 0; for (let k = 0; k < SC.length; k++) if (t >= SC[k].start) i = k; return i; };
  const hkey = n => (EP.HEADKEY && EP.HEADKEY[n]) || n;
  window.ready = false;
  window.render = function (t) {
    const sc = cv.width / W; g.setTransform(sc, 0, 0, sc, 0, 0); ALPHA = 1; g.globalAlpha = 1;
    g.fillStyle = BG; g.fillRect(0, 0, W, H);
    // series pill on every frame, so viewers recognise the series
    if (EP.pill) { const pw = tw(EP.pill, 42) + 76; fillRR(540 - pw / 2, 196, pw, 80, 40, INK); txt(EP.pill, 540, 251, 42, YEL, { a: 'center' }); }
    const i = sceneAt(t), cur = SC[i], prev = SC[i - 1], k = i ? ease((t - cur.start) / .35) : 1;
    const hk = hkey(cur.name), hp = prev && hkey(prev.name), headSwap = prev && hp !== hk;
    if (headSwap && k < 1) withAlpha(1 - k, () => { g.save(); g.translate(0, -25 * k); EP.HEAD[hp](t, C[prev.name]); g.restore(); });
    withAlpha(headSwap ? k : 1, () => { g.save(); g.translate(0, headSwap ? 25 * (1 - k) : 0); EP.HEAD[hk](t, C[cur.name]); g.restore(); });
    if (prev && k < 1) withAlpha(1 - k, () => { g.save(); g.translate(0, -25 * k); EP.BODY[prev.name](t, C[prev.name]); g.restore(); });
    withAlpha(k, () => { g.save(); g.translate(0, 25 * (1 - k)); EP.BODY[cur.name](t, C[cur.name]); g.restore(); });
    // three teaser chips under the cover, first scene only
    if (i === 0 || (i === 1 && k < 1)) withAlpha(i === 0 ? 1 : 1 - k, () => { const ws = EP.chips.map(l => tw(l, 42) + 70); let x = 540 - (ws.reduce((a, b) => a + b, 0) + 20 * (ws.length - 1)) / 2; EP.chips.forEach((l, j) => { strokeRR(x, 1605, ws[j], 88, 44, INK, 6); txt(l, x + ws[j] / 2, 1663, 42, INK, { a: 'center' }); x += ws[j] + 20; }); });
    if (!COVER) subtitle(t);
  };
  document.fonts.load('900 60px "Noto Sans CJK SC"').then(() => document.fonts.load('800 60px "Avenir Next Condensed"')).then(() => document.fonts.ready).then(() => { window.render(0); window.ready = true; });
}
