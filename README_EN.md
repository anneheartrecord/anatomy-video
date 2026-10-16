# anatomy-video

English | [中文](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-20.10%2B-339933.svg)](https://nodejs.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-SVG%20%7C%20Canvas%20%7C%20WebGL-f7df1e.svg)](skills/anatomy-video/bridge)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-d97757.svg)](skills/anatomy-video/SKILL.md)

> Make videos with code. Explain ideas with machines.

An agent skill that combines two open-source projects and adds a bridge between them:

- **[xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video)**: the model writes a page that draws frame t, captured frame by frame into a video, with three plans and previews before building. This uses [the fork with a voiceover pipeline](https://github.com/anneheartrecord/xilo-opus-video): a written script becomes a narrated vertical short with subtitles and a cover, plus fact-checking and parallel rendering.
- **[Anatomy](https://github.com/wheresryan22/anatomy)**: a technical idea built as a real machine of many small precise parts, four-tone shading, isometric camera, moving under the pointer, with a geometry audit and optional WebGL shaders and 3D.
- **The bridge (`bridge/`, new here)**: a virtual clock takes over an Anatomy page's animation time, so the interactive machine becomes a video picture where any frame can be computed on its own; at the moment the narration says a word, the bridge injects hover, glide, key or click input, so the machine comes apart, fires or shifts on cue.

## Three outputs

| You want | Path |
|---|---|
| A video: promo, motion piece, explainer, script to video | Video workflow: brief → three plans with previews → brief.md → shot by shot → self-review → video, cover image, publish copy |
| An illustration, interactive figure or how-it-works drawing (docs, blog, landing page) | Anatomy: HTML, a lone SVG or React components |
| A video that explains a mechanism a machine can embody | Build the machine with Anatomy, narrate it, drive it from the narration, wrap it into a video |

## Results

**The dial indicator (Anatomy's smallest example), narrated**: the carriage slides when the narration says so, and the probe drops onto each gauge block as it is named.

![Dial indicator video](examples/dial-indicator-video.png)

**The Raptor engine (with a WebGL plume)**: hover takes it apart into 11 assemblies, leaving puts it back, and on ignition the WebGL plume fires in the same isometric camera.

![Raptor engine video](examples/raptor-engine-video.png)

Both are rendered frame by frame from one page: the same moment rendered twice is pixel-identical, and sequential and parallel renders match frame for frame.

## Install

```bash
npx skills add anneheartrecord/anatomy-video
```

Or copy it manually:

```bash
git clone https://github.com/anneheartrecord/anatomy-video.git
cp -r anatomy-video/skills/anatomy-video ~/.claude/skills/
```

### Requirements

- Python 3.9+ with `numpy`, `scipy` and `playwright` (`python3 -m pip install numpy scipy playwright`), then `python3 -m playwright install chromium`
- FFmpeg
- Node.js 20.10+ (Anatomy's builds and checks use only built-in modules; nothing to `npm install`)
- One voice: the `GEMINI_API_KEY` environment variable (Gemini TTS), or `edge-tts` (free, `uv tool install edge-tts`)
- Whisper for alignment: `mlx-whisper` on Apple Silicon, `faster-whisper` elsewhere; to avoid a global install, run `uv run --with mlx-whisper ...`

## Usage

Just say what you want:

```text
Turn this article into a 60-second vertical video with voiceover and subtitles (text attached)
```

```text
Draw an isometric figure explaining how a token bucket rate limiter works, interactive, light theme
```

```text
Make a vertical video about CDN cache hits and misses, explained by a working machine that does each step as the narration reaches it
```

## How the bridge works

- **`bridge/clock.js`** goes first in the page's `<head>` and takes over `requestAnimationFrame`, `performance.now`, `Date.now` and `setTimeout / setInterval`, holding time at 0; `render(t)` advances to t in fixed 1/60 s steps. Anatomy's exponential follows and springs depend on the previous frame, and this makes them pure functions of time. `IntersectionObserver` always reports visible and reduced motion is always off, so the machine never pauses as "offscreen".
- **`bridge/overlay.js`** fits the card into the vertical frame and draws the series pill, the two-line cover title, scene titles and subtitles above it; it replays the `video.json` action list, dispatching pointer and key events at the narration cue points (`pointerenter / pointerleave` along the ancestor chain, as a browser does).
- **`bridge/wrap_figure.py`** wraps a built Anatomy page into a video page without modifying it.

The full workflow and the `video.json` format are in [`references/anatomy-video.md`](skills/anatomy-video/references/anatomy-video.md); a reproducible example is in [`bridge/example/`](skills/anatomy-video/bridge/example).

## Layout

```
skills/anatomy-video/
  SKILL.md                 routing (video / figure / machine explainer) + the video workflow
  references/              video workflow references (plans, brief, craft rules, cover and opening, voiceover, fact-check, machine explainer)
  scripts/                 rendering (incl. parallel), voiceover pipeline, fact-check, QA sheet, file naming, audio tools
  templates/               vertical explainer template
  bridge/                  virtual clock, video overlay, page wrapper, example (new here)
  anatomy/                 Anatomy vendored as-is: SKILL.md, kit/, scripts/, references/, examples/
examples/                  images for this README
```

## Credits and license

- The video workflow, references and rendering scripts come from [xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video) by [周行 (Kianzzz)](https://github.com/Kianzzz).
- `anatomy/` is [Anatomy](https://github.com/wheresryan22/anatomy) by [Ryan (@wheresryan22)](https://github.com/wheresryan22), vendored unmodified.
- Sources, versions and changes for each part are in [NOTICE.md](NOTICE.md).

MIT, keeping every original copyright notice. See [LICENSE](LICENSE).
