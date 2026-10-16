#!/usr/bin/env python3
"""Lo-fi bed + sound effects on the cue points + the whole narration -> audio/mix.wav (-14 LUFS, safe peaks).

  mix.py --dir <project>                    # needs audio/timeline.json, audio/scenes.json, audio/voice.wav
  mix.py --dir <project> --music 0          # narration and effects only

Music ducks under the voice. Each cue gets a sound: 'pop' by default, or the kind set in scenes.json
("kind": {"scene.cue": "stamp" | "coin" | "print" | "pop" | "tick" | "pencil"}). Every scene change gets a soft whoosh.
The result is loudness-normalized and limited low enough that AAC encoding in render.py stays under -1 dBTP,
so pass it straight to `render.py --audio audio/mix.wav`.
"""
import argparse, json, os, subprocess, wave
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--dir', default='.')
ap.add_argument('--music', type=float, default=.32, help='music level under the voice (0 = no music)')
ap.add_argument('--bpm', type=float, default=96)
args = ap.parse_args()
os.chdir(args.dir)
TL = json.load(open('audio/timeline.json'))
CFG = json.load(open('audio/scenes.json'))
SR, DUR, BPM = 48000, TL['total'], args.bpm
BEAT = 60 / BPM; BAR = 4 * BEAT
n = int(DUR * SR) + SR
rng = np.random.default_rng(7)
mt = lambda m: 440 * 2 ** ((m - 69) / 12)

def env(length, a=.005, d=1.0):
    x = np.arange(int(length * SR)) / SR
    return np.minimum(1, x / a) * np.exp(-x / d)

def add(buf, t, sig, gain=1.0):
    i = int(t * SR); j = min(len(buf), i + len(sig))
    if i < len(buf): buf[i:j] += sig[:j - i] * gain

def filt(sig, kind, f):
    return sosfilt(butter(2, f, kind, fs=SR, output='sos'), sig)

def keys(m, length=2.4):  # Rhodes-like: harmonics + detune + tremolo
    x = np.arange(int(length * SR)) / SR; f = mt(m)
    s = sum(a * (np.sin(2 * np.pi * f * h * x) + np.sin(2 * np.pi * f * h * 1.003 * x)) for h, a in [(1, 1), (2, .35), (3, .12), (4, .05)])
    return s * env(length, .008, 1.1) * (1 + .15 * np.sin(2 * np.pi * 5 * x))

def bell(m, length=1.2):
    x = np.arange(int(length * SR)) / SR; f = mt(m)
    return (np.sin(2 * np.pi * f * x) + .3 * np.sin(2 * np.pi * f * 2.01 * x)) * env(length, .003, .35)

