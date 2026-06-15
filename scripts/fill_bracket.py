"""
Fill bracket SVG slots with actual team names from openfootball data.
Computes group standings from match results, then maps teams to bracket slots.

Runs after translate_svg.py in the workflow.
"""
import json
import re
import urllib.request
from pathlib import Path
from collections import defaultdict

# ============================================================
# Configuration
# ============================================================
DATA_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
GROUPS = list("ABCDEFGHIJKL")

# Full name → 3-letter code mapping (from openfootball data)
TEAM_FULL_TO_CODE = {
    "Mexico": "MEX", "South Korea": "KOR", "Czech Republic": "CZE",
    "South Africa": "RSA", "Canada": "CAN",
    "Bosnia & Herzegovina": "BIH", "Spain": "ESP", "Paraguay": "PAR",
    "United States": "USA", "Croatia": "CRO", "Morocco": "MAR",
    "Australia": "AUS", "Switzerland": "SUI", "Argentina": "ARG",
    "Saudi Arabia": "KSA", "Poland": "POL", "Japan": "JPN",
    "France": "FRA", "Nigeria": "NGA", "Italy": "ITA",
    "Chile": "CHI", "Sweden": "SWE", "Brazil": "BRA",
    "Egypt": "EGY", "Cameroon": "CMR", "Germany": "GER",
    "Iran": "IRN", "Colombia": "COL", "England": "ENG",
    "Uruguay": "URU", "Senegal": "SEN", "Portugal": "POR",
    "Netherlands": "NED", "Ecuador": "ECU", "Belgium": "BEL",
    "Denmark": "DEN", "Ghana": "GHA", "Peru": "PER",
    "Tunisia": "TUN", "Algeria": "ALG", "Wales": "WAL",
    "Scotland": "SCO", "Turkey": "TUR", "Ukraine": "UKR",
    "Serbia": "SRB", "Austria": "AUT", "Costa Rica": "CRC",
    "New Zealand": "NZL",
}

# Chinese team name mapping
TEAM_CODE_TO_ZH = {
    "MEX": "墨西哥", "KOR": "韩国", "CZE": "捷克", "RSA": "南非",
    "CAN": "加拿大", "BIH": "波黑", "ESP": "西班牙", "PAR": "巴拉圭",
    "USA": "美国", "CRO": "克罗地亚", "MAR": "摩洛哥", "AUS": "澳大利亚",
    "SUI": "瑞士", "ARG": "阿根廷", "KSA": "沙特", "POL": "波兰",
    "JPN": "日本", "FRA": "法国", "NGA": "尼日利亚", "ITA": "意大利",
    "CHI": "智利", "SWE": "瑞典", "BRA": "巴西", "EGY": "埃及",
    "CMR": "喀麦隆", "GER": "德国", "IRN": "伊朗", "COL": "哥伦比亚",
    "ENG": "英格兰", "URU": "乌拉圭", "SEN": "塞内加尔", "POR": "葡萄牙",
    "NED": "荷兰", "ECU": "厄瓜多尔", "BEL": "比利时", "DEN": "丹麦",
    "GHA": "加纳", "PER": "秘鲁", "TUN": "突尼斯", "ALG": "阿尔及利亚",
    "WAL": "威尔士", "SCO": "苏格兰", "TUR": "土耳其", "UKR": "乌克兰",
    "SRB": "塞尔维亚", "AUT": "奥地利", "CRC": "哥斯达黎加", "NZL": "新西兰",
}


