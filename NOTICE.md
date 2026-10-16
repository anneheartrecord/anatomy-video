# Notice / 来源说明

This repository combines two MIT-licensed projects and adds a bridge between them.
本仓库合并了两个 MIT 协议的开源项目，并在两者之间加了一层桥接。

| Path / 路径 | Source / 来源 | Version / 版本 | Changes / 改动 |
|---|---|---|---|
| `skills/anatomy-video/anatomy/` | [wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) by Ryan, MIT | commit `e948829` | none, vendored as-is (`git archive`); its own LICENSE is kept in the folder / 原样收录，未修改 |
| `skills/anatomy-video/` (except `anatomy/` and `bridge/`) | [Kianzzz/xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video) by 周行, MIT, through the fork [anneheartrecord/xilo-opus-video](https://github.com/anneheartrecord/xilo-opus-video) | fork commit `1676d97` | the fork's additions (voiceover pipeline, templates, fact-check, parallel render, naming); here the skill is renamed `anatomy-video` and its SKILL.md gains the routing section / 加了分流说明 |
| `skills/anatomy-video/bridge/`, `examples/` | new in this repository / 本仓库新增 | | virtual clock, video overlay, page wrapper, example |

To update Anatomy, replace `skills/anatomy-video/anatomy/` with a newer `git archive` of the upstream repository and update the commit above.
更新 Anatomy：用上游新版本的 `git archive` 替换 `skills/anatomy-video/anatomy/`，并更新上表的 commit。
