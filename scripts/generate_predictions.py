#!/usr/bin/env python3
"""
Fetch cup26matches.com prediction data and generate SVG panels.

Data source: https://cup26matches.com/data/probabilities.json (CC BY 4.0)
Output: .github/wc26/championship.svg, path-to-final.svg, next-match.svg, upcoming.svg

Runs in GitHub Actions (ubuntu-latest). No heavy deps — stdlib + requests.
"""

import json, os, sys, math, urllib.request
from datetime import datetime, timezone, timedelta

# ── Config ──────────────────────────────────────────────────────────
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", ".github", "wc26")
API_URL = "https://cup26matches.com/data/probabilities.json"
TZ = timezone(timedelta(hours=8))  # Asia/Shanghai

# Team name mapping: slug → (Chinese name, flag emoji)
TEAM_NAMES: dict[str, tuple[str, str]] = {
    "france": ("法国", "🇫🇷"), "spain": ("西班牙", "🇪🇸"), "england": ("英格兰", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "argentina": ("阿根廷", "🇦🇷"), "brazil": ("巴西", "🇧🇷"), "portugal": ("葡萄牙", "🇵🇹"),
    "germany": ("德国", "🇩🇪"), "netherlands": ("荷兰", "🇳🇱"), "belgium": ("比利时", "🇧🇪"),
    "colombia": ("哥伦比亚", "🇨🇴"), "morocco": ("摩洛哥", "🇲🇦"), "norway": ("挪威", "🇳🇴"),
    "usa": ("美国", "🇺🇸"), "mexico": ("墨西哥", "🇲🇽"), "croatia": ("克罗地亚", "🇭🇷"),
    "senegal": ("塞内加尔", "🇸🇳"), "uruguay": ("乌拉圭", "🇺🇾"), "japan": ("日本", "🇯🇵"),
    "ecuador": ("厄瓜多尔", "🇪🇨"), "switzerland": ("瑞士", "🇨🇭"), "australia": ("澳大利亚", "🇦🇺"),
    "canada": ("加拿大", "🇨🇦"), "south-korea": ("韩国", "🇰🇷"), "sweden": ("瑞典", "🇸🇪"),
    "iran": ("伊朗", "🇮🇷"), "ivory-coast": ("科特迪瓦", "🇨🇮"), "austria": ("奥地利", "🇦🇹"),
    "algeria": ("阿尔及利亚", "🇩🇿"), "turkey": ("土耳其", "🇹🇷"), "egypt": ("埃及", "🇪🇬"),
    "scotland": ("苏格兰", "🏴"), "czech-republic": ("捷克", "🇨🇿"),
    "ghana": ("加纳", "🇬🇭"), "saudi-arabia": ("沙特", "🇸🇦"), "paraguay": ("巴拉圭", "🇵🇾"),
    "uzbekistan": ("乌兹别克斯坦", "🇺🇿"), "dr-congo": ("刚果(金)", "🇨🇩"),
    "bosnia-and-herzegovina": ("波黑", "🇧🇦"), "south-africa": ("南非", "🇿🇦"),
    "panama": ("巴拿马", "🇵🇦"), "qatar": ("卡塔尔", "🇶🇦"), "tunisia": ("突尼斯", "🇹🇳"),
    "cape-verde": ("佛得角", "🇨🇻"), "curacao": ("库拉索", "🇨🇼"),
    "haiti": ("海地", "🇭🇹"), "iraq": ("伊拉克", "🇮🇶"), "jordan": ("约旦", "🇯🇴"),
    "new-zealand": ("新西兰", "🇳🇿"), "peru": ("秘鲁", "🇵🇪"), "chile": ("智利", "🇨🇱"),
    "venezuela": ("委内瑞拉", "🇻🇪"), "denmark": ("丹麦", "🇩🇰"), "italy": ("意大利", "🇮🇹"),
    "poland": ("波兰", "🇵🇱"), "serbia": ("塞尔维亚", "🇷🇸"), "wales": ("威尔士", "🏴"),
    "nigeria": ("尼日利亚", "🇳🇬"), "cameroon": ("喀麦隆", "🇨🇲"),
    "honduras": ("洪都拉斯", "🇭🇳"), "jamaica": ("牙买加", "🇯🇲"),
    "el-salvador": ("萨尔瓦多", "🇸🇻"), "trinidad-and-tobago": ("特立尼达和多巴哥", "🇹🇹"),
    "guatemala": ("危地马拉", "🇬🇹"),
}


def fetch_data():
    """Fetch probabilities.json from cup26matches.com."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, headers={"User-Agent": "world-cup-2026-widget/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ═══════════════════════════════════════════════════════════════
# SVG HELPERS
# ═══════════════════════════════════════════════════════════════

DARK_BG = "#0d1117"
CARD_BG = "#161b22"
BORDER = "#30363d"
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
ACCENT = "#58a6ff"
GOLD = "#d2991d"
GREEN = "#3fb950"
RED = "#f85149"
ORANGE = "#d2991d"
BAR_COLORS = ["#58a6ff", "#3fb950", "#d2991d", "#f78166", "#a371f7",
              "#79c0ff", "#56d364", "#e3b341", "#f0883e", "#bc8cff"]

SCALE = 1.5  # display scale factor


def svg_header(w, h):
    dw, dh = int(w * SCALE), int(h * SCALE)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{dw}" height="{dh}">'


def svg_rect(x, y, w, h, fill, rx=0):
    rx_attr = f' rx="{rx}"' if rx else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{rx_attr}/>'


def svg_text(x, y, text, fill=TEXT_PRIMARY, size=14, anchor="start", bold=False, font='monospace'):
    fw = ' font-weight="bold"' if bold else ''
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-family="{font}" text-anchor="{anchor}"{fw}>{text}</text>'


def pct_str(v):
    return f"{v * 100:.1f}%"


# ═══════════════════════════════════════════════════════════════
# DAY TRACKER
# ═══════════════════════════════════════════════════════════════

WC_START = datetime(2026, 6, 11, tzinfo=TZ)
WC_END = datetime(2026, 7, 19, tzinfo=TZ)
WC_TOTAL_DAYS = (WC_END - WC_START).days + 1


def generate_day_tracker():
    W, H = 600, 150
    now = datetime.now(TZ)
    day_num = (now.date() - WC_START.date()).days + 1
    day_num = max(1, min(day_num, WC_TOTAL_DAYS))
    pct = day_num / WC_TOTAL_DAYS

    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(10, 8, W - 20, H - 16, CARD_BG, 8))
    parts.append(svg_text(24, 36, "🗓️ 世界杯进行中 · World Cup 2026", ACCENT, 18, bold=True))
    parts.append(svg_text(24, 60, f"第 {day_num} 天 / 共 {WC_TOTAL_DAYS} 天  ·  Day {day_num} of {WC_TOTAL_DAYS}", TEXT_PRIMARY, 20, bold=True))
    parts.append(svg_rect(24, 76, 452, 14, BORDER, 3))
    bar_w = int(452 * pct)
    if bar_w > 0:
        parts.append(svg_rect(24, 76, bar_w, 14, ACCENT, 3))
        parts.append(svg_text(24 + bar_w // 2, 86, f"{pct*100:.0f}%", DARK_BG, 10, "middle"))
    parts.append(svg_text(24, 106, "6/11 开幕 — 7/19 决赛", TEXT_SECONDARY, 9))
    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 24, H - 12, f"更新 {now_str} CST", TEXT_SECONDARY, 8, "end"))
    parts.append("</svg>")
    return "\n".join(parts)


def team_label(slug):
    cn, flag = TEAM_NAMES.get(slug, (slug, ""))
    return f"{flag} {cn}"


# ═══════════════════════════════════════════════════════════════
# PANEL 1: 夺冠概率 TOP 10 条形图
# ═══════════════════════════════════════════════════════════════

def generate_championship(teams):
    W, H = 660, 560
    top10 = sorted(teams, key=lambda t: t["pChampion"], reverse=True)[:10]

    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(12, 10, W - 24, H - 20, CARD_BG, 8))
    parts.append(svg_rect(12, 10, W - 24, 1, BORDER))

    # Title
    parts.append(svg_text(30, 38, "🏆 2026世界杯夺冠概率 TOP 10", GOLD, 20, bold=True))
    parts.append(svg_text(30, 60, "Championship Odds · 50,000 Monte Carlo", TEXT_SECONDARY, 12))

    # Bar chart
    bar_x = 170
    bar_max_w = W - bar_x - 80
    bar_h = 22
    start_y = 80
    gap = 10

    for i, t in enumerate(top10):
        y = start_y + i * (bar_h + gap)
        name = team_label(t["slug"])
        pct = t["pChampion"]
        bar_w = int(pct / top10[0]["pChampion"] * bar_max_w)

        parts.append(svg_text(30, y + 16, f"{i+1}.", TEXT_SECONDARY, 12, "end"))
        parts.append(svg_text(40, y + 16, name, TEXT_PRIMARY, 12))
        parts.append(svg_rect(bar_x, y, bar_w, bar_h, BAR_COLORS[i % len(BAR_COLORS)], 3))
        parts.append(svg_text(bar_x + bar_w + 6, y + 16, pct_str(pct), TEXT_PRIMARY, 13, bold=True))

    # Footer
    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 30, H - 24, f"更新 {now_str} CST", TEXT_SECONDARY, 10, "end"))
    parts.append(svg_text(30, H - 24, "数据来源 cup26matches.com · CC BY 4.0", TEXT_SECONDARY, 9))

    parts.append("</svg>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# PANEL 2: 通往决赛之路 — 晋级概率表
# ═══════════════════════════════════════════════════════════════

def generate_path_to_final(teams):
    top8 = sorted(teams, key=lambda t: t["pChampion"], reverse=True)[:8]

    stages = [
        ("32强", "pRound32"), ("16强", "pRound16"), ("8强", "pQuarterfinal"),
        ("4强", "pSemifinal"), ("决赛", "pFinal"), ("🏆冠军", "pChampion"),
    ]
    col_w = 78
    name_w = 150
    row_h = 30
    header_h = 40
    W = name_w + len(stages) * col_w + 60
    H = header_h + len(top8) * row_h + 70

    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(12, 10, W - 24, H - 20, CARD_BG, 8))

    # Title
    parts.append(svg_text(30, 38, "🏆 通往决赛之路 / Path to the Final", GOLD, 14, bold=True))
    parts.append(svg_text(30, 56, "晋级概率 → 从左到右递减", TEXT_SECONDARY, 10))

    table_y = 72
    # Header row
    hx = 30 + name_w
    parts.append(svg_text(30, table_y + 20, "球队 / Team", TEXT_SECONDARY, 11, bold=True))
    for i, (label, _) in enumerate(stages):
        parts.append(svg_text(hx + i * col_w + col_w // 2, table_y + 20, label, TEXT_SECONDARY, 11, "middle"))

    # Separator
    parts.append(f'<line x1="30" y1="{table_y + 28}" x2="{W - 30}" y2="{table_y + 28}" stroke="{BORDER}" stroke-width="1"/>')

    for ri, t in enumerate(top8):
        ry = table_y + 35 + ri * row_h
        name = team_label(t["slug"])
        parts.append(svg_text(30, ry + 18, name, TEXT_PRIMARY, 12))

        for ci, (_, key) in enumerate(stages):
            p = t[key]
            cx = hx + ci * col_w + col_w // 2
            if ci == len(stages) - 1:
                parts.append(svg_text(cx, ry + 18, pct_str(p), GOLD, 12, "middle", True))
            else:
                parts.append(svg_text(cx, ry + 18, pct_str(p), TEXT_PRIMARY, 11, "middle"))

        # Row separator
        if ri < len(top8) - 1:
            parts.append(f'<line x1="30" y1="{ry + 24}" x2="{W - 30}" y2="{ry + 24}" stroke="{BORDER}" stroke-width="0.5"/>')

    # Footer
    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 30, H - 24, f"更新 {now_str} CST · cup26matches.com", TEXT_SECONDARY, 9, "end"))

    parts.append("</svg>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# PANEL 3: 下一场预测
# ═══════════════════════════════════════════════════════════════

def generate_next_match(teams, match_data=None, pm_odds=None):
    """Match data: list of {home, away, winA, draw, winB, blendA, blendD, blendB, ...}"""
    if not match_data:
        match_data = []
    W, H = 600, 400

    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(12, 10, W - 24, H - 20, CARD_BG, 8))

    parts.append(svg_text(24, 36, "⚽ 接下来比赛预测 · Elo + 市场共识", ACCENT, 18, bold=True))
    parts.append(svg_text(24, 58, "Elo + Dixon-Coles 模型 · 混入 Polymarket 赔率 (40/60) · 胜/平/负", TEXT_SECONDARY, 12))

    if not match_data:
        parts.append(svg_text(24, 90, "小组赛已结束 · 淘汰赛数据待发布", TEXT_SECONDARY, 12))
    else:
        sy = 72
        for i, m in enumerate(match_data[:6]):
            y = sy + i * 38
            wa = m.get("blendA", m.get("winA", 0))
            wd = m.get("blendD", m.get("draw", 0))
            wb = m.get("blendB", m.get("winB", 0))
            has_blend = "blendA" in m

            parts.append(svg_text(24, y + 16, m.get("date_short", ""), TEXT_SECONDARY, 10))
            parts.append(svg_text(100, y + 16, f"{team_label(m['home'])}  vs  {team_label(m['away'])}", TEXT_PRIMARY, 11))

            # Bar: home | draw | away
            bx, bw, bh = 300, 170, 14
            parts.append(svg_rect(bx, y + 2, int(bw * wa), bh, GREEN, 3))
            parts.append(svg_rect(bx + int(bw * wa), y + 2, int(bw * wd), bh, GOLD, 0))
            parts.append(svg_rect(bx + int(bw * (wa + wd)), y + 2, int(bw * wb), bh, RED, 3))

            label = f"混{wa*100:.0f}% / {wd*100:.0f}% / {wb*100:.0f}%" if has_blend else f"Elo {wa*100:.0f}% / {wd*100:.0f}% / {wb*100:.0f}%"
            parts.append(svg_text(bx, y + 26, label, TEXT_PRIMARY, 8))

            if has_blend:
                parts.append(svg_text(bx + bw + 8, y + 26, "← 混", GOLD, 8))

    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 30, H - 20, f"更新 {now_str} CST", TEXT_SECONDARY, 9, "end"))

    parts.append("</svg>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# PANEL 4: 即将到来 — 未来5场预测
# ═══════════════════════════════════════════════════════════════

def generate_upcoming(teams, match_data=None):
    W, H = 520, 320
    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(12, 10, W - 24, H - 20, CARD_BG, 8))

    parts.append(svg_text(30, 38, "📅 即将到来 / Upcoming Predictions", ACCENT, 18, bold=True))

    if not match_data or len(match_data) < 2:
        parts.append(svg_text(30, 80, "小组赛已结束 · 淘汰赛数据待发布", TEXT_SECONDARY, 13))
    else:
        upcoming = match_data[1:6]  # next 5 after the current one
        row_h = 38
        start_y = 62

        for i, m in enumerate(upcoming):
            y = start_y + i * row_h
            home_flag, home_name = TEAM_NAMES.get(m["home"], (m["home"], ""))
            away_flag, away_name = TEAM_NAMES.get(m["away"], (m["away"], ""))
            home_full = f"{home_flag} {home_name}"
            away_full = f"{away_flag} {away_name}"

            wa, d, wb = m.get("winA", 0), m.get("draw", 0), m.get("winB", 0)

            parts.append(svg_text(30, y + 18, m.get("date_short", ""), TEXT_SECONDARY, 10))
            parts.append(svg_text(80, y + 18, f"{home_full} vs {away_full}", TEXT_PRIMARY, 12))

            # Mini bars
            bar_x = 310
            bar_w = 180
            bar_h = 10
            bar_y = y + 8
            parts.append(svg_rect(bar_x, bar_y, int(bar_w * wa), bar_h, GREEN, 2))
            parts.append(svg_rect(bar_x + int(bar_w * wa), bar_y, int(bar_w * d), bar_h, GOLD, 0))
            parts.append(svg_rect(bar_x + int(bar_w * (wa + d)), bar_y, int(bar_w * wb), bar_h, RED, 2))

            # Percentages
            pred_text = f"主{wa*100:.0f}% / 平{d*100:.0f}% / 客{wb*100:.0f}%"
            parts.append(svg_text(bar_x, y + 26, pred_text, TEXT_SECONDARY, 9))

            if i < len(upcoming) - 1:
                parts.append(f'<line x1="30" y1="{y + 32}" x2="{W - 30}" y2="{y + 32}" stroke="{BORDER}" stroke-width="0.5"/>')

    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 30, H - 20, f"更新 {now_str} CST", TEXT_SECONDARY, 9, "end"))

    parts.append("</svg>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# ELO MATCH PREDICTION (Hicruben model ported to Python)
# ═══════════════════════════════════════════════════════════════

def expected_score(rating_a, rating_b, home_bonus=0):
    return 1.0 / (1.0 + 10 ** ((rating_b - (rating_a + home_bonus)) / 400.0))


def expected_goals(rating, opponent, home_bonus=0):
    diff = (rating + home_bonus) - opponent
    lam = 1.35 + diff / 400.0
    return max(0.3, min(3.5, lam))


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    p = math.exp(-lam)
    for i in range(1, k + 1):
        p *= lam / i
    return p


DC_RHO = -0.13


def dc_tau(a, b, lam, mu, rho):
    if a == 0 and b == 0:
        return 1 - lam * mu * rho
    if a == 0 and b == 1:
        return 1 + lam * rho
    if a == 1 and b == 0:
        return 1 + mu * rho
    if a == 1 and b == 1:
        return 1 - rho
    return 1.0


def match_prob(rating_a, rating_b, home_bonus=0):
    lam = expected_goals(rating_a, rating_b, home_bonus)
    mu = expected_goals(rating_b, rating_a, -home_bonus / 2)
    win_a = draw = win_b = 0.0
    for a in range(9):
        pa = poisson_pmf(a, lam)
        for b in range(9):
            tau = dc_tau(a, b, lam, mu, DC_RHO)
            p = pa * poisson_pmf(b, mu) * tau
            if a > b:
                win_a += p
            elif a < b:
                win_b += p
            else:
                draw += p
    total = win_a + draw + win_b
    return win_a / total, draw / total, win_b / total


POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"

# Polymarket search alias for each team
PM_SEARCH = {
    "south-korea": ["South Korea", "Korea Republic"],
    "usa": ["United States", "USA"],
    "bosnia-and-herzegovina": ["Bosnia and Herzegovina"],
    "ivory-coast": ["Ivory Coast", "Côte d'Ivoire"],
    "turkey": ["Turkey", "Türkiye"],
    "dr-congo": ["DR Congo", "Democratic Republic of the Congo"],
    "cape-verde": ["Cape Verde", "Cabo Verde"],
    "curacao": ["Curacao", "Curaçao"],
    "czech-republic": ["Czech Republic", "Czechia"],
    "saudi-arabia": ["Saudi Arabia"],
    "south-africa": ["South Africa"],
    "new-zealand": ["New Zealand"],
    "bosnia-and-herzegovina": ["Bosnia and Herzegovina"],
}


def _pm_search_names(slug):
    return PM_SEARCH.get(slug, [slug.replace("-", " ").title()])


def fetch_polymarket_odds(home, away, match_date_str):
    """Fetch (home_p, draw_p, away_p) from Polymarket for one fixture.
    Returns (None, None, None) if not found."""
    home_names = [n.lower() for n in _pm_search_names(home)]
    away_names = [n.lower() for n in _pm_search_names(away)]

    queries = [f"{home} {away}", f"{home_names[0]} {away_names[0]}"]
    event = None

    for q in queries:
        try:
            url = f"{POLYMARKET_GAMMA}/public-search?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers={"User-Agent": "wc-widget/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue

        for ev in data.get("events", []):
            title = (ev.get("title") or "").lower()
            if all(n in title for n in [home_names[0], away_names[0]]) and " vs" in title:
                slug = ev.get("slug", "")
                if match_date_str.replace("/", "-") in slug or match_date_str.replace("/", "") in slug:
                    event = ev
                    break
        if event:
            break

    if not event:
        return None, None, None

    home_p = draw_p = away_p = None
    for market in event.get("markets", []):
        q = (market.get("question") or "").lower()
        prices = market.get("outcomePrices")
        if not prices:
            continue
        try:
            prices = [float(p) for p in (json.loads(prices) if isinstance(prices, str) else prices)]
            yes = prices[0] if prices else None
        except (json.JSONDecodeError, ValueError, IndexError):
            continue
        if yes is None:
            continue

        if "draw" in q or "tie" in q:
            draw_p = yes
        elif "win on" in q or "will win" in q:
            if any(n in q for n in home_names):
                home_p = yes
            elif any(n in q for n in away_names):
                away_p = yes

    return home_p, draw_p, away_p


def fetch_all_polymarket_odds(matches):
    """Fetch Polymarket odds for all upcoming matches (max 6)."""
    pm_data = {}
    for m in matches[:6]:
        date_iso = f"2026-{m['date_short'].replace('/', '-')}"
        hp, dp, ap = fetch_polymarket_odds(m["home"], m["away"], m["date_short"])
        if hp is not None:
            # Normalize: Polymarket gives "Yes" prices that may not sum to 1
            total = (hp or 0) + (dp or 0) + (ap or 0)
            if total > 0:
                pm_data[(m["home"], m["away"])] = {
                    "home": (hp or 0) / total,
                    "draw": (dp or 0) / total,
                    "away": (ap or 0) / total,
                }
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.3)
    return pm_data


def blend_odds(elo_h, elo_d, elo_a, market_h, market_d, market_a, elo_weight=0.4):
    """Blend Elo predictions with market odds. Market gets 60% weight."""
    return (
        elo_weight * elo_h + (1 - elo_weight) * market_h,
        elo_weight * elo_d + (1 - elo_weight) * market_d,
        elo_weight * elo_a + (1 - elo_weight) * market_a,
    )


# ═══════════════════════════════════════════════════════════════
# FIXTURE SCHEDULE (2026 World Cup — first round group stage)
# ═══════════════════════════════════════════════════════════════
# Format: (date_str, time_str, home_slug, away_slug, group)

FIXTURES = [
    # June 11
    ("6/11", "03:00", "mexico", "south-africa", "A"),
    ("6/11", "10:00", "south-korea", "czech-republic", "A"),
    # June 12
    ("6/12", "03:00", "canada", "bosnia-and-herzegovina", "B"),
    ("6/12", "10:00", "qatar", "switzerland", "B"),
    # June 13
    ("6/13", "03:00", "brazil", "morocco", "C"),
    ("6/13", "06:00", "usa", "paraguay", "D"),
    ("6/13", "09:00", "haiti", "scotland", "C"),
    # June 14
    ("6/14", "01:00", "germany", "curacao", "E"),
    ("6/14", "04:00", "netherlands", "japan", "F"),
    ("6/14", "07:00", "ivory-coast", "ecuador", "E"),
    ("6/14", "09:00", "australia", "turkey", "D"),
    ("6/14", "12:00", "sweden", "tunisia", "F"),
    # June 15
    ("6/15", "00:00", "spain", "cape-verde", "H"),
    ("6/15", "03:00", "belgium", "egypt", "G"),
    ("6/15", "06:00", "saudi-arabia", "uruguay", "H"),
    ("6/15", "10:00", "iran", "new-zealand", "G"),
    # June 16
    ("6/16", "03:00", "france", "senegal", "I"),
    ("6/16", "06:00", "iraq", "norway", "I"),
    ("6/16", "09:00", "argentina", "algeria", "J"),
    # June 17
    ("6/17", "00:00", "austria", "jordan", "J"),
    ("6/17", "03:00", "portugal", "dr-congo", "K"),
    ("6/17", "06:00", "england", "croatia", "L"),
    ("6/17", "09:00", "ghana", "panama", "L"),
    ("6/17", "12:00", "uzbekistan", "colombia", "K"),
    # June 18
    ("6/18", "00:00", "czech-republic", "south-africa", "A"),
    ("6/18", "03:00", "switzerland", "bosnia-and-herzegovina", "B"),
    ("6/18", "06:00", "canada", "qatar", "B"),
    ("6/18", "09:00", "mexico", "south-korea", "A"),
    # June 19
    ("6/19", "00:00", "scotland", "morocco", "C"),
    ("6/19", "03:00", "haiti", "brazil", "C"),
    ("6/19", "06:00", "turkey", "usa", "D"),
    ("6/19", "09:00", "paraguay", "australia", "D"),
    # June 20
    ("6/20", "00:00", "ecuador", "germany", "E"),
    ("6/20", "03:00", "curacao", "ivory-coast", "E"),
    ("6/20", "06:00", "japan", "sweden", "F"),
    ("6/20", "09:00", "tunisia", "netherlands", "F"),
    # June 21
    ("6/21", "00:00", "egypt", "iran", "G"),
    ("6/21", "03:00", "new-zealand", "belgium", "G"),
    ("6/21", "06:00", "uruguay", "spain", "H"),
    ("6/21", "09:00", "cape-verde", "saudi-arabia", "H"),
    # June 22
    ("6/22", "00:00", "senegal", "iraq", "I"),
    ("6/22", "03:00", "norway", "france", "I"),
    ("6/22", "06:00", "jordan", "argentina", "J"),
    ("6/22", "09:00", "algeria", "austria", "J"),
    # June 23
    ("6/23", "00:00", "croatia", "ghana", "L"),
    ("6/23", "03:00", "panama", "england", "L"),
    ("6/23", "06:00", "colombia", "portugal", "K"),
    ("6/23", "09:00", "dr-congo", "uzbekistan", "K"),
]

HOSTS = {"mexico", "usa", "canada"}
HOME_ADV = 75


def _build_knockout_fixtures(ratings):
    """Dynamically build knockout fixtures from openfootball group results."""
    import ssl as _ssl
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE

    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
    req = urllib.request.Request(url, headers={"User-Agent": "wc-widget/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        data = json.loads(resp.read())

    # Compute group standings
    from collections import defaultdict as _dd
    group_matches = _dd(list)
    for m in data.get("matches", []):
        grp = m.get("group", "")
        if grp:
            group_matches[grp].append(m)

    standings = {}
    for grp_name, matches in group_matches.items():
        letter = grp_name.replace("Group ", "").strip()
        teams = _dd(lambda: {"pts": 0, "gf": 0, "ga": 0})
        for m in matches:
            t1, t2 = m.get("team1", ""), m.get("team2", "")
            score = m.get("score", {}).get("ft")
            if not score or not t1 or not t2: continue
            g1, g2 = score[0], score[1]
            teams[t1]["gf"] += g1; teams[t1]["ga"] += g2
            teams[t2]["gf"] += g2; teams[t2]["ga"] += g1
            if g1 > g2: teams[t1]["pts"] += 3
            elif g2 > g1: teams[t2]["pts"] += 3
            else: teams[t1]["pts"] += 1; teams[t2]["pts"] += 1
        sorted_teams = sorted(teams.items(),
            key=lambda x: (x[1]["pts"], x[1]["gf"] - x[1]["ga"], x[1]["gf"]),
            reverse=True)
        standings[letter] = []
        for name, stats in sorted_teams:
            slug = OF_NAME_MAP.get(name, name.lower().replace(" ", "-"))
            standings[letter].append(slug)

    # Build R32 pairings: 1A vs 2B, 1C vs 2D, etc.
    w = {l: standings[l][0] for l in sorted(standings) if len(standings[l]) >= 1}
    r = {l: standings[l][1] for l in sorted(standings) if len(standings[l]) >= 2}

    r32_pairs = [
        (w.get("A","?"), r.get("B","?")), (w.get("C","?"), r.get("D","?")),
        (w.get("E","?"), r.get("F","?")), (w.get("G","?"), r.get("H","?")),
        (w.get("I","?"), r.get("J","?")), (w.get("K","?"), r.get("L","?")),
        (w.get("B","?"), r.get("A","?")), (w.get("D","?"), r.get("C","?")),
        (w.get("F","?"), r.get("E","?")), (w.get("H","?"), r.get("G","?")),
        (w.get("J","?"), r.get("I","?")), (w.get("L","?"), r.get("K","?")),
    ]

    # 8 best 3rd place teams
    thirds = []
    for l in sorted(standings):
        if len(standings[l]) >= 3:
            thirds.append((standings[l][2], l))
    # Approximate 3rd place allocation to remaining R32 slots
    for t, _ in thirds[:4]:
        if len(r32_pairs) < 16:
            # Pair unassigned group winners with 3rd place teams
            for wl in sorted(w):
                if w[wl] not in [p[0] for p in r32_pairs] and w[wl] != t:
                    r32_pairs.append((w[wl], t))
                    break

    # Assign dates (June 28 - July 1 for R32)
    dates = [
        ("6/28", "00:00"), ("6/28", "03:00"), ("6/28", "06:00"), ("6/28", "09:00"),
        ("6/29", "00:00"), ("6/29", "03:00"), ("6/29", "06:00"), ("6/29", "09:00"),
        ("6/30", "00:00"), ("6/30", "03:00"), ("6/30", "06:00"), ("6/30", "09:00"),
        ("7/01", "00:00"), ("7/01", "03:00"), ("7/01", "06:00"), ("7/01", "09:00"),
    ]

    fixtures = []
    for i, (home, away) in enumerate(r32_pairs):
        if home == "?" or away == "?":
            continue
        if i < len(dates):
            fixtures.append((*dates[i], home, away, "R32"))

    return fixtures


def generate_match_data(teams_data: list[dict]):
    """Use calibrated Elo from cup26matches data to predict upcoming fixtures."""
    # Build Elo lookup — we approximate from the probabilities.json data
    # since we don't have the raw Elo ratings directly. We'll use the championship
    # odds as a proxy ranking and assign ratings accordingly.
    # Better: use the match_prob with approximate ratings derived from team strength.

    # For now, we use the Hicruben calibrated ratings directly.
    # These are available in the repo's data/elo-calibrated.json
    # We'll read from the local file if available, otherwise estimate.

    ratings_path = os.path.join(os.path.dirname(__file__), "..", "data", "elo-calibrated.json")
    ratings = {}
    if os.path.exists(ratings_path):
        with open(ratings_path) as f:
            cal = json.load(f)
            ratings = cal.get("ratings", {})
    else:
        # Fallback: approximate from championship odds order
        sorted_teams = sorted(teams_data, key=lambda t: t["pChampion"], reverse=True)
        for i, t in enumerate(sorted_teams):
            ratings[t["slug"]] = 2100 - i * 12

    # Find upcoming fixtures (date >= today in CST)
    now = datetime.now(TZ)
    today_str = now.strftime("%m/%d")

    matches = []
    for date_str, time_str, home, away, group in FIXTURES:
        match_month = int(date_str.split("/")[0])
        match_day = int(date_str.split("/")[1])
        match_date = datetime(2026, match_month, match_day, tzinfo=TZ)

        if match_date.date() < now.date():
            continue

        ra = ratings.get(home, 1500)
        rb = ratings.get(away, 1500)
        hb = HOME_ADV if home in HOSTS else 0
        wa, d, wb = match_prob(ra, rb, hb)

        matches.append({
            "home": home, "away": away,
            "date": f"{date_str} {time_str} CST", "date_short": f"{date_str}",
            "time": time_str, "group": group,
            "winA": wa, "draw": d, "winB": wb,
        })

    # If no upcoming group-stage fixtures, generate knockout fixtures
    if not matches:
        print("[predictions] No group fixtures remaining — building knockout bracket...")
        knockout = _build_knockout_fixtures(ratings)
        for date_str, time_str, home, away, round_name in knockout:
            ra = ratings.get(home, 1500)
            rb = ratings.get(away, 1500)
            wa, d, wb = match_prob(ra, rb)
            matches.append({
                "home": home, "away": away,
                "date": f"{date_str} {time_str} CST", "date_short": f"{date_str}",
                "time": time_str, "group": round_name,
                "winA": wa, "draw": d, "winB": wb,
            })
        print(f"[predictions] Added {len(knockout)} knockout fixtures")

    return matches


# ═══════════════════════════════════════════════════════════════
# MATCH RESULTS (from openfootball)
# ═══════════════════════════════════════════════════════════════

OPENFOOTBALL_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

# openfootball team name → our slug
OF_NAME_MAP = {
    "Mexico": "mexico", "South Africa": "south-africa", "South Korea": "south-korea",
    "Czech Republic": "czech-republic", "Canada": "canada",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina", "Qatar": "qatar",
    "Bosnia & Herzegovina": "bosnia-and-herzegovina",
    "Switzerland": "switzerland", "Brazil": "brazil", "Morocco": "morocco",
    "United States": "usa", "USA": "usa", "Paraguay": "paraguay", "Haiti": "haiti",
    "Scotland": "scotland", "Germany": "germany", "Curaçao": "curacao",
    "Ivory Coast": "ivory-coast", "Ecuador": "ecuador", "Netherlands": "netherlands",
    "Japan": "japan", "Australia": "australia", "Turkey": "turkey",
    "Sweden": "sweden", "Tunisia": "tunisia", "Spain": "spain",
    "Cape Verde": "cape-verde", "Belgium": "belgium", "Egypt": "egypt",
    "Saudi Arabia": "saudi-arabia", "Uruguay": "uruguay", "Iran": "iran",
    "New Zealand": "new-zealand", "France": "france", "Senegal": "senegal",
    "Iraq": "iraq", "Norway": "norway", "Argentina": "argentina",
    "Algeria": "algeria", "Austria": "austria", "Jordan": "jordan",
    "Portugal": "portugal", "DR Congo": "dr-congo",
    "England": "england", "Croatia": "croatia", "Ghana": "ghana",
    "Panama": "panama", "Uzbekistan": "uzbekistan", "Colombia": "colombia",
}


def fetch_match_results():
    """Fetch completed match results from openfootball."""
    req = urllib.request.Request(OPENFOOTBALL_URL, headers={"User-Agent": "wc-widget/1.0"})
    results = []
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for m in data.get("matches", []):
            score = m.get("score", {})
            ft = score.get("ft")
            if ft and len(ft) == 2:
                home_slug = OF_NAME_MAP.get(m.get("team1", ""))
                away_slug = OF_NAME_MAP.get(m.get("team2", ""))
                if home_slug and away_slug:
                    results.append({
                        "date": m.get("date", "")[-5:],  # "MM-DD"
                        "home": home_slug,
                        "away": away_slug,
                        "hg": ft[0],
                        "ag": ft[1],
                    })
    except Exception as e:
        print(f"[record] Failed to fetch openfootball data: {e}")
    results.sort(key=lambda r: r["date"])  # chronological order
    return results


def generate_record(match_results):
    """Generate record.svg — model prediction accuracy tracker."""
    lbl = team_label  # local alias
    if not match_results:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 100"><rect width="500" height="100" fill="#0d1117"/><text x="20" y="40" fill="#8b949e" font-size="14" font-family="monospace">暂无比赛数据</text></svg>'

    # Load Elo ratings and run walk-forward
    ratings_path = os.path.join(os.path.dirname(__file__), "..", "data", "elo-calibrated.json")
    ratings = {}
    if os.path.exists(ratings_path):
        with open(ratings_path) as f:
            ratings = json.load(f).get("ratings", {})

    # Walk-forward: for each match in chronological order, predict then update
    items = []
    temp_ratings = dict(ratings)  # start from pre-tournament ratings
    hit, miss = 0, 0

    for m in match_results:
        ra = temp_ratings.get(m["home"], 1500)
        rb = temp_ratings.get(m["away"], 1500)
        hb = HOME_ADV if m["home"] in HOSTS else 0
        wa, d, wb = match_prob(ra, rb, hb)

        # Determine model's pick (highest probability)
        probs = [("home", wa), ("draw", d), ("away", wb)]
        probs.sort(key=lambda x: x[1], reverse=True)
        pick = probs[0][0]
        pick_pct = probs[0][1]

        # Determine actual result
        if m["hg"] > m["ag"]:
            actual = "home"
        elif m["hg"] < m["ag"]:
            actual = "away"
        else:
            actual = "draw"

        correct = pick == actual
        if correct:
            hit += 1
        else:
            miss += 1

        # Pick display name
        if pick == "home":
            pick_name = lbl(m["home"]).split(" ", 1)[-1] if " " in lbl(m["home"]) else m["home"]
        elif pick == "away":
            pick_name = lbl(m["away"]).split(" ", 1)[-1] if " " in lbl(m["away"]) else m["away"]
        else:
            pick_name = "平局"

        items.append({
            "date": m["date"],
            "home": m["home"],
            "away": m["away"],
            "score": f"{m['hg']}-{m['ag']}",
            "pick": f"{pick_name} {pick_pct*100:.0f}%",
            "correct": correct,
        })

        # Update Elo after the match
        exp = expected_score(ra, rb, hb)
        score_val = 1.0 if m["hg"] > m["ag"] else (0.0 if m["hg"] < m["ag"] else 0.5)
        gd = abs(m["hg"] - m["ag"])
        g = 1.0 if gd <= 1 else (1.5 if gd == 2 else (11 + gd) / 8)
        delta = 60 * g * (score_val - exp)
        temp_ratings[m["home"]] = ra + delta
        temp_ratings[m["away"]] = rb - delta

    total = hit + miss
    pct = hit / total * 100 if total > 0 else 0

    # Build SVG
    row_h = 20
    header_h = 50
    H = header_h + len(items) * row_h + 65
    W = 500

    parts = [svg_header(W, H)]
    parts.append(svg_rect(0, 0, W, H, DARK_BG))
    parts.append(svg_rect(10, 8, W - 20, H - 16, CARD_BG, 8))

    parts.append(svg_text(24, 34, "📋 模型战绩 · Model Scorecard", ACCENT, 18, bold=True))
    parts.append(svg_text(24, 56, f"已完赛 {total}/104 场 · 预测正确 {hit} 场 · 准确率 {pct:.0f}%", TEXT_SECONDARY, 12))

    # Summary badges
    parts.append(svg_rect(24, 62, 48, 18, GREEN, 3))
    parts.append(svg_text(48, 75, f"{hit} ✅", DARK_BG, 10, "middle", bold=True))
    parts.append(svg_rect(84, 62, 48, 18, RED, 3))
    parts.append(svg_text(108, 75, f"{miss} ❌", DARK_BG, 10, "middle", bold=True))

    # Table header
    ty = 100
    parts.append(svg_text(24, ty, "日期", TEXT_SECONDARY, 9, bold=True))
    parts.append(svg_text(68, ty, "主队", TEXT_SECONDARY, 9, bold=True))
    parts.append(svg_text(172, ty, "比分", TEXT_SECONDARY, 9, "middle", bold=True))
    parts.append(svg_text(220, ty, "客队", TEXT_SECONDARY, 9, bold=True))
    parts.append(svg_text(315, ty, "模型预测", TEXT_SECONDARY, 9, bold=True))
    parts.append(svg_text(435, ty, "结果", TEXT_SECONDARY, 9, "middle", bold=True))
    parts.append(f'<line x1="24" y1="{ty+8}" x2="{W-24}" y2="{ty+8}" stroke="{BORDER}" stroke-width="1"/>')

    for i, item in enumerate(items[-20:]):  # show last 20
        y = ty + 20 + i * row_h
        parts.append(svg_text(24, y, item["date"], TEXT_SECONDARY, 9))
        parts.append(svg_text(68, y, lbl(item["home"]), TEXT_PRIMARY, 10))
        parts.append(svg_text(172, y, item["score"], TEXT_PRIMARY, 10, "middle", bold=True))
        parts.append(svg_text(220, y, lbl(item["away"]), TEXT_PRIMARY, 10))
        parts.append(svg_text(315, y, item["pick"], TEXT_SECONDARY, 10))
        mark = "✅" if item["correct"] else "❌"
        color = GREEN if item["correct"] else RED
        parts.append(svg_text(435, y, mark, color, 11, "middle"))

    parts.append(f'<line x1="24" y1="{ty + 20 + len(items[-20:]) * row_h + 2}" x2="{W-24}" y2="{ty + 20 + len(items[-20:]) * row_h + 2}" stroke="{BORDER}" stroke-width="0.5"/>')
    parts.append(svg_text(24, H - 30, "RPS 0.175 · walk-forward 预测 · 数据 openfootball + cup26matches.com", TEXT_SECONDARY, 9))
    now_str = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    parts.append(svg_text(W - 24, H - 16, f"更新 {now_str} CST", TEXT_SECONDARY, 8, "end"))
    parts.append("</svg>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("[predictions] Fetching data from cup26matches.com...")
    try:
        data = fetch_data()
        teams = data["teams"]
        print(f"[predictions] Got {len(teams)} teams, {data['trials']} trials")
    except Exception as e:
        print(f"[predictions] Failed to fetch cup26matches data: {e}")
        teams = []

    print("[predictions] Computing match predictions...")
    matches = generate_match_data(teams)
    upcoming = [m for m in matches if m["date_short"] >= datetime.now(TZ).strftime("%m/%d")]

    print("[predictions] Fetching Polymarket odds...")
    try:
        pm_odds = fetch_all_polymarket_odds(upcoming[:6])
        print(f"[predictions] Got Polymarket odds for {len(pm_odds)} matches")
    except Exception as e:
        print(f"[predictions] Polymarket fetch failed: {e}")
        pm_odds = {}

    # Blend Elo + market odds into match data
    for m in upcoming[:6]:
        key = (m["home"], m["away"])
        if key in pm_odds:
            pm = pm_odds[key]
            bh, bd, ba = blend_odds(m["winA"], m["draw"], m["winB"], pm["home"], pm["draw"], pm["away"])
            m["blendA"] = bh
            m["blendD"] = bd
            m["blendB"] = ba
            m["pmA"] = pm["home"]
            m["pmD"] = pm["draw"]
            m["pmB"] = pm["away"]

    print("[predictions] Generating next-match.svg...")
    with open(os.path.join(OUT_DIR, "next-match.svg"), "w", encoding="utf-8") as f:
        f.write(generate_next_match(teams, upcoming, pm_odds))

    print("[predictions] Generating championship.svg...")
    with open(os.path.join(OUT_DIR, "championship.svg"), "w", encoding="utf-8") as f:
        f.write(generate_championship(teams))

    print("[predictions] Generating path-to-final.svg...")
    with open(os.path.join(OUT_DIR, "path-to-final.svg"), "w", encoding="utf-8") as f:
        f.write(generate_path_to_final(teams))

    print("[predictions] Generating upcoming.svg...")
    with open(os.path.join(OUT_DIR, "upcoming.svg"), "w", encoding="utf-8") as f:
        f.write(generate_upcoming(teams, upcoming))

    print("[predictions] Generating day-tracker.svg...")
    with open(os.path.join(OUT_DIR, "day-tracker.svg"), "w", encoding="utf-8") as f:
        f.write(generate_day_tracker())

    print("[predictions] Fetching match results from openfootball...")
    results = fetch_match_results()
    print(f"[predictions] Got {len(results)} completed matches")

    print("[predictions] Generating record.svg...")
    record_svg = generate_record(results)
    with open(os.path.join(OUT_DIR, "record.svg"), "w", encoding="utf-8") as f:
        f.write(record_svg)

    print(f"[predictions] ✅ All SVGs generated in {OUT_DIR}")
    for fname in ["day-tracker.svg", "record.svg", "next-match.svg", "championship.svg", "path-to-final.svg", "upcoming.svg"]:
        fpath = os.path.join(OUT_DIR, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            print(f"  {fname}: {size:,} bytes")
        else:
            print(f"  {fname}: MISSING")


if __name__ == "__main__":
    main()
