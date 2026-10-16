#!/usr/bin/env python3
"""Synthesize the whole narration in one pass, then speed it up.

  tts.py narration.txt audio/voice.wav                       # Gemini TTS (needs GEMINI_API_KEY)
  tts.py narration.txt audio/voice.wav --backend edge        # edge-tts, free, no key
  tts.py narration.txt audio/voice.wav --speed 1.0           # keep the original pace

narration.txt: one paragraph per line, plain text, no stage directions.
Do not prepend style instructions such as "read this warmly": Gemini TTS reads them out loud.
"""
import argparse, base64, json, os, subprocess, sys, tempfile, urllib.request, wave


def gemini(text, out, voice, model):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        sys.exit('GEMINI_API_KEY is not set; use --backend edge for a free voice')
    body = {'contents': [{'parts': [{'text': text}]}],
            'generationConfig': {'responseModalities': ['AUDIO'],
                                 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}}}
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                 data=json.dumps(body).encode(), headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
    part = json.load(urllib.request.urlopen(req, timeout=600))['candidates'][0]['content']['parts'][0]['inlineData']
    raw, mime = base64.b64decode(part['data']), part.get('mimeType', '')
    if 'wav' in mime:                                   # newer models return a WAV file
        open(out, 'wb').write(raw)
    else:                                               # older models return raw PCM: audio/L16;rate=24000
        rate = int(mime.split('rate=')[-1].split(';')[0]) if 'rate=' in mime else 24000
        with wave.open(out, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(raw)


def edge(text, out, voice):
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        mp3 = f.name
    subprocess.run(['edge-tts', '--voice', voice, '--text', text, '--write-media', mp3], check=True, capture_output=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-ac', '1', '-ar', '24000', out], check=True)
    os.unlink(mp3)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('narration'); ap.add_argument('out')
    ap.add_argument('--backend', choices=['gemini', 'edge'], default='gemini')
    ap.add_argument('--voice', help='Gemini: Charon / Puck / Kore ...; edge: zh-CN-YunxiNeural ...')
    ap.add_argument('--model', default='gemini-3.8-flash-tts')
    ap.add_argument('--speed', type=float, default=1.25, help='atempo factor applied after synthesis (default 1.25)')
    a = ap.parse_args()
    paras = [l.strip() for l in open(a.narration, encoding='utf-8') if l.strip()]
    text = '\n\n'.join(paras)
    raw = a.out + '.raw.wav'
    if a.backend == 'gemini':
        gemini(text, raw, a.voice or 'Charon', a.model)
    else:
        edge(text, raw, a.voice or 'zh-CN-YunxiNeural')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', f'atempo={a.speed}', a.out], check=True)
    os.unlink(raw)
    with wave.open(a.out) as w:
        print(f'{a.out}: {w.getnframes() / w.getframerate():.1f}s at {a.speed}x')


if __name__ == '__main__':
    main()