def kick():
    L = .35; x = np.arange(int(L * SR)) / SR; f = np.geomspace(120, 42, len(x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(L, .001, .12)

def snare():
    L = .25; return filt(rng.standard_normal(int(L * SR)), 'bandpass', [900, 5000]) * env(L, .001, .06) + np.sin(2 * np.pi * 185 * np.arange(int(L * SR)) / SR) * env(L, .001, .04) * .5

def hat():
    L = .06; return filt(rng.standard_normal(int(L * SR)), 'highpass', 7000) * env(L, .0005, .015)

def bass(m, L):
    x = np.arange(int(L * SR)) / SR; f = mt(m)
    return (np.sin(2 * np.pi * f * x) + .25 * np.sin(4 * np.pi * f * x)) * env(L, .01, .5)

# Fmaj7 Em7 Dm7 Cmaj7, one chord per bar
CHORDS = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
ROOTS = [41, 40, 38, 36]
PENTA = [72, 74, 76, 79, 81, 84]

music, drums = np.zeros(n), np.zeros(n)
bars = int(DUR / BAR)
for b in range(bars):
    t0, c = b * BAR, b % 4
    last = b == bars - 1
    for k, m in enumerate(CHORDS[c]):
        add(music, t0 + k * .012, keys(m, 4.0 if last else 2.6), .16)
    if b >= 1 and not last:
        add(music, t0, bass(ROOTS[c], BEAT * 1.5), .5)
        add(music, t0 + BEAT * 2.5, bass(ROOTS[c] + 7, BEAT), .35)
        for beat in range(4):
            if beat in (0,) or (beat == 2 and b % 2): add(drums, t0 + beat * BEAT, kick(), .9)
            if beat == 2 and not b % 2: add(drums, t0 + (beat + .5) * BEAT, kick(), .6)
            if beat in (1, 3): add(drums, t0 + beat * BEAT, snare(), .35)
            for e in (0, 1):
                add(drums, t0 + (beat + e * .58) * BEAT, hat(), .12 if e else .18)
    if 6 <= b < bars - 4:  # a sparse melody in the middle
        for e in range(8):
            if rng.random() < .3: add(music, t0 + e * BEAT / 2, bell(PENTA[rng.integers(len(PENTA))]), .09)
    if last: add(music, t0, bass(ROOTS[c], 3.0), .45)

ir = rng.standard_normal(int(.9 * SR)) * np.exp(-np.arange(int(.9 * SR)) / SR / .25)
music = music + fftconvolve(music, ir)[:n] * .012
crackle = np.zeros(n); idx = rng.integers(0, n, 900); crackle[idx] = rng.uniform(-.3, .3, 900)
crackle += filt(rng.standard_normal(n), 'lowpass', 3000) * .004

def pencil(L=.5):
    s = filt(rng.standard_normal(int(L * SR)), 'bandpass', [2000, 7000])
    flutter = .55 + .45 * np.abs(np.sin(2 * np.pi * 23 * np.arange(len(s)) / SR + rng.random() * 6))
    return s * flutter * np.hanning(len(s))

def popfx():
    L = .18; x = np.arange(int(L * SR)) / SR; f = np.geomspace(500, 1300, len(x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(L, .001, .05)

def success():
    a = bell(84, .5); b = bell(88, 1.0); out = np.zeros(int(1.2 * SR)); out[:len(a)] += a; out[int(.1 * SR):int(.1 * SR) + len(b)] += b; return out

def whoosh():
    L = .5; return filt(rng.standard_normal(int(L * SR)), 'bandpass', [300, 2500]) * np.hanning(int(L * SR))

def thud():
    L = .5; x = np.arange(int(L * SR)) / SR; return np.sin(2 * np.pi * np.cumsum(np.geomspace(150, 40, len(x))) / SR) * env(L, .001, .15)

def tick():
    return filt(rng.standard_normal(int(.03 * SR)), 'highpass', 3000) * env(.03, .0005, .006)

def printer():  # receipt printer
    L = .22; x = filt(rng.standard_normal(int(L * SR)), 'bandpass', [1500, 6000])
    return x * (.6 + .4 * np.sign(np.sin(2 * np.pi * 60 * np.arange(len(x)) / SR))) * np.hanning(len(x))

sfx = np.zeros(n)
SOUND = {'stamp': (thud, .7), 'print': (printer, .25), 'pop': (popfx, .3), 'coin': (success, .25), 'tick': (tick, .4), 'pencil': (pencil, .22)}
KIND, OFFS = CFG.get('kind', {}), CFG.get('offs', {})
for sc in TL['scenes'][1:]:
    add(sfx, sc['start'], whoosh(), .3)
for sc in TL['scenes']:
    for k, t in sc['cues'].items():
        key = f"{sc['name']}.{k}"; fn, gain = SOUND[KIND.get(key, 'pop')]
        add(sfx, t + OFFS.get(key, 0), fn(), gain)

with wave.open('audio/voice.wav') as w:
    vr = w.getframerate(); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
v = np.interp(np.arange(int(len(v) * SR / vr)) / SR, np.arange(len(v)) / vr, v)
voice = np.zeros(n); add(voice, TL['offset'], v)
voice = voice / np.abs(voice).max() * .8
venv = np.convolve(np.abs(voice), np.ones(int(.25 * SR)) / int(.25 * SR), 'same')
duck = 1 - .55 * np.clip(venv / (venv.max() * .35), 0, 1)
mix = (music * .9 + drums * .55 + crackle * .5) * duck * args.music + sfx * .5 + voice
mix = mix[:int(DUR * SR)]
fade = int(1.2 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
mix /= np.abs(mix).max(); mix = np.tanh(mix * 2.0)          # soft clip the drum peaks
mix /= np.abs(mix).max() / .9
with wave.open('audio/mix_raw.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# loudness -14 LUFS, then limit: AAC encoding adds up to ~0.8 dB of true peak, so leave room for it
os.makedirs('qa', exist_ok=True)
tools = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio_tools.py')
subprocess.run(['python3', tools, 'normalize', 'audio/mix_raw.wav', 'audio/mix_norm.wav'], check=True, capture_output=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'audio/mix_norm.wav', '-af', 'volume=-0.8dB,alimiter=limit=0.8:level=false', 'audio/mix.wav'], check=True)
for f in ('audio/mix_raw.wav', 'audio/mix_norm.wav'):
    os.remove(f)
print(subprocess.run(['python3', tools, 'check', 'audio/mix.wav', '--out', 'qa/audio'], capture_output=True, text=True).stdout.splitlines()[0])
