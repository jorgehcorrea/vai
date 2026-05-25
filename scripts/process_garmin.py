#!/usr/bin/env python3
"""
Read /tmp/garmin_raw.json (30-day raw Garmin API responses) and produce:
  data/garmin.json         — today's snapshot (existing card structure)
  data/garmin_history.json — 30-day rolling history (runs, sleep, daily)
"""
import json
import os
from datetime import datetime, timezone

RAW_PATH     = "/tmp/garmin_raw.json"
SNAPSHOT_PATH = "data/garmin.json"
HISTORY_PATH  = "data/garmin_history.json"


# ── field extractors (unchanged from v1) ─────────────────────────────────────

def extract_user_summary(summary):
    if not summary:
        return {}
    return {
        "steps":                      summary.get("totalSteps"),
        "body_battery_charged":       summary.get("bodyBatteryChargedValue"),
        "body_battery_drained":       summary.get("bodyBatteryDrainedValue"),
        "body_battery_highest":       summary.get("bodyBatteryHighestValue"),
        "body_battery_lowest":        summary.get("bodyBatteryLowestValue"),
        "body_battery_most_recent":   summary.get("bodyBatteryMostRecentValue"),
        "stress_avg":                 summary.get("averageStressLevel"),
        "stress_max":                 summary.get("maxStressLevel"),
        "calories_active":            summary.get("activeKilocalories"),
        "calories_total":             summary.get("totalKilocalories"),
        "floors_ascended":            summary.get("floorsAscended"),
        "intensity_minutes_moderate": summary.get("moderateIntensityMinutes"),
        "intensity_minutes_vigorous": summary.get("vigorousIntensityMinutes"),
    }


def extract_sleep(sleep_data):
    if not sleep_data:
        return {}
    daily = sleep_data.get("dailySleepDTO") or {}
    scores = daily.get("sleepScores") or {}
    overall = scores.get("overall") or {}
    return {
        "duration_seconds":    daily.get("sleepTimeSeconds"),
        "score":               overall.get("value"),
        "deep_sleep_seconds":  daily.get("deepSleepSeconds"),
        "light_sleep_seconds": daily.get("lightSleepSeconds"),
        "rem_sleep_seconds":   daily.get("remSleepSeconds"),
        "awake_seconds":       daily.get("awakeSleepSeconds"),
        "start_time_gmt":      daily.get("sleepStartTimestampGMT"),
        "end_time_gmt":        daily.get("sleepEndTimestampGMT"),
    }


def extract_heart_rates(hr_data):
    if not hr_data:
        return {}
    return {
        "resting_hr":         hr_data.get("restingHeartRate"),
        "min_hr":             hr_data.get("minHeartRate"),
        "max_hr":             hr_data.get("maxHeartRate"),
        "last_7days_avg_rhr": hr_data.get("lastSevenDaysAvgRestingHeartRate"),
    }


def extract_hrv(hrv_data):
    if not hrv_data:
        return {}
    summary = hrv_data.get("hrvSummary") or {}
    baseline = summary.get("baseline") or {}
    return {
        "weekly_avg":              summary.get("weeklyAvg"),
        "last_night_avg":          summary.get("lastNight"),
        "last_night_5min_high":    summary.get("lastNight5MinHigh"),
        "baseline_low_upper":      baseline.get("lowUpper"),
        "baseline_balanced_low":   baseline.get("balancedLow"),
        "baseline_balanced_upper": baseline.get("balancedUpper"),
        "status":                  summary.get("status"),
    }


def extract_last_activity(activities):
    """Return the most recent activity entry from the range list."""
    if not activities:
        return {}
    for act in activities:
        if not act:
            continue
        act_type = act.get("activityType")
        type_key = act_type.get("typeKey") if isinstance(act_type, dict) else act_type
        duration = act.get("duration")
        return {
            "type":             type_key,
            "name":             act.get("activityName"),
            "distance_m":       act.get("distance"),
            "duration_seconds": int(duration) if duration is not None else None,
            "avg_hr":           act.get("averageHR"),
            "calories":         act.get("calories"),
            "start_time_local": act.get("startTimeLocal"),
        }
    return {}


# ── history builders ─────────────────────────────────────────────────────────

def _act_date(act):
    """Extract YYYY-MM-DD from an activity's startTimeLocal."""
    st = act.get("startTimeLocal") or ""
    return st[:10] if len(st) >= 10 else None


def _pace_min_km(duration_seconds, distance_m):
    """Average pace in minutes/km, rounded to 2 dp, or None."""
    if not duration_seconds or not distance_m:
        return None
    return round((duration_seconds / 60) / (distance_m / 1000), 2)


