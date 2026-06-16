# ⚽ World Cup 2026 README Widget / 世界杯 2026 动态看板

> 自动更新的 FIFA 2026 世界杯面板，每小时通过 GitHub Actions 刷新。
> Self-updating FIFA World Cup 2026 panels — auto-refreshed every hour via GitHub Actions.

基于 / Powered by [moose25/world-cup-2026-readme-widget](https://github.com/moose25/world-cup-2026-readme-widget)

---

## 📊 比赛面板 / Match Panels

| 面板 Panel | 中文 | English |
|---|---|---|
| 🕐 Countdown | 距开幕倒计时 | Days to kickoff |
| ⚽ Match | 正在进行的比赛 / 下一场 | Live or next match |
| 📅 Today | 今日全部赛程（北京时间）| Today's fixtures (Asia/Shanghai) |
| 🏆 R32 | 48 队晋级 32 强追踪 | Round-of-32 qualification tracker |
| 📋 Record | 模型战绩（比分 vs 预测）| Model scorecard (results vs predictions) |

<!-- WC26:START -->
<img src=".github/wc26/countdown.svg" alt="World Cup 2026 — countdown" />
<img src=".github/wc26/match.svg" alt="World Cup 2026 — match" />
<img src=".github/wc26/today.svg" alt="World Cup 2026 — today" />
<img src=".github/wc26/r32.svg" alt="World Cup 2026 — r32" />
<img src=".github/wc26/record.svg" alt="World Cup 2026 — model scorecard" />
<!-- WC26:END -->

---

## 🧠 AI 预测面板 / AI Prediction Panels

> 数据来源：**cup26matches.com** — Elo 评级 + Dixon-Coles 双变量泊松 + 50,000 次蒙特卡洛模拟
> Data: cup26matches.com (CC BY 4.0) — Elo + Dixon-Coles bivariate Poisson + 50k Monte Carlo

| 面板 Panel | 中文 | English |
|---|---|---|
| 🏆 Championship | 夺冠概率 TOP 10 | Championship odds top 10 |
| 🛤️ Path to Final | 通往决赛之路晋级概率 | Stage-by-stage advancement % |
| ⚽ Next Match | 接下来6场胜平负预测 | Next 6 matches W/D/L % |
| 📊 Qualification | 小组赛出线概率 | Group qualification odds |

<!-- WC26-PREDICTIONS:START -->
<img src=".github/wc26/championship.svg" alt="World Cup 2026 — AI championship odds" />

<img src=".github/wc26/path-to-final.svg" alt="World Cup 2026 — path to final" />

<img src=".github/wc26/next-match.svg" alt="World Cup 2026 — next match prediction" />

<img src=".github/wc26/upcoming.svg" alt="World Cup 2026 — group qualification" />
<!-- WC26-PREDICTIONS:END -->

---

## 🧠 预测模型 / Prediction Model

| 组件 | 说明 |
|------|------|
| **Elo 评级** | 48 队基于 913 场国际赛校准的动态评分 |
| **Dixon-Coles 泊松** | 双变量泊松模型 + ρ=-0.13 修正低比分平局 |
| **蒙特卡洛** | 50,000 次锦标赛模拟，锁定已完赛结果 |
| **回测验证** | Walk-forward RPS=0.175, ECE=2.3%, 准确率 62% |

---

## 🔧 工作原理 / How It Works

- **赛程数据 / Fixtures**: [openfootball/worldcup.json](https://github.com/openfootball/worldcup.json)
- **预测数据 / Predictions**: [cup26matches.com/data/probabilities.json](https://cup26matches.com/data/probabilities.json)
- **渲染 / Render**: SVG 图片直接嵌入 Markdown
- **更新 / Update**: GitHub Actions 每小时自动运行
- **时区 / Timezone**: `Asia/Shanghai`（北京时间 UTC+8）
