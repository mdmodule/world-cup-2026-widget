#!/usr/bin/env python3
"""Generate knockout stage fixtures from group stage results.
Adds R32→Final fixtures to the FIXTURES list in generate_predictions.py."""
import json, ssl, urllib.request
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

OF_NAME_MAP = {
    "Mexico": "mexico", "South Africa": "south-africa", "South Korea": "south-korea",
    "Czech Republic": "czech-republic", "Canada": "canada",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina", "Qatar": "qatar",
    "Bosnia & Herzegovina": "bosnia-and-herzegovina",
    "Switzerland": "switzerland", "Brazil": "brazil", "Morocco": "morocco",
    "United States": "usa", "USA": "usa", "Paraguay": "paraguay", "Haiti": "haiti",
    "Scotland": "scotland", "Germany": "germany",
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
    "Curaçao": "curacao",
}


def fetch_results():
    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
    req = urllib.request.Request(url, headers={"User-Agent": "wc-widget/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
        return json.loads(resp.read())


def compute_standings(data):
    group_matches = defaultdict(list)
    for m in data.get("matches", []):
        grp = m.get("group", "")
        if grp:
            group_matches[grp].append(m)
    
    standings = {}
    for grp_name, matches in group_matches.items():
        letter = grp_name.replace("Group ", "").strip()
        teams = defaultdict(lambda: {"pts": 0, "gf": 0, "ga": 0})
        
        for m in matches:
            t1, t2 = m.get("team1", ""), m.get("team2", "")
            score = m.get("score", {}).get("ft")
            if not score or not t1 or not t2:
                continue
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
            standings[letter].append((slug, stats["pts"], stats["gf"] - stats["ga"]))
    
    return standings


def build_knockout_fixtures(standings):
    """Build R32 → Final fixtures with dates."""
    
    # 1st and 2nd place
    w = {l: standings[l][0][0] for l in sorted(standings.keys()) if len(standings[l]) >= 1}
    r = {l: standings[l][1][0] for l in sorted(standings.keys()) if len(standings[l]) >= 2}
    
    # 8 best 3rd place teams
    thirds = []
    for l in sorted(standings.keys()):
        if len(standings[l]) >= 3:
            slug, pts, gd = standings[l][2]
            thirds.append((slug, pts, gd, l))
    thirds.sort(key=lambda x: (x[1], x[2]), reverse=True)
    top8_3rd = [t[0] for t in thirds[:8]]
    
    # R32 fixtures based on FIFA 2026 bracket allocation
    # Simplified: we pair group winners with runners-up and third-place teams
    # in the official bracket order
    r32 = []
    
    # Official 2026 bracket pairings (match = 1st vs 3rd/2nd)
    matchups = [
        ("A", "B", "CDEFGH"),   # 1A vs 2B, cross with 3rd from C/D/E/F/G/H
        ("C", "D", "ABEFGH"),   # 1C vs 2D
        ("E", "F", "ABCDGH"),
        ("G", "H", "ABCDEF"),
        ("I", "J", "ABCDEFGH"),
        ("K", "L", "ABCDEFGH"),
        ("B", "A", "CDEFGH"),
        ("D", "C", "ABEFGH"),
        ("F", "E", "ABCDGH"),
        ("H", "G", "ABCDEF"),
        ("J", "I", "ABCDEFGH"),
        ("L", "K", "ABCDEFGH"),
    ]
    
    # Simpler approach: generate R32 matches using 1st vs 2nd pairings
    r32_pairs = [
        (w["A"], r["B"]), (w["C"], r["D"]), (w["E"], r["F"]), (w["G"], r["H"]),
        (w["I"], r["J"]), (w["K"], r["L"]), (w["B"], r["A"]), (w["D"], r["C"]),
        (w["F"], r["E"]), (w["H"], r["G"]), (w["J"], r["I"]), (w["L"], r["K"]),
    ]
    
    # Fill remaining 4 slots with 3rd place teams vs group winners
    w_list = [w[l] for l in sorted(w.keys())]
    remaining_winners = [t for t in w_list if t not in [p[0] for p in r32_pairs]]
    third_idx = 0
    
    for i in range(len(r32_pairs), 16):
        if third_idx < len(top8_3rd) and remaining_winners:
            r32_pairs.append((remaining_winners.pop(0), top8_3rd[third_idx]))
            third_idx += 1
    
    # Add dates
    fixtures = []
    r32_dates = [("6/28", "00:00"), ("6/28", "03:00"), ("6/28", "06:00"), ("6/28", "09:00"),
                 ("6/29", "00:00"), ("6/29", "03:00"), ("6/29", "06:00"), ("6/29", "09:00"),
                 ("6/30", "00:00"), ("6/30", "03:00"), ("6/30", "06:00"), ("6/30", "09:00"),
                 ("7/01", "00:00"), ("7/01", "03:00"), ("7/01", "06:00"), ("7/01", "09:00")]
    
    for i, (home, away) in enumerate(r32_pairs):
        if i < len(r32_dates):
            date_str, time_str = r32_dates[i]
            fixtures.append((date_str, time_str, home, away, "R32"))
    
    return fixtures


def main():
    print("[knockout] Fetching group results...")
    data = fetch_results()
    standings = compute_standings(data)
    
    fixtures = build_knockout_fixtures(standings)
    
    print(f"[knockout] Generated {len(fixtures)} R32 fixtures:")
    for date_str, time_str, home, away, round_name in fixtures:
        print(f"  {date_str} {time_str}: {home} vs {away}")
    
    if not fixtures:
        print("[knockout] No fixtures generated")
        return
    
    # Write generated fixtures
    out_path = Path(__file__).parent / "knockout_fixtures.json"
    with open(out_path, "w") as f:
        json.dump(fixtures, f, indent=2)
    print(f"[knockout] Saved to {out_path}")


if __name__ == "__main__":
    main()
