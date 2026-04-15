import uuid
import hashlib
import random
import datetime
from datetime import timezone

def calculate_final_decision(trust_score, weather_severity, rider_history):
    """
    Determines payout outcome using a weighted combination of:
    - trust_score (0-100) from ML model
    - weather_severity (1-3: 1=moderate, 2=severe, 3=extreme)
    - rider_history (0-100: percentage of previous successful claims)
    Returns:
        status: 'approved', 'pending', or 'rejected'
        reason: human-readable explanation
    """
    trust_norm = trust_score / 100.0
    weather_bonus = {1:0.0, 2:0.05, 3:0.12}.get(weather_severity, 0.0)
    history_bonus = (rider_history / 100.0) * 0.1
    final_score = trust_norm + weather_bonus + history_bonus
    final_score = min(final_score, 1.0)
    
    # Random factor: ±8% (more noticeable)
    random_factor = random.uniform(-0.08, 0.08)
    final_score += random_factor
    final_score = max(0.0, min(1.0, final_score))
    
    if final_score >= 0.75:
        status = "approved"
        reason = f"High trust ({trust_score}) + weather severity {weather_severity} + good history ({rider_history}%)"
    elif final_score >= 0.45:
        status = "pending"
        reason = f"Moderate score ({final_score:.2f}) – requires manual review"
    else:
        status = "rejected"
        reason = f"Low final score ({final_score:.2f}) – insufficient trust or risky pattern"
    
    return status, reason, round(final_score, 3)

def process_payout(rider_id, trust_score, weather_severity, rider_history, amount=400):
    status, reason, final_score = calculate_final_decision(trust_score, weather_severity, rider_history)
    
    if status == "approved":
        upi_id = f"UPI{uuid.uuid4().hex[:16].upper()}"
    else:
        upi_id = "N/A"
    
    ledger_data = f"{rider_id}|{status}|{amount}|{final_score}|{datetime.datetime.now(timezone.utc).isoformat()}"
    ledger_hash = hashlib.sha256(ledger_data.encode()).hexdigest()
    
    return {
        "payout_id": str(uuid.uuid4()),
        "rider_id": rider_id,
        "trust_score": trust_score,
        "weather_severity": weather_severity,
        "rider_history": rider_history,
        "final_decision_score": final_score,
        "status": status.upper(),
        "reason": reason,
        "amount": amount,
        "upi_transaction_id": upi_id,
        "ledger_hash": ledger_hash,
        "timestamp": datetime.datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

def main():
    print("=" * 70)
    print("KAVACH PAYOUT ENGINE – RANDOMIZED SCENARIOS (each run is different)")
    print("=" * 70)
    
    # Generate 5 completely random riders each run
    for i in range(5):
        rider = f"RIDER_{random.randint(100,999)}"
        trust = random.randint(0, 100)          # random trust score
        severity = random.choice([1,2,3])       # random weather severity
        history = random.randint(0, 100)        # random rider history
        result = process_payout(rider, trust, severity, history)
        
        print(f"\nRider: {result['rider_id']}")
        print(f"Trust Score: {result['trust_score']}")
        print(f"Weather Severity: {result['weather_severity']} (1=moderate,2=severe,3=extreme)")
        print(f"Rider History (past success %): {result['rider_history']}%")
        print(f"Final Decision Score: {result['final_decision_score']}")
        print(f"Status: {result['status']}")
        print(f"Reason: {result['reason']}")
        if result['status'] == "APPROVED":
            print(f"UPI Transaction ID: {result['upi_transaction_id']}")
        print(f"Ledger Hash: {result['ledger_hash'][:48]}...")
        print("-" * 50)

if __name__ == "__main__":
    main()