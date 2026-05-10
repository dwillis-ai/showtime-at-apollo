#!/usr/bin/env python3
"""
bundle.py — Bake data.json into exec_dashboard.html to produce a single portable file.

Usage:
    python3 bundle.py                     # outputs exec_dashboard_YYYY-MM-DD.html
    python3 bundle.py --out snapshot.html # custom output path
"""
import json
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent

FETCH_LINE = (
    "const data = await fetch('data.json?t=' + Date.now())"
    ".then(r => { if (!r.ok) throw new Error('Failed'); return r.json(); });"
)
BUNDLED_LINE = "const data = window.__BUNDLED_DATA__;"

REFRESH_BTN_OLD = (
    '<button class="btn-refresh" id="refreshBtn" onclick="refreshData()">'
)
REFRESH_BTN_NEW = (
    '<button class="btn-refresh" id="refreshBtn" onclick="refreshData()" '
    'title="Bundled snapshot — re-renders from embedded data" '
    'style="opacity:0.7;cursor:default;">'
)

REFRESH_LABEL_OLD = "Refresh Data"
REFRESH_LABEL_NEW = "Snapshot"


def main():
    out_arg = None
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        out_arg = sys.argv[idx + 1]

    data_path = BASE / "data.json"
    html_path = BASE / "exec_dashboard.html"

    if not data_path.exists():
        print("ERROR: data.json not found", file=sys.stderr)
        sys.exit(1)
    if not html_path.exists():
        print("ERROR: exec_dashboard.html not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(data_path.read_text())
    html = html_path.read_text()

    # 1. Inject bundled data before </head>
    data_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    injection = f"<script>window.__BUNDLED_DATA__ = {data_json};</script>"
    if "</head>" not in html:
        print("ERROR: </head> not found in exec_dashboard.html", file=sys.stderr)
        sys.exit(1)
    html = html.replace("</head>", f"{injection}\n</head>", 1)

    # 2. Replace fetch with direct data reference
    if FETCH_LINE not in html:
        print("ERROR: fetch pattern not found — exec_dashboard.html may have changed",
              file=sys.stderr)
        sys.exit(1)
    html = html.replace(FETCH_LINE, BUNDLED_LINE, 1)

    # 3. Update the refresh button to communicate snapshot state
    html = html.replace(REFRESH_BTN_OLD, REFRESH_BTN_NEW, 1)
    html = html.replace(REFRESH_LABEL_OLD, REFRESH_LABEL_NEW, 1)

    # 4. Write output
    fetched = data.get("lastFetched", date.today().isoformat())
    out_name = out_arg or f"exec_dashboard_{fetched}.html"
    out_path = BASE / out_name
    out_path.write_text(html)

    size_kb = len(html.encode()) / 1024
    print(f"Bundled → {out_path.name}")
    print(f"  Size:         {size_kb:,.1f} KB")
    print(f"  Data date:    {fetched}")
    print(f"  Bookings rows:{len(data.get('bookingsRows', []))}")
    print(f"  Inv rows:     {len(data.get('inventoryQ2', []))}")


if __name__ == "__main__":
    main()
