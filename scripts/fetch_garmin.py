#!/usr/bin/env python3
"""
Read Garmin tokens from /tmp/garmin_tokens.json, authenticate via
api.client.loads(), fetch 30 days of health data from all endpoints,
and save all raw API responses to /tmp/garmin_raw.json.

Structure saved:
  {
    "date":             "YYYY-MM-DD",   # today
    "start_date":       "YYYY-MM-DD",   # today - 30 days
    "activities_range": [...],          # get_activities_by_date (one call)
    "daily": {
      "YYYY-MM-DD": {
        "user_summary": {...},
        "sleep_data":   {...},
        "heart_rates":  {...},
        "hrv_data":     {...}
      },
      ...                               # one entry per day
    }
  }
"""
import json
import sys
import time
from datetime import date, timedelta

import garminconnect

TOKEN_PATH   = "/tmp/garmin_tokens.json"
RAW_PATH     = "/tmp/garmin_raw.json"
LOOKBACK     = 30    # days
RATE_DELAY   = 0.4   # seconds between per-day calls to avoid rate-limiting


def fetch(label, fn, *args):
    """Call a Garmin API function, print result, never raise."""
    try:
        result = fn(*args)
        print(f"  OK  {label}")
        return result
    except Exception as exc:
        print(f"  ERR {label}: {exc}", file=sys.stderr)
        return None


def date_range(start: date, end: date):
    """Yield ISO date strings from start to end inclusive."""
    d = start
    while d <= end:
        yield d.isoformat()
        d += timedelta(days=1)


def main():
    today     = date.today()
    start     = today - timedelta(days=LOOKBACK)
    today_str = today.isoformat()
    start_str = start.isoformat()

    print(f"Fetching Garmin data {start_str} → {today_str} ({LOOKBACK + 1} days)")

    with open(TOKEN_PATH) as fh:
        token_content = fh.read()

    api = garminconnect.Garmin()
    api.client.loads(token_content)

    # ── Single range call for all activities ──────────────────────────────────
    print("Fetching activity range...")
    activities_range = fetch(
        f"activities_range ({start_str}→{today_str})",
        api.get_activities_by_date,
        start_str,
        today_str,
    )

    # ── Per-day calls ─────────────────────────────────────────────────────────
    daily = {}
    days = list(date_range(start, today))
    print(f"Fetching per-day data for {len(days)} days...")

    for i, day_str in enumerate(days, 1):
        print(f"  Day {i:02}/{len(days)}  {day_str}")
        daily[day_str] = {
            "user_summary": fetch(f"user_summary", api.get_user_summary,  day_str),
            "sleep_data":   fetch(f"sleep_data",   api.get_sleep_data,    day_str),
            "heart_rates":  fetch(f"heart_rates",  api.get_heart_rates,   day_str),
            "hrv_data":     fetch(f"hrv_data",     api.get_hrv_data,      day_str),
        }
        if i < len(days):
            time.sleep(RATE_DELAY)

    raw = {
        "date":             today_str,
        "start_date":       start_str,
        "activities_range": activities_range,
        "daily":            daily,
    }

    with open(RAW_PATH, "w") as fh:
        json.dump(raw, fh)

    n_act = len(activities_range) if activities_range else 0
    print(f"Raw data saved to {RAW_PATH}  ({len(daily)} days, {n_act} activities)")


if __name__ == "__main__":
    main()
