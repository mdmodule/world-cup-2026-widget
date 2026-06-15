#!/usr/bin/env python3
"""Check openfootball worldcup data for group results used to fill bracket slots."""
import json, urllib.request, os

# Check local data first (from the cloned widget repo)
data_path = os.path.expanduser("~/world-cup-2026-readme-widget/data")
json_files = []
for root, dirs, files in os.walk(data_path):
    for f in files:
        if f.endswith('.json'):
            json_files.append(os.path.join(root, f))

for jf in sorted(json_files):
    print(f"=== {jf} ===")
    with open(jf, 'r') as f:
        d = json.load(f)
    
    for r in d.get('rounds', []):
        name = r.get('name', '?')
        matches = r.get('matches', [])
        has_scores = any(m.get('score') or m.get('score1') for m in matches)
        
        if 'Group' in name or 'group' in name.lower():
            for g in r.get('groups', []):
                gn = g.get('name', '?')
                standings = g.get('standings', g.get('teams', []))
                if standings:
                    print(f"  {gn}: {len(standings)} teams, has_standings={bool(g.get('standings'))}")
                    for t in standings[:3]:
                        code = t.get('team', {}).get('code', t.get('code', '?'))
                        pts = t.get('pts', '?')
                        print(f"    {code} pts={pts}")
        elif has_scores:
            print(f"  {name}: {len(matches)} matches, has scores")
            for m in matches[:2]:
                t1 = m.get('team1', {}).get('code', '?')
                t2 = m.get('team2', {}).get('code', '?')
                s = m.get('score', m.get('score1', '?'))
                print(f"    {t1} vs {t2} = {s}")
