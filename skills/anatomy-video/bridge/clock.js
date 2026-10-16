// Virtual clock for live pages (Anatomy figures and anything else driven by requestAnimationFrame).
// Load it as the FIRST classic <script> in <head>, before the page's own scripts run.
// Time stops at 0 until window.__clock.advanceTo(ms) moves it forward in fixed steps, running timers and
// animation frames in order, so the page state becomes a pure function of time:
// the same t always gives the same frame, which is what frame-by-frame rendering needs.
(() => {
  const STEP = 1000 / 60;                 // the figures' springs and follows expect ~60 fps steps
  let now = 0, rafId = 0, timerId = 0;
  const frames = new Map(), timers = new Map(), hooks = [];
  const epoch = Date.UTC(2026, 0, 1);      // fixed wall clock, so Date-based text never changes between runs

  window.requestAnimationFrame = (cb) => { frames.set(++rafId, cb); return rafId; };
  window.cancelAnimationFrame = (id) => { frames.delete(id); };
  performance.now = () => now;
  Date.now = () => epoch + now;
  window.setTimeout = (fn, ms = 0, ...args) => { timers.set(++timerId, { at: now + Math.max(0, +ms || 0), fn, args }); return timerId; };
  window.clearTimeout = (id) => { timers.delete(id); };
  window.setInterval = (fn, ms = 0, ...args) => { const every = Math.max(1, +ms || 1); timers.set(++timerId, { at: now + every, fn, args, every }); return timerId; };
  window.clearInterval = window.clearTimeout;

  // Always visible: an observer reports "intersecting" right away, so figures never pause offscreen.
  window.IntersectionObserver = class {
    constructor(cb) { this.cb = cb; }
    observe(target) { const entry = { target, isIntersecting: true, intersectionRatio: 1, boundingClientRect: target.getBoundingClientRect?.(), time: now }; queueMicrotask(() => this.cb([entry], this)); }
    unobserve() {} disconnect() {} takeRecords() { return []; }
  };
  // Never "reduced motion": a video wants the motion.
  const realMatch = window.matchMedia.bind(window);
  window.matchMedia = (q) => /prefers-reduced-motion/.test(q)
    ? { matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent() { return false; } }
    : realMatch(q);

  function fireTimers() {
    for (;;) {
      let next = null;
      for (const [id, t] of timers) if (t.at <= now && (!next || t.at < next[1].at)) next = [id, t];
      if (!next) return;
      const [id, t] = next;
      if (t.every) t.at += t.every; else timers.delete(id);
      try { t.fn(...t.args); } catch (e) { console.error(e); }
    }
  }
  function step(dt) {
    now += dt;
    hooks.forEach((h) => h(now));          // scheduled pointer / key actions land before this frame
    fireTimers();
    const due = [...frames.values()]; frames.clear();
    for (const cb of due) { try { cb(now); } catch (e) { console.error(e); } }
  }
  window.__clock = {
    get now() { return now; },
    onStep(fn) { hooks.push(fn); },
    // Advance to ms (never backwards). Rendering always starts from a fresh page, so this holds for
    // sequential renders, single stills and every range of a parallel render.
    advanceTo(ms) {
      if (ms < now - 1e-6) throw new Error(`clock.js: time went backwards (${now} -> ${ms} ms); render from a fresh page`);
      while (now + STEP <= ms + 1e-6) step(STEP);
      if (ms - now > 1e-6) step(ms - now);
    },
  };
})();
