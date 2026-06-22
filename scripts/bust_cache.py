#!/usr/bin/env python3
"""Add cache-busting version strings to img src URLs in README.md.
Forces GitHub's camo proxy to fetch fresh SVGs instead of serving stale cache."""
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

README = Path(".github/../README.md").resolve()
TZ = timezone(timedelta(hours=8))

content = README.read_text(encoding="utf-8")
ts = datetime.now(TZ).strftime("%m%d%H%M")  # e.g. 06221350

# Replace .github/wc26/*.svg src with versioned URLs
# Pattern: src=".github/wc26/filename.svg" → src=".github/wc26/filename.svg?v=MmDDHHMM"
updated = re.sub(
    r'src="(\.github/wc26/[^"]+\.svg)"',
    rf'src="\1?v={ts}"',
    content
)

if updated != content:
    README.write_text(updated, encoding="utf-8")
    print(f"✓ Cache-busted README img URLs with v={ts}")
else:
    print("  No img src changes needed")
