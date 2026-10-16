---
name: anatomy-video
description: >-
  Make videos with code, and explain ideas with machines. Three outputs in one skill:
  (1) code-rendered videos — Canvas / HTML-CSS-SVG / WebGL / Three.js / Remotion / HyperFrames / Manim pages that draw frame t,
  rendered frame by frame with Playwright + FFmpeg, with three plans and previews before building, code-synthesized sound,
  and a voiceover pipeline that turns a written script into a narrated vertical short (TTS sped up to 1.25x, word-level alignment,
  hard subtitles, cover-first opening, fact-check gate, parallel rendering, cover image and publish copy);
  (2) Anatomy figures — crafted, highly detailed, interactive isometric SVG figures that explain a technical idea as a real
  physical object (lock, gauge, plotter, engine), with optional WebGL shaders and a 3D mode;
  (3) machine-explainer videos — an Anatomy machine driven by a virtual clock and narration cues, wrapped into a narrated video.
  Use whenever someone wants to make, animate or render a video, motion graphic, explainer, promo, kinetic typography, pixel-art
  or UI motion piece, turn an article or script into a video, or wants an isometric illustration, explanatory figure, interactive
  explainer or technical drawing of how something works — including Chinese requests like「做个视频」「用代码做视频」「做个动效」
  「把这篇文章做成视频」「文字稿转视频」「口播稿做成视频」「画个原理图」「做个等距插图」「用机器讲清楚这个概念」.
  Not for generating footage with video models, editing in Premiere/CapCut/AE, or subtitling an existing video.
---

# anatomy-video：用代码做视频，用机器讲概念

