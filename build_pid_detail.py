#!/usr/bin/env python3
"""
build_pid_detail.py — Parse 12 per-product-line Omni query results into
pidDetailRows and merge them into data.json.

Expected inputs (written by the refresh-exec flow before this script runs):
  /tmp/pid_apollo_desktop.json
  /tmp/pid_apollo_rackmount.json
  /tmp/pid_volt_desktop.json
  /tmp/pid_modeling_mics.json
  /tmp/pid_aib.json
  /tmp/pid_analog.json
  /tmp/pid_gpm.json
  /tmp/pid_gps.json
  /tmp/pid_uad.json
  /tmp/pid_amp_top_box.json
  /tmp/pid_accessories.json
  /tmp/pid_analog_mics.json

Each file is a JSON array of Omni result rows (the `result` array from getData).
Field names expected per row:
  "Level Code"             → dealer
  "Product ID"             → productId
  "Booked (USD)"           → booked
  "Shipped USD"            → shipped
  "Open USD"               → open
  "Rebate Product Target"  → rebateTarget
"""
import json
from pathlib import Path

DATA_JSON = Path("/Users/dwillis/showtime-at-apollo/data.json")

PRODUCT_LINES = [
    ("Apollo Desktop",   "/tmp/pid_apollo_desktop.json"),
    ("Apollo Rackmount", "/tmp/pid_apollo_rackmount.json"),
    ("Volt Desktop",     "/tmp/pid_volt_desktop.json"),
    ("Modeling Mics",    "/tmp/pid_modeling_mics.json"),
    ("AIB",              "/tmp/pid_aib.json"),
    ("Analog",           "/tmp/pid_analog.json"),
    ("GPM",              "/tmp/pid_gpm.json"),
    ("GPS",              "/tmp/pid_gps.json"),
    ("UAD",              "/tmp/pid_uad.json"),
    ("Amp Top Box",      "/tmp/pid_amp_top_box.json"),
    ("Accessories",      "/tmp/pid_accessories.json"),
    ("Analog Mics",      "/tmp/pid_analog_mics.json"),
]


def load_rows(path):
    """Load Omni result rows from a temp file.

    Handles two formats:
    - Raw array: [{...}, ...]  (rows written directly)
    - Wrapped tool output: [{"type":"text","text":"<JSON string>"}]
    """
    content = Path(path).read_text().strip()
    parsed = json.loads(content)
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and "type" in parsed[0]:
        # Wrapped tool-output format
        inner = json.loads(parsed[0]["text"])
        return inner.get("result", [])
    # Plain array of rows
    return parsed


def parse_rows(rows, product_line):
    out = []
    for r in rows:
        dealer = (r.get("Level Code") or "").strip()
        pid    = (r.get("Product ID")  or "").strip()
        if not dealer or not pid:
            continue
        out.append({
            "dealer":       dealer,
            "productLine":  product_line,
            "productId":    pid,
            "booked":       round(float(r.get("Booked (USD)")          or 0), 2),
            "shipped":      round(float(r.get("Shipped USD")           or 0), 2),
            "open":         round(float(r.get("Open USD")              or 0), 2),
            "rebateTarget": round(float(r.get("Rebate Product Target") or 0), 2),
        })
    return out


def main():
    all_rows = []
    for product_line, path in PRODUCT_LINES:
        p = Path(path)
        if not p.exists():
            print(f"  MISSING: {path} — skipping {product_line}")
            continue
        rows = load_rows(path)
        parsed = parse_rows(rows, product_line)
        print(f"  {product_line}: {len(rows)} raw -> {len(parsed)} valid")
        all_rows.extend(parsed)

    print(f"\nTotal pidDetailRows: {len(all_rows)}")

    data = json.loads(DATA_JSON.read_text())
    data["pidDetailRows"] = all_rows
    DATA_JSON.write_text(json.dumps(data, separators=(",", ":")))
    print("data.json updated with pidDetailRows.")


if __name__ == "__main__":
    main()
