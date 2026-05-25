# vai 🏃

> *vai* — Italian for "go". Personal health and training dashboard.

Live: [jorgehcorrea.github.io/vai](https://jorgehcorrea.github.io/vai)

---

## What is this

A personal dashboard built to track training, weight, and wellness data in one place. No subscriptions, no third-party apps — just raw data from Garmin, Withings, and a morning alarm shortcut that opens this on wakeup.

---

## Pages

| File | URL | Purpose |
|---|---|---|
| `index.html` | `/vai/` | Morning dashboard — today's workout, race countdown, week strip |
| `microdosing.html` | `/vai/microdosing.html` | Fadiman protocol journal — mood, focus, energy, sleep tracking |

---

## Data

| File | Updated | Source |
|---|---|---|
| `data/weight.json` | Daily (GitHub Action) | Withings scale via API |

---

## Integrations

### Withings (weight)
OAuth2 connection to Withings Health API. A GitHub Action runs daily at 7am ECT and fetches the latest weight measurements, saving them to `data/weight.json`.

**Secrets required:**
- `WITHINGS_CLIENT_ID`
- `WITHINGS_CLIENT_SECRET`
- `WITHINGS_REFRESH_TOKEN`

### Garmin Connect (activities)
— In progress

### Strava (runs)
— Planned

---

## Training plan

4-week base building block targeting VO2max improvement and 5K race readiness.

**Schedule:** Mon / Wed / Sat / Sun running + Mon / Wed elliptical evenings

**Goal race:** Mini Quito 5K — Parque Bicentenario, June 6 2026

---

## Stack

- Pure HTML/CSS/JS — no framework, no build step
- GitHub Pages for hosting
- GitHub Actions for data pipeline
- Google Calendar for session scheduling
- iOS Shortcuts for morning alarm integration

---

## Local dev

Just open any `.html` file in a browser. No server needed.

```bash
open index.html
```

---

*Built with Claude — May 2026*
