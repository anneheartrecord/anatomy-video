#!/usr/bin/env python3
"""Script text + Whisper word timestamps -> scene starts, in-scene cues and subtitles.

  timeline.py --dir <project>          # reads audio/narration.txt, audio/voice_segments.json, audio/scenes.json
                                       # writes timeline.js (for the page) and audio/timeline.json (for mix.py)

scenes.json:
  {"scenes": [["cover", "first words of the hook", {"stamp": "a phrase from the narration"}],
              ["point1", "第一，", {"a": "...", "b": "..."}], ...],
   "kind": {"cover.stamp": "stamp", "point1.b": "coin"},      # optional, sound per cue (default pop)
   "offs": {"cover.stamp": 0.3}}                             # optional, seconds added to that cue's sound

Every anchor and cue is an exact phrase from narration.txt, searched in order. The script text is aligned to
the recognized characters with difflib, so homophone errors in recognition do not matter and subtitles use
your own wording. Video time = narration time + OFFSET, so frame 0 is a clean cover.
"""
import argparse, json, os, re
from difflib import SequenceMatcher

OFFSET, TAIL, MAX_SUB = .4, 2.6, 15


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default='.')
    a = ap.parse_args()
    os.chdir(a.dir)
    text = open('audio/narration.txt', encoding='utf-8').read().replace('\n', '')
    segs = json.load(open('audio/voice_segments.json'))
    cfg = json.load(open('audio/scenes.json'))

    norm = lambda c: c.lower() if (c.isalnum() or '一' <= c <= '鿿') else ''
    s_idx = [i for i, c in enumerate(text) if norm(c)]
    s_str = ''.join(norm(text[i]) for i in s_idx)
    a_chars, a_times = [], []
    for sg in segs:
        for w in sg.get('words', []):
            cs = [c for c in w['word'] if norm(c)]
            for k, c in enumerate(cs):
                a_chars.append(norm(c)); a_times.append(w['start'] + (w['end'] - w['start']) * k / max(1, len(cs)))
    t_of = [None] * len(s_str)
    for b in SequenceMatcher(None, s_str, ''.join(a_chars), autojunk=False).get_matching_blocks():
        for k in range(b.size):
            t_of[b.a + k] = a_times[b.b + k]
    known = [k for k, v in enumerate(t_of) if v is not None]
    if not known:
        raise SystemExit('nothing aligned: is voice_segments.json from the same narration?')
    for k in range(len(t_of)):                       # interpolate characters that did not match
        if t_of[k] is None:
            lo = max([j for j in known if j < k], default=known[0]); hi = min([j for j in known if j > k], default=known[-1])
            t_of[k] = t_of[lo] if hi == lo else t_of[lo] + (t_of[hi] - t_of[lo]) * (k - lo) / (hi - lo)
    print(f'aligned {len(known) / len(t_of):.0%} of the script characters')
    pos_of = {i: k for k, i in enumerate(s_idx)}

    def tchar(i):
        while i not in pos_of and i < len(text):
            i += 1
        return t_of[pos_of[min(i, s_idx[-1])]] + OFFSET

    def find(sub, after=0):
        i = text.find(sub, after)
        if i < 0:
            raise SystemExit(f'phrase not found in narration (after char {after}): {sub!r}')
        return i

    scenes, pos = [], 0
    for name, anchor, cues in cfg['scenes']:
        i = find(anchor, pos); pos = i + 1
        scenes.append({'name': name, 'start': round(max(0, tchar(i) - .35), 3),
                       'cues': {k: round(tchar(find(v, i)), 3) for k, v in cues.items()}})
    scenes[0]['start'] = 0.0

    # subtitles: split at punctuation, long pieces at 、 or by length; trailing punctuation is not shown
    subs = []
    for m in re.finditer(r'[^，。；：！？]+[，。；：！？]?', text):
        body = m.group().strip().rstrip('，。；：！？').strip()
        if not body:
            continue
        parts = [body]
        if len(body) > MAX_SUB:
            merged = []
            for p in [p for p in re.split(r'(?<=、)', body) if p]:
                if merged and len(merged[-1]) + len(p) <= MAX_SUB:
                    merged[-1] += p
                else:
                    merged.append(p)
            parts = merged
        off = m.start()
        for p in parts:
            i = text.find(p, off); off = i + len(p)
            subs.append([round(tchar(i) - .08, 3), None, p.rstrip('、').strip()])
    end = segs[-1]['end'] + OFFSET
    for k in range(len(subs)):
        nxt = subs[k + 1][0] if k + 1 < len(subs) else end + .3
        subs[k][1] = round(min(nxt - .04, subs[k][0] + 6), 3)

    tl = {'total': round(end + TAIL, 2), 'offset': OFFSET, 'scenes': scenes, 'subs': subs}
    json.dump(tl, open('audio/timeline.json', 'w'), ensure_ascii=False, indent=1)
    open('timeline.js', 'w').write('window.TL = ' + json.dumps(tl, ensure_ascii=False) + ';\n')
    for s in scenes:
        print(f"{s['start']:7.2f}  {s['name']:<10}", ' '.join(f'{k}={v:.1f}' for k, v in s['cues'].items()))
    print(f"{len(subs)} subtitles, total {tl['total']}s -> timeline.js, audio/timeline.json")


if __name__ == '__main__':
    main()