这个 skill 合并了两个开源项目：用代码逐帧渲染视频的 [xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video)（含本仓库加的配音流水线），和用等距机器解释概念的 [Anatomy](https://github.com/wheresryan22/anatomy)（原样收在 `anatomy/`），再用一层桥接（`bridge/`）把 Anatomy 的机器变成可以逐帧渲染的视频画面。

## 先分流：要做哪一种

| 用户要的 | 走哪条路 | 从哪读起 |
|---|---|---|
| 一条视频（宣传片、动效、知识讲解、文字稿转视频） | 下面的视频流程（第 0–6 步） | 本文件 |
| 一张插图 / 交互图 / 原理图（给文档、博客、落地页用），不是视频 | Anatomy 的流程，产出 HTML、SVG 或 React 组件 | `anatomy/SKILL.md`，kit 在 `anatomy/kit/` |
| 一条讲原理的视频，概念能对应到一台会动的机器 | 先按 Anatomy 造机器，再按视频流程配音、包装、渲染 | `references/anatomy-video.md` |

拿不准时：讲「东西怎么运作」的，优先考虑机器；讲观点、清单、价格的，用讲解模板（`templates/vertical-explainer/`）。两者可以混在一条视频里。

## 视频流程

Opus 自己不输出视频。这个 skill 让它写一个会自己动的网页（或 Manim 场景），网页暴露 `render(t)`，由脚本一帧一帧截图，再用 FFmpeg 合成 MP4。声音也用代码合成或接语音模型。

一句话提示词做视频是在抽卡：出来什么样、为什么这样、下次能不能再做出来，都不可控。这个 skill 的做法是**先把规划摆到用户面前，确认了再动手**：三个方案（每个都写清封面和开头黄金几秒）→ 每个方案一张关键帧或几秒预览 → 用户确认 → 写成 `brief.md` → 从封面和开头做起，按 brief 逐镜头制作、逐镜头自检 → 交付成片、封面图和发布文案。

## 工作目录

在当前目录下建 `opus-video/<slug>/`，所有东西放在里面：

```
opus-video/<slug>/
  source/        用户给的原材料、参考视频抽帧、分析笔记
  previews/      三个方案的预览（plan-a.png / plan-b.mp4 ...）
  brief.md       用户确认后的完整方案，也是可以复用的提示词
  index.html     成片的画面代码（或 Remotion / HyperFrames / Manim 工程）
  audio/         合成的配乐、音效、配音
  qa/            自检用的静帧和抽帧图
  out/<主题名>.mp4       成片（文件名取自 publish.txt 的标题，见「交付」）
  out/<主题名>-封面.png  封面图（第 0 帧的构图，贴纸贴好、不带字幕）
  out/publish.txt  发布用的标题、简介、tags
```

有配音的片子另外有 `audio/narration.txt`、`audio/scenes.json`、`timeline.js`，见 [references/voiceover-pipeline.md](references/voiceover-pipeline.md)。竖版讲解可以直接从 `templates/vertical-explainer/` 起步；机器讲概念的片子另有 Anatomy 的构建脚本、`figure-light.html` 和 `video.json`，见 [references/anatomy-video.md](references/anatomy-video.md)。

## 第 0 步：检查环境

运行一次 `python3 scripts/check_env.py`（路径相对本 skill 目录）。它会检查 python3、ffmpeg、Playwright 以及可用的浏览器，缺什么会告诉你怎么装。缺依赖时先告诉用户要装什么，得到同意再装。

## 第 1 步：问清楚要做什么

先问用户想做什么，接受三种原材料，给了哪种就用哪种，可以混着给：

- **想法**：一句话主题也行，越具体越好
- **原内容**：文章、口播稿、产品网址、产品代码库、数据表
- **参考视频**：本地文件或链接

用户给了现成的音乐时，先运行 `python3 scripts/audio_tools.py beats <音乐文件> > source/beats.json` 测出节拍、重拍和鼓点，方案和分镜都按这张节拍表来排。

只追问会改变方案的信息，一次最多问 3 个：时长、画幅（16:9 / 9:16 / 1:1）、要不要配音、有没有指定的品牌色或字体。用户没说的用合理默认值（30 秒、1920×1080、30fps、代码合成配乐、不配音；有配音时默认 1.25 倍速，见 craft-rules.md 声音一节），在方案里写明，让用户改。开头第一句默认写成一句暴论（前 5 秒内说完，见 opening-and-cover.md）。

处理原材料：

- **原内容**：提炼出核心信息、受众和必须出现的事实。事实只能来自原材料，不确定的就不写，不要替用户编功能、数字、年份。
- **事实核查**：稿子里有价格、额度、数据、产品功能、截止日期、对第三方的描述，或者「最新 / 现在」这类会过期的说法时，按 [references/fact-check.md](references/fact-check.md) 先调研、建核对表（`scripts/factcheck.py extract`），按核查结果改稿，再把稿子和核对表一起交给用户确认。
- **参考视频**：链接需要下载时，先告诉用户文件来源并征得同意再下载。然后运行 `python3 scripts/analyze_video.py <视频> --out source/ref`（`--out` 是文件名前缀，会生成 `source/ref-sheet.png`、`source/ref-info.txt`），它会输出时长、分辨率、帧率、镜头切换时间点和一张抽帧拼图。看拼图，写下参考视频的镜头结构、节奏、配色、字体和用到的代码类型（对照 [references/code-stack.md](references/code-stack.md)）。参考视频只学结构和手法，不照搬别人的素材和文案。

## 第 2 步：给三个方案

读 [references/code-stack.md](references/code-stack.md) 选技术组合，按 [references/plan-format.md](references/plan-format.md) 的格式写三个方案。

三个方案要有明显差别，差别在风格、叙事结构或技术组合上，不能只是换个配色。讲原理、讲机制的内容，至少有一个方案是「机器讲概念」：说清楚用哪台机器、它的哪个动作对应概念的哪一步（见 references/anatomy-video.md）。常见的拉开方式：一个稳妥（最贴近原材料和参考），一个风格化（换一种画面语言），一个结构上大胆（换一种讲法，比如用一个贯穿全片的主角或者一个不切镜头的长镜头）。

每个方案都要写画面概括（逐镜头的一两句话）、技术组合、声音、预计渲染耗时和风险，以及**封面帧和开头前 15 秒**（第 0 帧长什么样、开头旁白怎么说、画面怎么跟着动）。封面和开头按 [references/opening-and-cover.md](references/opening-and-cover.md) 写：第一帧就是封面，开头先给话题和反差、不给答案。原材料里找不到能当钩子的数字、反差、金句、背书或痛点时，先告诉用户补素材。

## 第 3 步：给每个方案做预览

预览是为了让用户在花大量时间渲染之前，先看到画面长什么样。预览页面也是 `render(t)` 页面，动手前先读 [references/craft-rules.md](references/craft-rules.md) 的页面骨架和字体两节，后面正式制作时可以直接在预览代码上接着做。

每个方案的预览页只搭一个镜头，时间用这个镜头自己的时间（从 0 开始），不用搭整条时间轴。

- 默认每个方案做 **一张关键帧**，优先做**封面帧**（第 0 帧），它最能代表风格，也就是成片的封面；封面帧不足以体现风格时，再加一张最有代表性的镜头。用 `python3 scripts/render.py previews/plan-a.html previews/plan-a.png --still 2.0 --size 1920x1080`。
- 方案的卖点在运动本身时（界面变形、节拍卡点、转场），改做 **2–4 秒的小样**：`python3 scripts/render.py previews/plan-b.html previews/plan-b.mp4 --size <方案画幅> --fps 30 --duration 3`。
- 预览做出来后自己先看一遍图，明显的问题（字溢出、元素挤在一起、画面太空）先修，再给用户。
- 方案里的「预计渲染耗时」用预览来估：渲染脚本会打印用时，单帧耗时 × 总帧数 × 子帧数，再乘 1.3 左右留余量。

把三个方案和预览路径一起给用户，请他选一个，或者说要怎么混合、修改。用户要改就回到第 2 或第 3 步，直到确认。

## 第 4 步：写 brief.md

用户确认后，按 [references/brief-template.md](references/brief-template.md) 写 `brief.md`。它就是这支视频完整的结构化提示词，分 `<role>` `<inputs>` `<direction>` `<structure>` `<build>` `<gotchas>` `<start>` 七块，已经确认的内容全部填实。

这份文件有两个用处：接下来的制作严格按它来；用户以后想复用、换主题、或者拿到别的工具里跑，直接用这份。写完告诉用户文件位置。

## 第 5 步：制作

制作规则在 [references/craft-rules.md](references/craft-rules.md)，动手前把整份读完。最要紧的几条：

1. **画面只由时间决定**。`window.render(t)` 画出第 t 秒；不用 `requestAnimationFrame`、`setTimeout`、CSS transition，随机数带固定种子，帧和帧之间不保存状态。这样任何一帧都能单独重渲，改一个镜头不会影响别的镜头。
2. **从封面和开头做起**。第一个做的就是第 0 帧封面和开头约 15 秒，按 opening-and-cover.md 的自检清单过一遍，通过了再往下做。
3. **一个镜头一个镜头做**。每做完一个镜头，用 `render.py --still` 渲 3 张静帧，自己看：文字有没有溢出、元素有没有重叠、主体够不够大、字停留够不够久。修好再做下一个。30 秒以上的片子，所有镜头搭完后先渲一版 960×540、不加运动模糊的低清小样，节奏和转场对了再精修，精修前别花时间在细节上。
4. **声音和画面用同一张时间表**。先定节拍网格或旁白时间轴，镜头切换和关键动作落在上面；音效放在画面动作发生的那一帧。配音整段合成，不要一句一句拼。
5. **有配音就少放字**。旁白讲句子，画面只放关键词和图形：每屏一个短标题加最多一行注释，词在念到时已经在屏上，一段旁白念完这格就不再出新字。不要逐字打出整句旁白，细则见 craft-rules.md 的「有配音时的画面文字」。
6. **有配音就按流水线走**。旁白整段合成、加速，用逐字时间戳生成场景切换点、动作点和字幕，命令和坑都在 [references/voiceover-pipeline.md](references/voiceover-pipeline.md)。
7. **镜头要动**。推、拉、跟随，让主体在画面里足够大；brief 没写镜头的时候，Opus 默认会固定机位，画面容易显得空。

用户点名框架时按框架来（Remotion / HyperFrames / Manim），没点名默认单个 HTML 文件，具体选择见 code-stack.md。

## 第 6 步：渲染和验收

- 渲染：`python3 scripts/render_parallel.py index.html out/<主题名>.mp4 --size 1920x1080 --fps 30 --duration 30 --audio audio/mix.wav`，把时间轴切成几段多进程同时渲，再无损拼接，比 `render.py` 快约 2.8 倍，帧数完全一致；要运动模糊加 `--subframes 4`（渲染时间也会变成 4 倍，先告诉用户）。只渲一小段检查时用 `render.py --start / --duration`。
- 有核对表的片子，渲正式版之前先过闸：`python3 scripts/factcheck.py gate source/factcheck.md --narration audio/narration.txt --page index.html`，退出码不是 0 就先改。
- 声音：音效用 `python3 scripts/audio_tools.py sfx timeline.json audio/sfx.wav` 按时间点合成，混好后 `audio_tools.py normalize` 到 -14 LUFS，再用 `audio_tools.py check audio/mix.wav --out qa/audio` 看响度和波形图。
- 每个场景搭完后，用 `python3 scripts/qa_stills.py index.html audio/timeline.json qa/scenes.png` 出「第 0 帧 + 每个场景最满状态」的拼图，先看这张再渲整片。
- 验收：`python3 scripts/analyze_video.py out/<主题名>.mp4 --out qa/final` 出抽帧图，再加一张手机尺寸的（`--cell-width 360`）。按 craft-rules.md 的「自检打分」给自己打分（「开场」一项按 opening-and-cover.md 的自检清单打），列出最严重的 3 个问题和时间点，改完只重渲那几秒，重复到每项 8 分以上，再对照验收清单核对。把每一轮的分数和问题记在 `qa/review_log.md` 里，交付时一起给用户。
- 有问题就回到对应镜头修，只重渲那一段也可以（`--start` / `--duration`），最后再整片合成。

## 交付

成片和封面图按主题命名，不同主题的视频文件名不能重复，**不要叫 `final.mp4`**：

1. 渲正式版之前先写好 `out/publish.txt`（格式见下）。
2. 用它的标题生成文件名：`NAME=$(python3 scripts/topic_name.py out/publish.txt)`，去掉空格、标点换成「-」，比如「AI 提问模板：说清四件事，一次写对」→ `AI提问模板-说清四件事-一次写对`。
3. 成片 `out/$NAME.mp4`，封面图 `out/$NAME-封面.png`（导出方法见 opening-and-cover.md，视频第一帧就是这张封面）。
4. 同一系列的几集，标题本身就要不一样（写上各自的主题），文件名才不会撞；同一主题的旧版要留着时，加后缀（`-无配音版`、`-横版`）。

`publish.txt` 方便直接复制到发布页。

格式只有三段，段与段之间空一行，不写「【标题】」这类标签，不写分隔符，不写封面字、用法说明：

```
标题（20 字以内，空格不算；覆盖用户会搜的词）

简介（一段，内容只来自原材料）

#tag1 #tag2 #tag3 #tag4 #tag5
```

tags 只给 5 个（抖音最多 5 个），挑搜索量最大、和内容最贴的。备选标题、其他平台的 tags 需要时直接在回复里给，不写进这个文件。

告诉用户：成片路径、`brief.md` 路径、工程目录，以及一段简短说明，包括这次的关键创作决定、已知的不足（比如某个镜头可以更好）、渲染用时。事实类内容里有不确定的地方，单独列出来让用户核对；带截止日期的活动、会过期的价格，单列成「发布前要再核的」。

## 遇到这些情况

- **用户想要真人或写实角色**：代码画不出来。可以建议用户先用视频模型生成**纯绿幕背景**的人物片段，交给本 skill 抠像，再用代码搭场景、大字和动效，做法见 code-stack.md 的「视频模型角色 + 代码场景」。
- **渲染太慢**：先降分辨率或帧率出小样，确认后再出正式版；运动模糊和 WebGL 后期是最耗时的两项。
- **浏览器里 WebGL 不可用**：`check_env.py` 会提示；先渲一帧确认着色器真的生效了，再渲整片。
- **用户只想要提示词**：跳过第 5、6 步，把 `brief.md` 交给用户即可。
