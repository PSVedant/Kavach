import random
import datetime
import json
from datetime import timezone

# Weather patterns per city (monthly probability of severe event)
# Format: {city: {1-12: probability}}
CITY_WEATHER_RISK = {
    "chennai": {6: 0.3, 7: 0.4, 8: 0.35, 9: 0.2, 10: 0.25, 11: 0.5, 12: 0.4},
    "mumbai": {6: 0.4, 7: 0.6, 8: 0.5, 9: 0.3},
    "kolkata": {5: 0.2, 6: 0.5, 7: 0.6, 8: 0.5, 9: 0.3, 10: 0.2},
    "bangalore": {8: 0.2, 9: 0.25, 10: 0.2},
    "default": {1:0.05,2:0.05,3:0.05,4:0.05,5:0.1,6:0.15,7:0.15,8:0.15,9:0.1,10:0.05,11:0.05,12:0.05}
}

def get_monthly_risk(city):
    """Returns the probability of severe weather for current month."""
    current_month = datetime.datetime.now().month
    risks = CITY_WEATHER_RISK.get(city.lower(), CITY_WEATHER_RISK["default"])
    return risks.get(current_month, 0.1)  # default 10% if month not listed

def check_alert(city, zone_id):
    """
    Simulates real‑time weather alert cross‑validation.
    - Uses monthly risk probabilities for the city.
    - Coastal zones (e.g., MA13, MA14) have higher baseline risk.
    - Random but statistically consistent with real weather patterns.
    """
    # Determine zone type
    coastal_zones = ["MA13", "MA14", "CO01", "CO02"]
    is_coastal = zone_id in coastal_zones
    
    # Base probability from city's monthly risk
    base_prob = get_monthly_risk(city)
    
    # Boost for coastal zones
    if is_coastal:
        base_prob = min(base_prob * 1.5, 0.9)
    
    # Random chance of alert
    alert_happens = random.random() < base_prob
    
    if not alert_happens:
        return {
            "alert_confirmed": False,
            "confidence": round(random.uniform(0, 0.4), 2),
            "triggered_zones": [],
            "sources": {"imd": False, "skymet": False, "dma": False},
            "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "reason": "No severe weather predicted this month"
        }
    
    # If alert happens, simulate source agreement (more realistic)
    # IMD is most reliable, Skymet good, DMA variable
    imd_agrees = random.random() < 0.95
    skymet_agrees = random.random() < 0.85
    dma_agrees = random.random() < 0.75
    
    sources = {
        "imd": imd_agrees,
        "skymet": skymet_agrees,
        "dma": dma_agrees
    }
    
    # Alert confirmed if at least 2 of 3 agree (consensus)
    consensus = sum(sources.values()) >= 2
    confidence = sum(sources.values()) / 3.0
    
    triggered = []
    if consensus:
        # Determine which zones are affected (simulate spreading)
        if is_coastal:
            triggered = [zone_id] + (coastal_zones if random.random() < 0.6 else [])
        else:
            triggered = [zone_id]
    
    return {
        "alert_confirmed": consensus,
        "confidence": round(confidence, 2),
        "triggered_zones": triggered,
        "sources": sources,
        "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "base_probability": round(base_prob, 2)
    }

def main():
    print("=== Chennai Coastal Zone (MA13) – current month ===")
    for _ in range(3):  # show 3 runs to see variability
        result = check_alert("Chennai", "MA13")
        print(json.dumps(result, indent=2))
        print("-" * 50)
    
    print("\n=== Bangalore Inland Zone (BLR01) – 3 runs ===")
    for _ in range(3):
        result = check_alert("Bangalore", "BLR01")
        print(json.dumps(result, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    main()