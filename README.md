# ⚽ World Cup 2026 README Widget / 世界杯 2026 动态看板

> 自动更新的 FIFA 2026 世界杯面板，每 6 小时通过 GitHub Actions 刷新。
> Self-updating FIFA World Cup 2026 panels — auto-refreshed every 6 hours via GitHub Actions.

基于 / Powered by [moose25/world-cup-2026-readme-widget](https://github.com/moose25/world-cup-2026-readme-widget)

---

## 📊 面板 / Panels

| 面板 Panel | 中文 | English |
|---|---|---|
| 🕐 Countdown | 距开幕倒计时 | Days to kickoff |
| ⚽ Match | 正在进行的比赛 / 下一场 | Live or next match |
| 📅 Today | 今日全部赛程（北京时间）| Today's fixtures (Asia/Shanghai) |
| 🏆 R32 | 48 队晋级 32 强追踪 | Round-of-32 qualification tracker |
| 🌲 Bracket | 淘汰赛对阵树 | Knockout bracket |

<!-- WC26:START -->
<img src=".github/wc26/countdown.svg" alt="World Cup 2026 — countdown" />
<img src=".github/wc26/match.svg" alt="World Cup 2026 — match" />
<img src=".github/wc26/today.svg" alt="World Cup 2026 — today" />
<img src=".github/wc26/r32.svg" alt="World Cup 2026 — r32" />
<img src=".github/wc26/bracket.svg" alt="World Cup 2026 — bracket" />
<!-- WC26:END -->

---

## 🔧 工作原理 / How It Works

- **数据源 / Data**: [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json)（公共领域，无需 API Key）
- **渲染 / Render**: 每个面板是一个 SVG 图片，直接嵌入 Markdown
- **更新 / Update**: GitHub Actions 定时运行 → 拉取最新数据 → 生成 SVG → 自动提交
- **时区 / Timezone**: `Asia/Shanghai`（北京时间 UTC+8）
