# 有配音的片子：流水线

有旁白的视频（知识讲解、口播稿转视频）按这条线做。核心思路：**旁白整段合成，用逐字时间戳让画面去对旁白**，场景切换、画面动作、字幕全部用稿子里的原话定位。

模板在 `templates/vertical-explainer/`（竖版 1080×1920，第 0 帧是封面、场景淡入淡出、底部一行硬字幕），把整个目录拷到 `opus-video/<slug>/` 再改。

## 命令顺序

下面 `$S` 是本 skill 的目录，命令都在项目目录里跑。

```bash
# 1. 旁白：audio/narration.txt，一段一行，纯文本；有事实就先建核对表（见 fact-check.md）
python3 $S/scripts/factcheck.py extract audio/narration.txt source/factcheck.md
# 2. 合成并加速（默认 1.25 倍）；没有 GEMINI_API_KEY 就用 --backend edge（免费）
python3 $S/scripts/voice/tts.py audio/narration.txt audio/voice.wav
# 3. 逐词时间戳（Apple Silicon 用 mlx-whisper，其他机器换成 faster-whisper）
uv run --with mlx-whisper python $S/scripts/voice/align.py audio/voice.wav audio/voice_segments.json
# 4. 写 audio/scenes.json，生成时间轴和字幕
python3 $S/scripts/voice/timeline.py
# 5. 改 index.html 的 HEAD / BODY，出每个场景最满状态的拼图检查
python3 $S/scripts/qa_stills.py index.html audio/timeline.json qa/scenes.png
# 6. 配乐 + 音效 + 旁白混音（-14 LUFS，峰值留够 AAC 编码的余量）
python3 $S/scripts/voice/mix.py
# 7. 先写好 out/publish.txt（标题 / 简介 / 5 个 tag），用标题生成文件名，再过事实闸门、并行渲染、导出封面图
NAME=$(python3 $S/scripts/topic_name.py out/publish.txt)
python3 $S/scripts/factcheck.py gate source/factcheck.md --narration audio/narration.txt --page index.html
python3 $S/scripts/render_parallel.py index.html "out/$NAME.mp4" --size 1080x1920 --fps 30 --duration <timeline.json 的 total> --audio audio/mix.wav
python3 $S/scripts/render.py "index.html?cover=1" "out/$NAME-封面.png" --still <开头印章落下之后的秒数> --size 1080x1920
```

## scenes.json

```json
{
 "scenes": [
  ["cover", "开头第一句的前几个字", {"stamp": "暴论里的关键词"}],
  ["point1", "第一，", {"a": "旁白里的一个短语", "b": "后面的另一个短语"}]
 ],
 "kind": {"cover.stamp": "stamp", "point1.b": "coin"},
 "offs": {"cover.stamp": 0.3}
}
```

- 每个场景：名字、起点原话、场景内动作点。原话必须是 `narration.txt` 里一字不差的片段，按顺序查找。
- 页面里 `BODY[名字](t, c)` 拿到的 `c` 就是这些动作点的时间（秒），`c._start` 是场景起点。念到哪个词，就在 `c.那个词` 的时刻让对应元素出现。
- `kind` 决定这个动作点配什么音效：`pop`（默认）、`stamp`、`coin`、`print`、`tick`、`pencil`。
- 一个场景的第一个动作点离场景起点超过 3 秒，就先放一个占位元素，不然画面会空着。

## 踩过的坑

| 现象 | 原因 | 处理 |
|---|---|---|
| 开头多出一段「用自然的语气朗读……」 | Gemini TTS 会把风格指令当正文读 | `tts.py` 只传正文，不加任何指令 |
| 场景切换点算错、时长为负 | whisper 会把好几段旁白合成一个分段，分段边界不可靠 | `timeline.py` 用逐字对齐，不用分段边界 |
| 字幕出现错别字（字节 → 自解） | whisper 同音识别错 | 识别结果只拿时间，字幕和定位都用稿子原文 |
| 音频末尾多出空段、重复段 | whisper 在静音处幻觉 | `align.py` 丢掉空文本和短于 0.3 秒的分段 |
| 第一段切片为空 | 起点算成 -0.05 秒 | 起点不小于 0（已处理） |
| 成片峰值超过 -1 dBTP | AAC 编码会把真峰值抬高约 0.8 dB | `mix.py` 标准化后再限幅到 0.8 |
| edge-tts 返回 403 | 版本旧，微软换了鉴权 | `uv tool upgrade edge-tts` |
| 批量删除临时文件时卡住 | shell 里 `rm` 被设成了交互确认 | 脚本里一律用 `rm -f` |

## 自检时多看三样

- 第 0 帧是不是完整封面（没有字幕、没有半截动画）。
- 每个场景最满的状态有没有文字溢出、元素重叠，`qa_stills.py` 的拼图一眼能看出来。
- 印章、贴纸这类开头动作，从落下到切走至少要留 1 秒，否则观众看不见。
