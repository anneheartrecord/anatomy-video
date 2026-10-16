#!/usr/bin/env python3
"""Wrap a built live page (an Anatomy figure) into a video page that render.py / render_parallel.py can render.

  wrap_figure.py figure.html video.json index.html

It inlines clock.js as the first script in <head> (so the figure's own scripts run on virtual time),
then window.VIDEO from video.json and a <script src="timeline.js"> (written by scripts/voice/timeline.py),
and overlay.js before </body>. The figure file itself is not modified.

video.json:
{
  "size": [1080, 1920],
  "pill": "机器讲概念 · 第 1 课",                         # series label on every frame ("" to hide)
  "cover": {"l1": "缓存为什么快", "l2": "像一把锁", "pulse": "cover.lock"},
  "chips": ["命中", "失效", "重算"],                        # teaser chips under the cover
  "titles": {"how": {"tag": "原理", "title": "每根销子都对上", "sub": "钥匙 = 缓存键"}},
  "figure": {"top": 660, "width": 990, "height": 720},      # where the card goes (px); optional "target", "root", "caption": true
  "actions": [                                             # input replayed on the virtual clock
    {"at": "how.match", "do": "glide", "from": [0.25, 0.5], "to": [0.75, 0.5], "dur": 1.6},
    {"at": "how.miss", "do": "hover", "x": 0.3, "y": 0.5},
    {"at": "end", "after": 0.5, "do": "leave"},
    {"at": 12.0, "do": "key", "key": "ArrowRight"}
  ]
}
"at" is seconds, a scene name, or "scene.cue" from audio/scenes.json; x / y are fractions of the figure's stage box
(.iso-stage or .<prefix>-stage; override with figure.target). "eval" runs JS on the page, e.g. clicking a button.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    fig, cfg, out = sys.argv[1:]
    html = open(fig, encoding='utf-8').read()
    video = json.load(open(cfg, encoding='utf-8'))
    clock = open(os.path.join(HERE, 'clock.js'), encoding='utf-8').read()
    overlay = open(os.path.join(HERE, 'overlay.js'), encoding='utf-8').read()
    head = (f'<script>{clock}</script>\n<script>window.VIDEO = {json.dumps(video, ensure_ascii=False)};</script>\n'
            '<script src="timeline.js"></script>\n')
    i = html.lower().find('<head>')
    if i < 0:
        sys.exit('wrap_figure.py: no <head> in the figure page')
    html = html[:i + 6] + head + html[i + 6:]
    j = html.lower().rfind('</body>')
    if j < 0:
        sys.exit('wrap_figure.py: no </body> in the figure page')
    html = html[:j] + f'<script>{overlay}</script>\n' + html[j:]
    open(out, 'w', encoding='utf-8').write(html)
    print(f'{out}: {fig} + clock + overlay, {len(video.get("actions", []))} actions')


if __name__ == '__main__':
    main()
