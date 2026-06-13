"""
Post-process World Cup 2026 SVG panels to add Chinese translations.
Replaces English labels with Chinese versions, including team names.
"""
import re
from pathlib import Path

# ============================================================
# Team name translations: 3-letter FIFA code → Chinese
# Covers all 48 participating nations + common football nations
# ============================================================
TEAM_NAMES = {
    # North America (hosts)
    "USA": "美国", "MEX": "墨西哥", "CAN": "加拿大",
    # South America (CONMEBOL)
    "ARG": "阿根廷", "BRA": "巴西", "URU": "乌拉圭",
    "COL": "哥伦比亚", "ECU": "厄瓜多尔", "PER": "秘鲁",
    "CHI": "智利", "PAR": "巴拉圭", "BOL": "玻利维亚",
    "VEN": "委内瑞拉",
    # Europe (UEFA)
    "ENG": "英格兰", "ESP": "西班牙", "FRA": "法国",
    "GER": "德国", "ITA": "意大利", "NED": "荷兰",
    "POR": "葡萄牙", "BEL": "比利时", "CRO": "克罗地亚",
    "DEN": "丹麦", "SUI": "瑞士", "SRB": "塞尔维亚",
    "POL": "波兰", "AUT": "奥地利", "UKR": "乌克兰",
    "TUR": "土耳其", "SWE": "瑞典", "WAL": "威尔士",
    "SCO": "苏格兰", "NOR": "挪威", "CZE": "捷克",
    "HUN": "匈牙利", "ROU": "罗马尼亚", "GRE": "希腊",
    "SVK": "斯洛伐克", "SVN": "斯洛文尼亚",
    # Africa (CAF)
    "SEN": "塞内加尔", "MAR": "摩洛哥", "TUN": "突尼斯",
    "NGA": "尼日利亚", "GHA": "加纳", "EGY": "埃及",
    "CMR": "喀麦隆", "CIV": "科特迪瓦", "ALG": "阿尔及利亚",
    "RSA": "南非", "MLI": "马里", "BFA": "布基纳法索",
    # Asia (AFC)
    "JPN": "日本", "KOR": "韩国", "IRN": "伊朗",
    "KSA": "沙特", "AUS": "澳大利亚", "QAT": "卡塔尔",
    "UAE": "阿联酋", "IRQ": "伊拉克", "UZB": "乌兹别克斯坦",
    "CHN": "中国", "JOR": "约旦",
    # Oceania (OFC)
    "NZL": "新西兰",
    # Additional / CONCACAF
    "CRC": "哥斯达黎加", "PAN": "巴拿马", "JAM": "牙买加",
    "HON": "洪都拉斯", "SLV": "萨尔瓦多",
}

