import numpy as np
import joblib
import os
import random

# Paths (relative to project root)
MODEL_PATH = "ml/fraud_model.pkl"
FEATURES_PATH = "ml/feature_names.pkl"

model = None
feature_names = None

# Load the real ML model if it exists
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        feature_names = joblib.load(FEATURES_PATH)
        print("[INFO] Loaded real ML model (logistic regression) from", MODEL_PATH)
    else:
        print("[WARNING] No trained model found. Using fallback weighted average.")
except Exception as e:
    print("[ERROR] Could not load model:", e)
    print("[INFO] Falling back to weighted average.")

# Fallback (weighted average) – kept as safety net
WEIGHTS = {
    "gps_natural_travel": 0.25,
    "accelerometer_active": 0.20,
    "pressure_consistency": 0.15,
    "cell_tower_match": 0.15,
    "work_history_match": 0.15,
    "no_active_order": 0.10
}

def compute_trust_score_fallback(signals):
    
    score = sum(signals[k] * w for k, w in WEIGHTS.items())
    score = round(score, 1)
    tier = "auto" if score >= 75 else ("hold" if score >= 45 else "reject")
    tier_desc = {
        "auto": "Auto‑approved (low fraud risk)",
        "hold": "Hold for manual review (medium risk)",
        "reject": "Rejected / flagged for investigation (high risk)"
    }[tier]
    return {"score": score, "tier": tier, "tier_description": tier_desc}

def compute_trust_score_ml(signals):
    # Convert dict to array in correct feature order
    X = np.array([[signals[f] for f in feature_names]])
    fraud_prob = model.predict_proba(X)[0][1]

    trust_score = (1 - fraud_prob) * 100

    # 🚨 RULE-BASED CORRECTIONS (KEEP THESE)
    if signals["gps_natural_travel"] < 20:
        trust_score *= 0.3

    if signals["cell_tower_match"] < 20:
        trust_score *= 0.4

    if signals["accelerometer_active"] < 20:
        trust_score *= 0.6

    # 🔥 Prevent unrealistic extremes (nice improvement)
    trust_score = max(5, min(trust_score, 95))

    trust_score = round(trust_score, 1)

    tier = "auto" if trust_score >= 75 else ("hold" if trust_score >= 45 else "reject")

    tier_desc = {
        "auto": "Auto-approved (low fraud risk)",
        "hold": "Hold for manual review (medium risk)",
        "reject": "Rejected / flagged for investigation (high risk)"
    }[tier]

    # 🔥 EXPLAINABILITY (NEW PART)
    reason = []

    if signals["gps_natural_travel"] < 20:
        reason.append("Low GPS consistency")

    if signals["cell_tower_match"] < 20:
        reason.append("Cell tower mismatch")

    if signals["accelerometer_active"] < 20:
        reason.append("No motion detected")

    if signals["pressure_consistency"] < 30:
        reason.append("Pressure not matching storm zone")

    if signals["work_history_match"] < 30:
        reason.append("Unusual location for rider")

    if signals["no_active_order"] < 30:
        reason.append("Active order conflict detected")

    # If everything looks fine
    if not reason:
        reason.append("All signals consistent and normal")

    return {
        "score": trust_score,
        "tier": tier,
        "tier_description": tier_desc,
        "reason": ", ".join(reason)
    }
    
def compute_trust_score(signals):
    if model is not None:
        return compute_trust_score_ml(signals)
    else:
        return compute_trust_score_fallback(signals)

# Helper to generate random signals (for demo)
def generate_random_signals():
    return {k: random.randint(0, 100) for k in WEIGHTS.keys()}

def main():
    print("=" * 70)
    print("KAVACH FRAUD SCORING ENGINE")
    print("=" * 70)
    if model:
        print("✓ Using real logistic regression model (94.5% accuracy).\n")
    else:
        print("⚠️ Using fallback weighted average.\n")

    # Test with 5 random riders
    for i in range(5):
        signals = generate_random_signals()
        result = compute_trust_score(signals)
        print(f"Rider {i+1}: Trust Score = {result['score']} → {result['tier_description']}")
        print("   Signals:", signals)
        print("-" * 50)

    # Special scenarios (demonstrate extremes)
    print("\n" + "=" * 70)
    print("SPECIAL SCENARIO: GPS Spoof Attempt")
    print("=" * 70)
    spoof = {"gps_natural_travel": 10, "accelerometer_active": 15, "pressure_consistency": 20,
             "cell_tower_match": 5, "work_history_match": 30, "no_active_order": 80}
    result = compute_trust_score(spoof)
    print(f"Trust Score: {result['score']} → {result['tier_description']}")

    print("\n" + "=" * 70)
    print("SPECIAL SCENARIO: Genuine Stranded Rider")
    print("=" * 70)
    genuine = {"gps_natural_travel": 95, "accelerometer_active": 88, "pressure_consistency": 85,
               "cell_tower_match": 90, "work_history_match": 85, "no_active_order": 95}
    result = compute_trust_score(genuine)
    print(f"Trust Score: {result['score']} → {result['tier_description']}")

if __name__ == "__main__":
    main()
