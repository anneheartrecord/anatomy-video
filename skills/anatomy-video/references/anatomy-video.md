# 机器讲概念：把 Anatomy 机器做成视频

讲原理、讲机制的视频（缓存为什么快、限流怎么工作、发动机怎么点火），最好的画面是一台**会动的真机器**：它的工作方式本身就是那个概念。Anatomy（`anatomy/`）负责造这台机器，这一节负责把它变成带配音、字幕、封面的竖版视频。

## 什么时候用

- 概念能对应到一个物理机构：锁、量具、绘图仪、阀门、发动机、抽屉柜……
- 观众需要看到「东西怎么动」，光靠关键词和卡片讲不清。
- 不适合：纯观点、纯清单、价格对比这类内容，继续用 `templates/vertical-explainer/`。

两种可以混用：一条视频大部分是讲解模板，中间一两段换成机器镜头，分开渲染后用 ffmpeg 拼接。

## 流程

```bash
# 0. 稿子、事实核查（fact-check.md），和别的配音视频一样
# 1. 造机器：读 anatomy/SKILL.md，按它的流程做（真实数字 → 发明物体 → 零件清单 → 几何 → 审计）
#    视频用浅色主题：node build.mjs --light，拿到 figure-light.html
#    先找最接近的 anatomy/examples/ 改，比从零做快得多
# 2. 配音和时间轴（voiceover-pipeline.md 第 2–4 步）：tts.py → align.py → scenes.json → timeline.py
# 3. 写 video.json（封面、各场景标题、动作），包装成视频页
python3 $S/bridge/wrap_figure.py figure-light.html video.json index.html
# 4. 自检拼图、混音、事实闸门、并行渲染、封面图，和别的配音视频一样
python3 $S/scripts/qa_stills.py index.html audio/timeline.json qa/scenes.png
python3 $S/scripts/voice/mix.py
NAME=$(python3 $S/scripts/topic_name.py out/publish.txt)
python3 $S/scripts/render_parallel.py index.html "out/$NAME.mp4" --size 1080x1920 --fps 30 --duration <total> --audio audio/mix.wav
python3 $S/scripts/render.py "index.html?cover=1" "out/$NAME-封面.png" --still <封面动作结束后> --size 1080x1920
```

## 造机器时为视频多想三件事

1. **动作要能被触发**。Anatomy 的机器靠指针、键盘和按钮驱动，视频里这些都由 `video.json` 的动作模拟。设计时就想好：念到哪句话，机器该做什么（拆开、点火、换挡、滑到某一格），对应哪种输入。
2. **需要精确控制时，暴露一个状态函数**。在 live 脚本里加 `window.figure = { set(state) {...} }`，视频里用 `{"do": "eval", "js": "figure.set('apart')"}` 调用，比模拟指针坐标稳。
3. **自带的循环演示就是空闲画面**。没人碰时机器会自己演示；一旦有输入，演示停下，空闲 3.6 秒后再恢复（这是虚拟时间，会被正确重放）。旁白没讲到机器的段落，可以让它自己转。

## video.json

```json
{
  "size": [1080, 1920],
  "pill": "机器讲概念 · 第 1 课",
  "cover": {"l1": "猛禽发动机", "l2": "拆开看看", "pulse": "cover.apart"},
  "chips": ["燃烧", "拆解", "点火"],
  "titles": {
    "apart": {"tag": "拆解", "title": "11 个组件", "sub": "悬停就拆开"},
    "fire": {"title": "点火"}
  },
  "figure": {"top": 660, "width": 990, "height": 720},
  "actions": [
    {"at": "apart", "do": "hover", "x": 0.5, "y": 0.45},
    {"at": "apart.chamber", "do": "glide", "from": [0.5, 0.45], "to": [0.55, 0.6], "dur": 1.2},
    {"at": "fire", "do": "leave"},
    {"at": "fire.ignite", "do": "eval", "js": "document.querySelector('[data-fire]').click()"},
    {"at": 12.0, "do": "key", "key": "ArrowRight"}
  ]
}
```

- `cover`：第 0 帧的两行大字（第二行红底白字），`pulse` 是让标题跳一下的动作点；第一个场景就是封面（见 opening-and-cover.md）。
- `titles`：每个场景顶部的小标签、大标题、一行注释，按 `scenes.json` 里的场景名。
- `figure`：卡片在画面里的位置（px），会等比缩放放进 `width × height` 的框里；`target` 改坐标参照元素（默认 `.iso-stage` 或 `.<前缀>-stage`），`root` 改要缩放的元素（默认 `.iso-page`）；卡片下方的英文图例和说明默认隐藏，`"caption": true` 保留。
- `actions`：`at` 是秒数、场景名或 `场景.动作点`，`after` 再往后推几秒；`x / y` 是舞台框里的比例坐标。
  - `hover`：指针移到某点。
  - `glide`：指针在 `dur` 秒内从 `from` 平滑移到 `to`。
  - `leave`：指针离开机器。
  - `click`：在某点按下、抬起、点击。
  - `key`：按一个键，发给舞台元素。
  - `eval`：在页面里执行一段 JS。

## 虚拟时钟（bridge/clock.js）

Anatomy 的动画是「时间驱动的平滑运动」：指数跟随和弹簧，每一帧依赖上一帧。代码视频要求任意一帧都能单独算出来，所以 `clock.js` 接管页面的 `requestAnimationFrame`、`performance.now`、`Date.now`、`setTimeout / setInterval`，让时间停在 0；`render(t)` 时以 1/60 秒的固定步长从当前时刻推进到 t，按顺序跑定时器、动作和动画帧。

- 同一个 t 永远得到同一帧（实测：百分表和带 WebGL 尾焰的猛禽发动机，同一时刻渲两次逐像素相同；顺序渲染和并行渲染逐帧一致）。
- 时间只能往前走。`render.py` 的单帧、整片、只渲一段，以及 `render_parallel.py` 的每一段，都从一个新页面开始往前推，满足这个条件。
- `IntersectionObserver` 一律报告「在视口内」，`prefers-reduced-motion` 一律为否，否则机器会因为不在屏幕上或减少动效而停住。
- `Date.now()` 固定从 2026-01-01 起算，页面上不会出现随渲染时间变化的文字。
- 页面不能依赖真实网络和真实时间（加载远程资源、读系统时钟）。

## 踩过的坑

| 现象 | 原因 | 处理 |
|---|---|---|
| 指针离开后机器不复位 | `pointerleave` 不冒泡，只发给命中元素，舞台收不到 | `overlay.js` 沿祖先链逐个发 enter / leave，和浏览器一致 |
| 悬停打到了按钮上 | 页面第一个 `svg` 是按钮图标，不是机器 | 坐标参照默认取舞台元素（`.iso-stage`、`.rp-stage` 这类） |
| 卡片偏左、被裁 | 缩放原点是元素左上角，平移量不该再乘缩放 | 已修 |
| 封面横幅压住卡片 | 卡片默认位置太高 | 默认 `top` 660，横幅在 620 以上 |
| 输入之后机器不再自己动 | 它的演示被打断，空闲 3.6 秒才恢复 | 需要它继续动，就在旁白里留出空闲时间，或用 `eval` 直接设状态 |
| 每帧要渲 0.1 秒以上 | WebGL 和大量零件 | 用 `render_parallel.py`；预览先降到 540×960 |
