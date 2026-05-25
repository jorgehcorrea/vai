#!/usr/bin/env python3
"""
Read /tmp/garmin_raw.json (raw Garmin API responses) and extract the
relevant health fields, saving clean JSON to data/garmin.json.
"""
import json
import os
from datetime import datetime, timezone

RAW_PATH = "/tmp/garmin_raw.json"
OUT_PATH = "data/garmin.json"


# ── field extractors ──────────────────────────────────────────────────────────

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


def extract_last_activity(activities):
    if not activities:
        return {}
    act = activities[0] if isinstance(activities, list) and activities else {}
    if not act:
        return {}
    act_type = act.get("activityType")
    type_key = (
        act_type.get("typeKey") if isinstance(act_type, dict) else act_type
    )
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


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    with open(RAW_PATH) as fh:
        raw = json.load(fh)

    result = {
        "date":          raw.get("date"),
        "user_summary":  extract_user_summary(raw.get("user_summary")),
        "sleep":         extract_sleep(raw.get("sleep_data")),
        "heart_rate":    extract_heart_rates(raw.get("heart_rates")),
        "last_activity": extract_last_activity(raw.get("activities")),
        "hrv":           extract_hrv(raw.get("hrv_data")),
        "last_updated":  datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(result, fh, indent=2)

    print(f"Garmin data saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
