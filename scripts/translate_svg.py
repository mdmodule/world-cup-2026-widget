"""
Post-process World Cup 2026 SVG panels to add Chinese translations.
Replaces English labels with bilingual (Chinese-first) versions.
"""
import re
import sys
from pathlib import Path

# Translation map: exact SVG text → Chinese replacement
# Order matters: longer strings first to avoid partial matches
TRANSLATIONS = [
    # --- Panel headers ---
    ("WORLD CUP 26 · COUNTDOWN", "世界杯 2026 · 倒计时"),
    ("WORLD CUP 26 · TODAY", "世界杯 2026 · 今日赛程"),
    ("WORLD CUP 26 · ROUND-OF-32 TRACKER", "世界杯 2026 · 32强出线追踪"),
    ("WORLD CUP 26 · BRACKET", "世界杯 2026 · 淘汰赛对阵"),
    # --- Group headers (e.g. "WORLD CUP 26 · GROUP D") ---
    # We'll handle these with a regex replacement below

    # --- Status labels ---
    ("8 best third-placed teams advance", "8支最佳小组第三晋级"),
    ("DAYS TO KICKOFF", "距开幕"),
    ("OF 39 · UNDERWAY", "共39天 · 进行中"),
    ("OF 39 · TODAY", "共39天 · 今日"),

    # --- Column headers (R32 panel) ---
    (">GRP<", ">组<"),
    (">GD<", ">净胜<"),
    (">PTS<", ">分<"),

    # --- Bracket round labels (surrounded by >...< in SVG) ---
    (">R32<", ">32强<"),
    (">R16<", ">16强<"),
    (">QF<", ">8强<"),
    (">SF<", ">半决赛<"),
    (">FINAL<", ">决赛<"),

    # --- Live status dots (in text elements) ---
    (">LIVE<", ">直播中<"),

    # --- Countdown footer ---
    ("Final ·", "决赛 ·"),
    ("Kickoff ·", "开幕 ·"),
]

# Regex-based replacements (for dynamic content like "WORLD CUP 26 · GROUP X")
REGEX_TRANSLATIONS = [
    (r"WORLD CUP 26 · GROUP ([A-L])", r"世界杯 2026 · 小组 \1"),
]


def translate_svg(content: str) -> str:
    """Apply translations to SVG content."""
    result = content
    
    # Apply exact string replacements
    for en, zh in TRANSLATIONS:
        result = result.replace(en, zh)
    
    # Apply regex replacements
    for pattern, replacement in REGEX_TRANSLATIONS:
        result = re.sub(pattern, replacement, result)
    
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
