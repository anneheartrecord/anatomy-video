#!/usr/bin/env python3
"""Transcribe the narration with word timestamps (Whisper) -> audio/voice_segments.json

  align.py audio/voice.wav audio/voice_segments.json --lang zh

Uses mlx-whisper on Apple Silicon when available, otherwise faster-whisper.
If neither is installed, run it through uv without installing anything globally:
  uv run --with mlx-whisper python align.py ...        (Apple Silicon)
  uv run --with faster-whisper python align.py ...     (elsewhere)

Whisper hallucinates empty or repeated segments at the very end of the audio; those are dropped here.
The transcript itself is only used for timing: timeline.py aligns it back to your script text,
so homophone mistakes in recognition do not reach the subtitles.
"""
import argparse, json


def transcribe(path, lang, prompt):
    try:
        import mlx_whisper
        r = mlx_whisper.transcribe(path, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language=lang,
                                   word_timestamps=True, initial_prompt=prompt)
        return r['segments']
    except ImportError:
        from faster_whisper import WhisperModel
        model = WhisperModel('large-v3', compute_type='int8')
        segs, _ = model.transcribe(path, language=lang, word_timestamps=True, initial_prompt=prompt)
        return [{'start': s.start, 'end': s.end, 'text': s.text,
                 'words': [{'start': w.start, 'end': w.end, 'word': w.word} for w in s.words]} for s in segs]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('audio'); ap.add_argument('out')
    ap.add_argument('--lang', default='zh')
    ap.add_argument('--prompt', default='', help='domain words that help recognition, e.g. product names')
    a = ap.parse_args()
    segs = transcribe(a.audio, a.lang, a.prompt or None)
    kept = [s for s in segs if s['text'].strip() and s['end'] - s['start'] >= .3]
    json.dump(kept, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f'{a.out}: {len(kept)} segments (dropped {len(segs) - len(kept)}), ends at {kept[-1]["end"]:.2f}s')
    print('  first:', kept[0]['text'][:40]); print('  last: ', kept[-1]['text'][-40:])


if __name__ == '__main__':
    main()
