# Example: a dial indicator, narrated

The smallest Anatomy figure (`anatomy/examples/dial-indicator`) turned into an 18-second vertical video: the carriage
slides when the narration says so, the probe drops onto each gauge block as it is named, then the figure goes back to
its own tour. Run from this folder (`$S` is the skill folder):

```bash
S=../..
mkdir -p qa out
cp $S/anatomy/examples/dial-indicator/dial-indicator-light.html figure.html
python3 $S/scripts/voice/tts.py audio/narration.txt audio/voice.wav --backend edge
uv run --with mlx-whisper python $S/scripts/voice/align.py audio/voice.wav audio/voice_segments.json
python3 $S/scripts/voice/timeline.py
python3 $S/bridge/wrap_figure.py figure.html video.json index.html
python3 $S/scripts/qa_stills.py index.html audio/timeline.json qa/scenes.png
python3 $S/scripts/voice/mix.py
python3 $S/scripts/render_parallel.py index.html out/百分表怎么读出高度.mp4 --size 1080x1920 --fps 30 \
  --duration $(python3 -c "import json;print(json.load(open('audio/timeline.json'))['total'])") --audio audio/mix.wav
```
