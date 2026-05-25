#!/usr/bin/env python3
"""
Read /tmp/weight_raw.json (Withings API response) and merge new weight
entries into data/weight.json, deduplicating by date.
"""
import json
import os
from datetime import datetime, timezone

RAW_PATH = "/tmp/weight_raw.json"
OUT_PATH = "data/weight.json"


def load_raw():
    with open(RAW_PATH, "r") as f:
        return json.load(f)


def load_existing():
    try:
        with open(OUT_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": [], "last_updated": ""}


def parse_entries(data):
    """Extract weight measurements (meastype=1) from Withings measuregrps."""
    entries = []
    groups = data.get("body", {}).get("measuregrps", [])
    for g in groups:
        for m in g.get("measures", []):
            if m["type"] == 1:  # weight
                weight_kg = m["value"] * (10 ** m["unit"])
                date_str = datetime.fromtimestamp(
                    g["date"], tz=timezone.utc
                ).strftime("%Y-%m-%d")
                entries.append(
                    {
                        "date": date_str,
                        "weight_kg": round(weight_kg, 2),
                        "timestamp": g["date"],
                    }
                )
    return entries


def main():
    raw = load_raw()

    if raw.get("status") != 0:
        print(f"Withings API error — status: {raw.get('status')}")
        print(json.dumps(raw, indent=2))
        raise SystemExit(1)

    existing = load_existing()

    # Merge: existing entries keyed by date, new entries overwrite on same date
    merged = {e["date"]: e for e in existing.get("entries", [])}
    new_entries = parse_entries(raw)
    for e in new_entries:
        merged[e["date"]] = e

    result = {
        "entries": sorted(merged.values(), key=lambda x: x["date"], reverse=True),
        "last_updated": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved {len(result['entries'])} weight entries to {OUT_PATH}")


if __name__ == "__main__":
    main()
