#!/usr/bin/env python3
"""Render frame 0 plus the fullest state of every scene into one contact sheet.

  qa_stills.py index.html audio/timeline.json qa/scenes.png --size 1080x1920

"Fullest state" = 0.3 s before the next scene starts, when everything in that scene has appeared.
Frame 0 must already be a complete cover; the sheet makes overlaps, overflow and empty scenes easy to spot.
"""
import argparse, json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('page'); ap.add_argument('timeline'); ap.add_argument('out')
    ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--cell-width', type=int, default=300)
    a = ap.parse_args()
    tl = json.load(open(a.timeline))
    sc = tl['scenes']
    times = [0.0] + [round((sc[k + 1]['start'] if k + 1 < len(sc) else tl['total']) - .3, 2) for k in range(len(sc))]
    tmp = tempfile.mkdtemp()
    for i, t in enumerate(times):
        subprocess.run(['python3', os.path.join(HERE, 'render.py'), a.page, f'{tmp}/s{i:03d}.png', '--still', str(t), '--size', a.size],
                       check=True, capture_output=True)
        label = 'frame 0' if i == 0 else f'{sc[i - 1]["name"]} @ {t}s'
        print(f'{i:3d}  {label}')
    rows = (len(times) + a.cols - 1) // a.cols
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-pattern_type', 'glob', '-i', f'{tmp}/s*.png',
                    '-vf', f'scale={a.cell_width}:-1,tile={a.cols}x{rows}:padding=6', '-frames:v', '1', a.out], check=True)
    print(a.out)


if __name__ == '__main__':
    main()
