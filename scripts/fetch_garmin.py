#!/usr/bin/env python3
"""
Read Garmin tokens from /tmp/garmin_tokens.json, authenticate via
api.client.loads(), fetch today's health data from all endpoints,
and save the raw API responses to /tmp/garmin_raw.json.
"""
import json
import sys
from datetime import date

import garminconnect

TOKEN_PATH = "/tmp/garmin_tokens.json"
RAW_PATH = "/tmp/garmin_raw.json"


def fetch(label, fn, *args):
    """Call a Garmin API function, printing success/failure, never raising."""
    try:
        result = fn(*args)
        print(f"{label}: OK")
        return result
    except Exception as exc:
        print(f"{label}: ERROR — {exc}", file=sys.stderr)
        return None


def main():
    today = date.today().isoformat()
    print(f"Fetching Garmin data for {today}")

    with open(TOKEN_PATH) as fh:
        token_content = fh.read()

    api = garminconnect.Garmin()
    api.client.loads(token_content)

    raw = {
        "date": today,
        "user_summary": fetch("user_summary",    api.get_user_summary,       today),
        "sleep_data":   fetch("sleep_data",      api.get_sleep_data,         today),
        "heart_rates":  fetch("heart_rates",     api.get_heart_rates,        today),
        "activities":   fetch("activities",      api.get_activities_fordate, today),
        "hrv_data":     fetch("hrv_data",        api.get_hrv_data,           today),
    }

    with open(RAW_PATH, "w") as fh:
        json.dump(raw, fh)

    print(f"Raw data saved to {RAW_PATH}")


if __name__ == "__main__":
    main()
