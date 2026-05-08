"""
garmin_fetch.py
Scarica tutto il necessario da Garmin Connect per analisi allenamento e progressi.

Output: data/garmin_snapshot.json

Uso:
    python garmin_fetch.py                  # ultimi 30 giorni
    python garmin_fetch.py --days 60        # ultimi 60 giorni
"""

import os
import json
import argparse
from datetime import date, timedelta
from pathlib import Path
from getpass import getpass

from garminconnect import Garmin
from dotenv import load_dotenv

# ── credenziali ───────────────────────────────────────────────────────────────
# Crea un file .env nella root del repo con:
#   GARMIN_EMAIL=tua@email.com
#   GARMIN_PASSWORD=tuapassword
load_dotenv()


def get_client() -> Garmin:
    email = os.getenv("GARMIN_EMAIL") or input("Garmin email: ")
    password = os.getenv("GARMIN_PASSWORD") or getpass("Garmin password: ")
    client = Garmin(email, password)
    client.login()
    print(f"✓ Login OK — {client.get_full_name()}")
    return client


# ── attività ──────────────────────────────────────────────────────────────────

def fetch_activities(client: Garmin, days: int) -> list[dict]:
    start = (date.today() - timedelta(days=days)).isoformat()
    end = date.today().isoformat()
    raw = client.get_activities_by_date(start, end)
    result = []
    for a in raw:
        result.append({
            "activity_id":               a.get("activityId"),
            "date":                      a.get("startTimeLocal", "")[:10],
            "type":                      a.get("activityType", {}).get("typeKey"),
            "name":                      a.get("activityName"),
            "distance_km":               round((a.get("distance") or 0) / 1000, 2),
            "duration_min":              round((a.get("duration") or 0) / 60, 1),
            "avg_pace_min_km":           _pace(a.get("averageSpeed")),
            "avg_hr":                    a.get("averageHR"),
            "max_hr":                    a.get("maxHR"),
            "calories":                  a.get("calories"),
            "aerobic_training_effect":   a.get("aerobicTrainingEffect"),
            "anaerobic_training_effect": a.get("anaerobicTrainingEffect"),
            "vo2max":                    a.get("vO2MaxValue"),
            "training_stress_score":     a.get("trainingStressScore"),
            "avg_cadence_spm":           _cadence(a.get("averageRunningCadenceInStepsPerMinute")),
            "max_cadence_spm":           _cadence(a.get("maxRunningCadenceInStepsPerMinute")),
            "avg_stride_length_m":       a.get("avgStrideLength"),
        })
    return result


def fetch_splits(client: Garmin, activities: list[dict]) -> list[dict]:
    """Splits km-per-km per ogni attività di corsa."""
    result = []
    running_ids = [
        a["activity_id"] for a in activities
        if a.get("type") in ("running", "trail_running", "treadmill_running")
        and a.get("activity_id")
    ]
    for act_id in running_ids:
        try:
            details = client.get_activity_splits(act_id)
            laps = details.get("lapDTOs") or details.get("laps") or []
            splits = []
            for lap in laps:
                splits.append({
                    "lap":              lap.get("lapIndex"),
                    "distance_km":      round((lap.get("distance") or 0) / 1000, 2),
                    "duration_min":     round((lap.get("duration") or 0) / 60, 2),
                    "pace":             _pace(lap.get("averageSpeed")),
                    "avg_hr":           lap.get("averageHR"),
                    "avg_cadence_spm":  _cadence(lap.get("averageRunCadence")),
                    "elevation_gain_m": lap.get("elevationGain"),
                })
            result.append({"activity_id": act_id, "splits": splits})
        except Exception as e:
            result.append({"activity_id": act_id, "error": str(e)})
    return result


# ── metriche giornaliere ──────────────────────────────────────────────────────

def fetch_resting_hr(client: Garmin, days: int) -> list[dict]:
    result = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            raw = client.get_rhr_day(d)
            rhr = (
                raw.get("allMetrics", {})
                   .get("metricsMap", {})
                   .get("WELLNESS_RESTING_HEART_RATE", [{}])[0]
                   .get("value")
            )
        except Exception:
            rhr = None
        result.append({"date": d, "resting_hr": rhr})
    return result


def fetch_body_battery(client: Garmin, days: int) -> list[dict]:
    result = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            bb = client.get_body_battery(d) or []
            result.append({
                "date":    d,
                "charged": max((x.get("charged", 0) for x in bb), default=None),
                "drained": min((x.get("drained", 0) for x in bb), default=None),
            })
        except Exception:
            result.append({"date": d, "charged": None, "drained": None})
    return result


def fetch_sleep(client: Garmin, days: int) -> list[dict]:
    result = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            s = client.get_sleep_data(d)
            daily = s.get("dailySleepDTO", {})
            result.append({
                "date":             d,
                "sleep_duration_h": round((daily.get("sleepTimeSeconds") or 0) / 3600, 2),
                "deep_sleep_min":   round((daily.get("deepSleepSeconds") or 0) / 60, 1),
                "light_sleep_min":  round((daily.get("lightSleepSeconds") or 0) / 60, 1),
                "rem_sleep_min":    round((daily.get("remSleepSeconds") or 0) / 60, 1),
                "awake_min":        round((daily.get("awakeSleepSeconds") or 0) / 60, 1),
                "sleep_score":      daily.get("sleepScores", {}).get("overall", {}).get("value"),
                "hrv_weekly_avg":   s.get("hrvSummary", {}).get("weeklyAvg"),
                "hrv_last_night":   s.get("hrvSummary", {}).get("lastNight"),
            })
        except Exception:
            result.append({"date": d, "sleep_duration_h": None})
    return result


