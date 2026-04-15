from fastapi import FastAPI
from backend.fraud_scoring import compute_trust_score

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Kavach API running"}

@app.post("/fraud-score")
def fraud_score(signals: dict):
    return compute_trust_score(signals)