def build_runs_history(activities_range):
    """All activities, newest-first."""
    if not activities_range:
        return []
    runs = []
    for act in activities_range:
        if not act:
            continue
        act_type = act.get("activityType")
        type_key = act_type.get("typeKey") if isinstance(act_type, dict) else act_type
        distance_m = act.get("distance")
        duration_s = act.get("duration")
        duration_s = int(duration_s) if duration_s is not None else None
        runs.append({
            "date":             _act_date(act),
            "activity_type":    type_key,
            "distance_km":      round(distance_m / 1000, 2) if distance_m else None,
            "duration_seconds": duration_s,
            "avg_hr":           act.get("averageHR"),
            "avg_pace_min_km":  _pace_min_km(duration_s, distance_m),
            "calories":         act.get("calories"),
        })
    return sorted(runs, key=lambda r: r["date"] or "", reverse=True)


def build_sleep_history(daily, dates):
    """One entry per day that has sleep data, newest-first."""
    result = []
    for d in sorted(dates, reverse=True):
        day_data   = daily.get(d) or {}
        sleep_data = day_data.get("sleep_data")
        hrv_data   = day_data.get("hrv_data")
        if not sleep_data:
            continue
        sd      = sleep_data.get("dailySleepDTO") or {}
        scores  = sd.get("sleepScores") or {}
        overall = scores.get("overall") or {}
        hrv_sum = (hrv_data or {}).get("hrvSummary") or {}
        entry = {
            "date":                d,
            "duration_seconds":    sd.get("sleepTimeSeconds"),
            "score":               overall.get("value"),
            "deep_sleep_seconds":  sd.get("deepSleepSeconds"),
            "light_sleep_seconds": sd.get("lightSleepSeconds"),
            "rem_sleep_seconds":   sd.get("remSleepSeconds"),
            "awake_seconds":       sd.get("awakeSleepSeconds"),
            "hrv_weekly_average":  hrv_sum.get("weeklyAvg"),
        }
        if any(v is not None for k, v in entry.items() if k != "date"):
            result.append(entry)
    return result


def build_daily_history(daily, dates):
    """Steps, body battery, resting HR, stress — one entry per day with data, newest-first."""
    result = []
    for d in sorted(dates, reverse=True):
        day_data = daily.get(d) or {}
        us = day_data.get("user_summary") or {}
        hr = day_data.get("heart_rates") or {}
        steps      = us.get("totalSteps")
        bb_low     = us.get("bodyBatteryLowestValue")
        bb_high    = us.get("bodyBatteryHighestValue")
        resting_hr = hr.get("restingHeartRate")
        stress_avg = us.get("averageStressLevel")
        if any(v is not None for v in [steps, bb_low, bb_high, resting_hr, stress_avg]):
            result.append({
                "date":              d,
                "steps":             steps,
                "body_battery_low":  bb_low,
                "body_battery_high": bb_high,
                "resting_hr":        resting_hr,
                "stress_avg":        stress_avg,
            })
    return result


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    with open(RAW_PATH) as fh:
        raw = json.load(fh)

    today      = raw.get("date")
    daily      = raw.get("daily") or {}
    activities = raw.get("activities_range") or []
    dates      = sorted(daily.keys())
    now_str    = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    today_day  = daily.get(today) or {}

    # ── today's snapshot (data/garmin.json) ──────────────────────────────────
    snapshot = {
        "date":          today,
        "user_summary":  extract_user_summary(today_day.get("user_summary")),
        "sleep":         extract_sleep(today_day.get("sleep_data")),
        "heart_rate":    extract_heart_rates(today_day.get("heart_rates")),
        "last_activity": extract_last_activity(activities),
        "hrv":           extract_hrv(today_day.get("hrv_data")),
        "last_updated":  now_str,
    }

    # ── 30-day history (data/garmin_history.json) ─────────────────────────────
    runs  = build_runs_history(activities)
    sleep = build_sleep_history(daily, dates)
    daily_hist = build_daily_history(daily, dates)

    history = {
        "last_updated": now_str,
        "runs":         runs,
        "sleep":        sleep,
        "daily":        daily_hist,
    }

    os.makedirs("data", exist_ok=True)

    with open(SNAPSHOT_PATH, "w") as fh:
        json.dump(snapshot, fh, indent=2)
    print(f"Snapshot  → {SNAPSHOT_PATH}")

    with open(HISTORY_PATH, "w") as fh:
        json.dump(history, fh, indent=2)
    print(
        f"History   → {HISTORY_PATH}  "
        f"({len(runs)} activities, {len(sleep)} sleep days, {len(daily_hist)} daily records)"
    )


if __name__ == "__main__":
    main()