def fetch_stress(client: Garmin, days: int) -> list[dict]:
    result = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            s = client.get_stress_data(d)
            result.append({
                "date":          d,
                "avg_stress":    s.get("avgStressLevel"),
                "max_stress":    s.get("maxStressLevel"),
                "rest_stress":   s.get("restStressDuration"),
                "low_stress":    s.get("lowStressDuration"),
                "medium_stress": s.get("mediumStressDuration"),
                "high_stress":   s.get("highStressDuration"),
            })
        except Exception:
            result.append({"date": d, "avg_stress": None})
    return result


def fetch_steps(client: Garmin, days: int) -> list[dict]:
    result = []
    for i in range(days):
        d = (date.today() - timedelta(days=i)).isoformat()
        try:
            raw = client.get_steps_data(d)
            total = sum(x.get("steps", 0) for x in raw) if isinstance(raw, list) else 0
            result.append({"date": d, "steps": total})
        except Exception:
            result.append({"date": d, "steps": None})
    return result


# ── training ──────────────────────────────────────────────────────────────────

def fetch_training_status(client: Garmin) -> dict:
    today = date.today().isoformat()
    out = {}
    for key, fn in [
        ("status",    lambda: client.get_training_status(today)),
        ("readiness", lambda: client.get_training_readiness(today)),
    ]:
        try:
            out[key] = fn()
        except Exception as e:
            out[key] = {"error": str(e)}
    return out


def fetch_training_plan(client: Garmin, days_ahead: int = 30) -> list[dict]:
    """Workout pianificati (Garmin Coach / piano mezza maratona)."""
    result = []
    today = date.today()
    for i in range(-7, days_ahead):          # 7 giorni passati + N futuri
        d = (today + timedelta(days=i)).isoformat()
        try:
            workouts = client.get_workout_by_date(d)
            if not workouts:
                continue
            for w in (workouts if isinstance(workouts, list) else [workouts]):
                result.append({
                    "date":                   d,
                    "workout_id":             w.get("workoutId"),
                    "name":                   w.get("workoutName"),
                    "type":                   w.get("sportType", {}).get("sportTypeKey")
                                              if isinstance(w.get("sportType"), dict)
                                              else w.get("sportType"),
                    "estimated_duration_min": round((w.get("estimatedDurationInSecs") or 0) / 60, 1),
                    "estimated_distance_km":  round((w.get("estimatedDistanceInMeters") or 0) / 1000, 2),
                    "description":            w.get("description"),
                })
        except Exception:
            continue
    return result


def fetch_personal_records(client: Garmin) -> list[dict]:
    """Record personali per attività di corsa."""
    try:
        prs = client.get_personal_record()
        result = []
        for pr in (prs if isinstance(prs, list) else []):
            result.append({
                "activity_type": pr.get("activityType"),
                "distance":      pr.get("value"),
                "pr_type":       pr.get("prType"),
                "date":          pr.get("prStartTimeGmt", "")[:10],
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]


def fetch_fitness_age(client: Garmin) -> dict:
    try:
        return client.get_fitnessage_data(date.today().isoformat())
    except Exception as e:
        return {"error": str(e)}


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    days = args.days

    client = get_client()
    print()

    # Le attività vanno prima — servono gli ID per i splits
    print("  → activities...", end=" ", flush=True)
    try:
        activities = fetch_activities(client, days)
        print(f"OK ({len(activities)} attività)")
    except Exception as e:
        activities = []
        print(f"ERRORE ({e})")

    steps_list = [
        ("splits",           lambda: fetch_splits(client, activities)),
        ("resting_hr",       lambda: fetch_resting_hr(client, days)),
        ("body_battery",     lambda: fetch_body_battery(client, days)),
        ("sleep",            lambda: fetch_sleep(client, days)),
        ("stress",           lambda: fetch_stress(client, days)),
        ("steps",            lambda: fetch_steps(client, days)),
        ("training_status",  lambda: fetch_training_status(client)),
        ("training_plan",    lambda: fetch_training_plan(client)),
        ("personal_records", lambda: fetch_personal_records(client)),
        ("fitness_age",      lambda: fetch_fitness_age(client)),
    ]

    snapshot = {
        "generated_at": date.today().isoformat(),
        "days":         days,
        "activities":   activities,
    }

    for name, fn in steps_list:
        print(f"  → {name}...", end=" ", flush=True)
        try:
            snapshot[name] = fn()
            print("OK")
        except Exception as e:
            snapshot[name] = {"error": str(e)}
            print(f"ERRORE ({e})")

    out = Path(__file__).parent / "data" / "garmin_snapshot.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Salvato in: {out}")


# ── util ──────────────────────────────────────────────────────────────────────

def _pace(speed_m_s) -> str | None:
    if not speed_m_s:
        return None
    s = int(1000 / speed_m_s)
    return f"{s // 60}:{s % 60:02d}"


def _cadence(raw) -> int | None:
    """Garmin a volte restituisce passi per minuto per un solo piede → x2."""
    if raw is None:
        return None
    return int(raw * 2) if raw < 120 else int(raw)


if __name__ == "__main__":
    main()
