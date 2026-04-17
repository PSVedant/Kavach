"""
weather_engine.py – Kavach Parametric Insurance
Real weather alerts via OpenWeatherMap API.
Fallback to random simulation if API key is missing or call fails.
"""

import os
import random
import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[WARNING] 'requests' library not installed. Run: pip install requests")

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env file from current directory
except ImportError:
    print("[WARNING] 'python-dotenv' not installed. Run: pip install python-dotenv")
    print("[WARNING] Falling back to os.environ only.")

# ---------------------------------------------------------------------------
# Alert condition mapping (OpenWeatherMap "main" weather field)
# ---------------------------------------------------------------------------
ALERT_CONDITIONS = {"Rain", "Thunderstorm", "Drizzle", "Cyclone"}


def _simulate_fallback(zone_id: str) -> dict:
    """Original random-based simulation used as a fallback."""
    alert_confirmed = random.random() < 0.3
    return {
        "alert_confirmed": alert_confirmed,
        "confidence": round(random.uniform(0.6, 0.95), 2) if alert_confirmed else round(random.uniform(0.05, 0.25), 2),
        "triggered_zones": [zone_id] if alert_confirmed else [],
        "sources": {
            "imd_api": False,
            "satellite": False,
            "ground_sensors": False,
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "note": "SIMULATED – fallback mode (no API key or request failed)",
    }


def check_alert(city: str, zone_id: str) -> dict:
    """
    Check weather alert for a city/zone.

    Parameters
    ----------
    city    : City name understood by OpenWeatherMap (e.g. "Chennai")
    zone_id : Internal zone identifier (e.g. "MA13")

    Returns
    -------
    dict with keys:
        alert_confirmed  – bool
        confidence       – float 0-1
        triggered_zones  – list of zone_id strings
        sources          – dict of bool flags
        timestamp        – ISO-8601 UTC string
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        print(f"[WARNING] OPENWEATHER_API_KEY not set. Using random simulation for zone {zone_id}.")
        return _simulate_fallback(zone_id)

    if not REQUESTS_AVAILABLE:
        print("[WARNING] 'requests' not available. Using random simulation.")
        return _simulate_fallback(zone_id)

    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather_main = data["weather"][0]["main"]  # e.g. "Rain", "Clear"
        alert_confirmed = weather_main in ALERT_CONDITIONS

        print(f"[OpenWeatherMap] City: {city} | Condition: {weather_main} | Alert: {alert_confirmed}")

        return {
            "alert_confirmed": alert_confirmed,
            "confidence": 0.9 if alert_confirmed else 0.2,
            "triggered_zones": [zone_id] if alert_confirmed else [],
            "sources": {
                "imd_api": False,
                "satellite": False,
                "ground_sensors": False,
            },
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "weather_condition": weather_main,
        }

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Network error reaching OpenWeatherMap. Falling back to simulation.")
    except requests.exceptions.Timeout:
        print(f"[ERROR] OpenWeatherMap API timed out. Falling back to simulation.")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP error from OpenWeatherMap: {e}. Falling back to simulation.")
    except (KeyError, IndexError, ValueError) as e:
        print(f"[ERROR] Unexpected API response format: {e}. Falling back to simulation.")

    return _simulate_fallback(zone_id)


# ---------------------------------------------------------------------------
# Demo / manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        ("Chennai", "MA13"),
        ("Bengaluru", "BLR01"),
        ("Mumbai", "MA14"),
        ("Coimbatore", "CO01"),
    ]

    print("=" * 55)
    print("Kavach – Weather Alert Engine")
    print("=" * 55)

    for city, zone in test_cases:
        result = check_alert(city, zone)
        status = "⚠️  ALERT" if result["alert_confirmed"] else "✅  CLEAR"
        print(f"\n{status}  |  Zone: {zone}  |  City: {city}")
        print(f"  Confidence     : {result['confidence']}")
        print(f"  Triggered zones: {result['triggered_zones']}")
        if "weather_condition" in result:
            print(f"  OWM Condition  : {result['weather_condition']}")
        print(f"  Timestamp      : {result['timestamp']}")
