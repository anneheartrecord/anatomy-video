#!/usr/bin/env python3
"""Render a render(t) page in parallel: split the timeline into N frame ranges, render each with
render.py in its own browser, join the pieces losslessly, then mux the audio once.

  render_parallel.py index.html out/<topic>.mp4 --size 1080x1920 --fps 30 --duration 94.2 --audio audio/mix.wav
  render_parallel.py index.html out/<topic>.mp4 --duration 30 --workers 6

Because render(t) depends only on t, every frame range can be rendered independently. Ranges are cut on
frame numbers, so the joined video has exactly round(fps * duration) frames, the same as render.py.
Each worker runs its own Chromium (~300–500 MB of memory), so keep workers ≤ CPU cores.
With --subframes > 1, the first frame of each range is blended from fewer samples (slightly less blur);
render sequentially with render.py if that ever shows.
"""
import argparse, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('page'); ap.add_argument('out')
    ap.add_argument('--size', default='1920x1080')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--duration', type=float, required=True)
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--subframes', type=int, default=1)
    ap.add_argument('--audio')
    ap.add_argument('--crf', type=int, default=16)
    ap.add_argument('--workers', type=int, default=max(1, min(4, (os.cpu_count() or 2) - 2)),
                    help='parallel browsers (default: CPU cores - 2, at most 4; more rarely helps, the bottleneck is screenshots)')
    a = ap.parse_args()

    frames = round(a.fps * a.duration)
    n = max(1, min(a.workers, frames // a.fps or 1))          # at least ~1 second per worker
    cuts = [round(frames * k / n) for k in range(n + 1)]
    tmp = tempfile.mkdtemp(prefix='render_parallel_')
    t0 = time.time()
    procs = []
    for k in range(n):
        f0, f1 = cuts[k], cuts[k + 1]
        seg = os.path.join(tmp, f'seg{k:02d}.ts')   # MPEG-TS: joins without dropping frames at B-frame boundaries
        cmd = ['python3', os.path.join(HERE, 'render.py'), a.page, seg, '--size', a.size, '--fps', str(a.fps),
               '--start', repr(a.start + f0 / a.fps), '--duration', repr((f1 - f0) / a.fps),
               '--subframes', str(a.subframes), '--crf', str(a.crf)]
        log = open(os.path.join(tmp, f'seg{k:02d}.log'), 'w')
        procs.append((k, f0, f1, seg, subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), log))
    print(f'{frames} frames in {n} ranges: ' + ', '.join(f'{f0}-{f1 - 1}' for _, f0, f1, *_ in procs), flush=True)

    failed = []
    for k, f0, f1, seg, p, log in procs:
        rc = p.wait(); log.close()
        if rc != 0:
            failed.append(k)
            print(f'  range {k} failed:\n' + open(log.name).read()[-2000:], file=sys.stderr)
        else:
            print(f'  range {k} ({f1 - f0} frames) done at {time.time() - t0:.0f}s', flush=True)
    if failed:
        sys.exit(f'ranges {failed} failed; logs in {tmp}')

    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for _, _, _, seg, _, _ in procs:
            f.write(f"file '{seg}'\n")
    video = os.path.join(tmp, 'video.mp4') if a.audio else a.out
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', video], check=True)
    joined = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', video], capture_output=True, text=True).stdout.strip()
    print(f'  joined: {joined} frames', flush=True)
    if a.audio:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-ss', str(a.start), '-i', a.audio,
                        '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', 'apad', '-c:a', 'aac', '-b:a', '192k', '-shortest', a.out], check=True)   # apad: pad the audio so no video frame is cut

    got = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                          'stream=nb_read_packets', '-of', 'csv=p=0', a.out], capture_output=True, text=True).stdout.strip()
    shutil.rmtree(tmp)
    status = 'ok' if got == str(frames) else f'MISMATCH (expected {frames})'
    print(f'{a.out}: {got} frames {status}, {a.size} @ {a.fps}fps, {n} workers, rendered in {time.time() - t0:.1f}s')
    if got != str(frames):
        sys.exit(1)


if __name__ == '__main__':
    main()