# ============================================================
# Label translations
# ============================================================
LABEL_TRANSLATIONS = [
    # --- Panel headers ---
    ("WORLD CUP 26 · COUNTDOWN", "世界杯 2026 · 倒计时"),
    ("WORLD CUP 26 · TODAY", "世界杯 2026 · 今日赛程"),
    ("WORLD CUP 26 · ROUND-OF-32 TRACKER", "世界杯 2026 · 32强出线追踪"),
    ("WORLD CUP 26 · BRACKET", "世界杯 2026 · 淘汰赛对阵"),
    ("WORLD CUP 26 · ALL GROUPS", "世界杯 2026 · 全部小组"),
    ("WORLD CUP 26 · TOP SCORERS", "世界杯 2026 · 射手榜"),
    ("WORLD CUP 26 · STATS", "世界杯 2026 · 数据统计"),

    # --- Status labels ---
    ("8 best third-placed teams advance", "8支最佳小组第三晋级"),
    ("DAYS TO KICKOFF", "距开幕"),
    ("OF 39 · UNDERWAY", "共39天 · 进行中"),
    ("OF 39 · TODAY", "共39天 · 今日"),

    # --- Column headers (R32 panel, groups panel) ---
    (">GRP<", ">组<"),
    (">GD<", ">净胜<"),
    (">PTS<", ">分<"),
    (">GF<", ">进球<"),
    (">GA<", ">失球<"),
    (">W<", ">胜<"),
    (">D<", ">平<"),
    (">L<", ">负<"),

    # --- Bracket round labels ---
    (">R32<", ">32强<"),
    (">R16<", ">16强<"),
    (">QF<", ">8强<"),
    (">SF<", ">半决赛<"),
    (">FINAL<", ">决赛<"),

    # --- Status indicators ---
    (">LIVE<", ">直播中<"),
    (">QUALIFIED<", ">已晋级<"),
    (">ELIMINATED<", ">已淘汰<"),
    (">qualified<", ">已晋级<"),
    (">eliminated<", ">已淘汰<"),
    ("Qualified", "已晋级"),
    ("Eliminated", "已淘汰"),
    ("qualified", "已晋级"),
    ("eliminated", "已淘汰"),

    # --- R32 specific ---
    ("Qualification Cut", "晋级线"),
    ("3rd place", "第三名"),
    ("3rd", "第三"),
    ("pts", "分"),
    ("Pts", "分"),
    ("Rank", "排名"),
    ("Team", "球队"),
    ("Played", "已赛"),
    ("Won", "胜"),
    ("Drawn", "平"),
    ("Lost", "负"),

    # --- Misc ---
    ("Final ·", "决赛 ·"),
    ("Kickoff ·", "开幕 ·"),
    ("Group ", "小组 "),
    ("Standings", "积分榜"),
    ("Fixtures", "赛程"),
    ("Goals", "进球"),
    ("Assists", "助攻"),
    ("Top Scorers", "射手榜"),
    ("Clean Sheets", "零封"),
    ("Penalties", "点球"),
    ("Biggest Win", "最大比分"),
    ("Tournament Stats", "赛事统计"),
    ("Total Goals", "总进球"),
    ("Matches Played", "已赛场次"),
    ("H2H", "交手"),
    ("EXTRAS", "加时"),
    ("PEN", "点球"),
]

# Regex replacements for dynamic content
REGEX_TRANSLATIONS = [
    (r"WORLD CUP 26 · GROUP ([A-L])", r"世界杯 2026 · 小组 \1"),
    # Days of week in dates
    (r">Mon<", r">周一<"),
    (r">Tue<", r">周二<"),
    (r">Wed<", r">周三<"),
    (r">Thu<", r">周四<"),
    (r">Fri<", r">周五<"),
    (r">Sat<", r">周六<"),
    (r">Sun<", r">周日<"),
]


def translate_team_names(content: str) -> str:
    """Replace 3-letter team codes with Chinese names in SVG text elements.
    
    Only replaces when the code appears as a standalone text node
    (e.g., <text ...>USA</text>), NOT when it's part of other text.
    """
    result = content
    
    # For each team code, replace it when it appears as the full text content
    for code, zh_name in TEAM_NAMES.items():
        # Only replace when the code is the ENTIRE content between text tags
        result = re.sub(
            rf'(<text[^>]*>)\s*{re.escape(code)}\s*(</text>)',
            rf'\1{zh_name}\2',
            result
        )
    
    return result


def translate_labels(content: str) -> str:
    """Apply label translations."""
    result = content
    for en, zh in LABEL_TRANSLATIONS:
        result = result.replace(en, zh)
    
    for pattern, replacement in REGEX_TRANSLATIONS:
        result = re.sub(pattern, replacement, result)
    
    return result


def translate_svg(content: str) -> str:
    """Apply all translations to SVG content."""
    result = translate_labels(content)
    result = translate_team_names(result)
    return result


def main():
    wc26_dir = Path(".github/wc26")
    if not wc26_dir.exists():
        print("No .github/wc26 directory found")
        return
    
    svg_files = sorted(wc26_dir.glob("*.svg"))
    if not svg_files:
        print("No SVG files found")
        return
    
    for svg_path in svg_files:
        original = svg_path.read_text(encoding="utf-8")
        translated = translate_svg(original)
        if translated != original:
            svg_path.write_text(translated, encoding="utf-8")
            print(f"✓ Translated: {svg_path.name}")
        else:
            print(f"  No changes: {svg_path.name}")


if __name__ == "__main__":
    main()