def fetch_data():
    """Download worldcup.json data."""
    req = urllib.request.Request(DATA_URL)
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def compute_standings(data):
    """Compute group standings from match results.
    
    Returns: {
        'A': [(code, pts, gd, gs), ...],  # sorted by pts desc, gd desc, gs desc
    }
    """
    # Collect matches by group
    group_matches = defaultdict(list)
    for m in data.get('matches', []):
        grp = m.get('group', '')
        if not grp:
            continue
        group_matches[grp].append(m)
    
    standings = {}
    for grp_name, matches in group_matches.items():
        # Extract group letter
        letter = grp_name.replace('Group ', '').strip()
        
        # Compute team stats
        teams = defaultdict(lambda: {'pts': 0, 'gf': 0, 'ga': 0, 'played': 0})
        
        for m in matches:
            t1 = m.get('team1', '')
            t2 = m.get('team2', '')
            score = m.get('score')
            if not score or not t1 or not t2:
                continue
            
            ft = score.get('ft', score.get('ht'))
            if not ft:
                continue
            
            g1, g2 = ft[0], ft[1]
            
            # Team 1 stats
            t1_key = t1
            teams[t1_key]['gf'] += g1
            teams[t1_key]['ga'] += g2
            teams[t1_key]['played'] += 1
            
            # Team 2 stats
            t2_key = t2
            teams[t2_key]['gf'] += g2
            teams[t2_key]['ga'] += g1
            teams[t2_key]['played'] += 1
            
            # Points
            if g1 > g2:
                teams[t1_key]['pts'] += 3
            elif g2 > g1:
                teams[t2_key]['pts'] += 3
            else:
                teams[t1_key]['pts'] += 1
                teams[t2_key]['pts'] += 1
        
        # Sort: pts desc, gd desc, gf desc
        sorted_teams = sorted(
            teams.items(),
            key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga'], x[1]['gf']),
            reverse=True
        )
        
        # Convert to list of (code, pts, gd, gs)
        result = []
        for name, stats in sorted_teams:
            code = TEAM_FULL_TO_CODE.get(name, name[:3].upper())
            result.append((code, stats['pts'], stats['gf'] - stats['ga'], stats['gf']))
        
        standings[letter] = result
    
    return standings


def fill_bracket_slots(bracket_svg, standings):
    """Replace bracket placeholders with actual team names (in Chinese)."""
    result = bracket_svg
    
    # Build lookup: "1A" → team code, "2B" → team code, etc.
    slot_to_team = {}
    
    for letter, teams in standings.items():
        if len(teams) >= 1:
            slot_to_team[f"1{letter}"] = teams[0][0]  # 1st place
        if len(teams) >= 2:
            slot_to_team[f"2{letter}"] = teams[1][0]  # 2nd place
    
    # Replace group position placeholders in text elements
    # e.g., <text ...>A1</text> → <text ...>美国</text>
    for slot_code, team_code in slot_to_team.items():
        zh_name = TEAM_CODE_TO_ZH.get(team_code, team_code)
        # Only replace when the slot code is the ENTIRE text node content
        result = re.sub(
            rf'(<text[^>]*>)\s*{re.escape(slot_code)}\s*(</text>)',
            rf'\1{zh_name}\2',
            result
        )
    
    return result


def main():
    wc26_dir = Path(".github/wc26")
    bracket_path = wc26_dir / "bracket.svg"
    
    if not bracket_path.exists():
        print("No bracket.svg found")
        return
    
    # Fetch data
    try:
        data = fetch_data()
        print("✓ Downloaded worldcup.json")
    except Exception as e:
        print(f"✗ Failed to download data: {e}")
        return
    
    # Compute standings
    standings = compute_standings(data)
    
    filled = 0
    for letter, teams in standings.items():
        print(f"  Group {letter}: {', '.join(f'{TEAM_CODE_TO_ZH.get(c,c)}({p}分)' for c,p,_,_ in teams[:3])}")
        filled += len(teams)
    
    if filled == 0:
        print("  No standings data available — bracket slots remain as placeholders")
        return
    
    # Read and fill bracket
    original = bracket_path.read_text(encoding="utf-8")
    updated = fill_bracket_slots(original, standings)
    
    if updated != original:
        bracket_path.write_text(updated, encoding="utf-8")
        print(f"✓ Filled bracket with team names ({filled} teams)")
    else:
        print("  No changes to bracket")


if __name__ == "__main__":
    main()
