"""
Kavach — Gig Delivery Fraud Detection Dataset Generator
Team GuideX | DEV Trails 2026

This script generates a realistic synthetic dataset for training a fraud detection
model on parametric weather payout claims made by gig delivery workers.

Real-world assumption: A fraudster sitting at home and spoofing their GPS location
cannot simultaneously fake their phone's accelerometer, barometric sensor, cell tower
association, and platform order history. Each of these signals is independent enough
that faking all of them at once is practically impossible for a Telegram-organised
syndicate using off-the-shelf GPS spoofing apps.

The dataset captures that asymmetry — genuine riders look consistent across all signals,
fraudsters look inconsistent in at least one or more of them.
"""

import numpy as np
import pandas as pd

# ─── Reproducibility ───────────────────────────────────────────────────────────
# Fixed seed so the dataset is reproducible across runs. Change this to get a
# different random split while keeping the same statistical properties.
SEED = 42
rng = np.random.default_rng(SEED)

TOTAL_ROWS = 10_000
BASE_FRAUD_RATE = 0.10       # 10% of total rows are fraud before pattern rules apply
EDGE_CASE_FRACTION = 0.05    # 5% of rows are extreme edge cases

n_edge = int(TOTAL_ROWS * EDGE_CASE_FRACTION)     # 500 edge case rows
n_main = TOTAL_ROWS - n_edge                       # 9500 standard rows


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def clip(arr):
    """
    All features are on a 0-100 scale. This ensures no value drifts outside
    that range after noise is added. Real sensor data always has physical bounds.
    """
    return np.clip(arr, 0, 100)


def add_noise(arr, scale=8.0):
    """
    Real-world sensor data is never perfectly clean. GPS has float error.
    Accelerometers have vibration noise. This adds ±5% Gaussian noise to every
    feature to reflect that. Scale=5.0 means noise std is 5 units on a 0-100 scale.
    """
    return arr + rng.normal(0, scale, size=arr.shape)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — GENERATE MAIN ROWS (9,500 rows)
# ══════════════════════════════════════════════════════════════════════════════

# ─── GPS Natural Travel (gps_natural_travel) ──────────────────────────────────
# Real assumption: a genuine rider has a traceable GPS route leading INTO the
# claimed zone over the 90 minutes before the alert. Their path shows road
# adherence, natural speed variation, and no sudden coordinate jumps.
# A spoofed GPS just teleports into the zone — no trajectory, no history.
# Base: uniform between 60 and 100 for the full population.
# We will reduce this for fraud cases in Section 3.

gps_base = rng.uniform(60, 100, n_main)

# ─── Cell Tower Match (cell_tower_match) ─────────────────────────────────────
# Real assumption: a device's registered cell tower cannot be faked without
# physical presence near that tower. GPS spoofing apps do not move the device —
# they only lie about its GPS coordinate. So a fraudster at home in Adyar
# claiming to be in Velachery will have a cell tower mismatch.
#
# Correlation with GPS: these two signals are positively correlated (r ≈ 0.7)
# because a genuine rider physically present in a zone will have both a real
# GPS trace and a matching cell tower. We model this by building cell_tower_match
# partly from gps_base plus independent variation.
#
# Formula: 0.7 * gps_base + 0.3 * independent_noise, then scaled.

cell_independent = rng.uniform(60, 100, n_main)
cell_tower_base = 0.7 * gps_base + 0.3 * cell_independent
# Rescale to 0-100 range after weighted combination
cell_tower_base = (cell_tower_base - cell_tower_base.min()) / \
                  (cell_tower_base.max() - cell_tower_base.min()) * 40 + 60

# ─── Accelerometer Active (accelerometer_active) ─────────────────────────────
# Real assumption: a rider on a scooter in active traffic produces continuous
# motion data — road vibration, braking, turning. A phone sitting on a table
# at home produces a flat line. We model genuine riders as high-activity (80-100)
# and will reduce this sharply for fraud pattern B.

accel_base = rng.uniform(70, 100, n_main)

# ─── Pressure Consistency (pressure_consistency) ─────────────────────────────
# Real assumption: every modern smartphone has a barometric pressure sensor.
# During a genuine storm event, the on-device reading should match the
# hyperlocal weather API reading for that zone within a calibrated delta.
# A phone indoors at home in clear weather shows stable indoor pressure —
# which will NOT match a storm zone's pressure reading.
# Genuine range: 70-100. We reduce for fraud.

pressure_base = rng.uniform(65, 100, n_main)

# ─── Work History Match (work_history_match) ─────────────────────────────────
# Real assumption: every registered rider has a delivery history. A worker who
# has never operated within 15km of the claimed zone in two years of activity
# appearing there during a red alert is a red flag.
# New riders (<1 month) get lower scores because they have less history to verify.
# We model this by sampling rider tenure and scoring accordingly.
#
# Tenure distribution: 60% experienced (>6 months), 40% newer (<6 months)

tenure_experienced = rng.uniform(70, 100, int(n_main * 0.60))
tenure_new = rng.uniform(20, 70, n_main - int(n_main * 0.60))
work_history_base = np.concatenate([tenure_experienced, tenure_new])
rng.shuffle(work_history_base)  # mix experienced and new riders randomly

# ─── No Active Order (no_active_order) ───────────────────────────────────────
# Real assumption: a rider claiming to be stranded cannot simultaneously have
# an open delivery order on the platform. High score = no active order (good).
# Low score = active order during claim (very suspicious).
# Genuine: 80-100. Fraud: 0-40.

no_order_base = rng.uniform(75, 100, n_main)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — FRAUD LABEL GENERATION FOR MAIN ROWS
# ══════════════════════════════════════════════════════════════════════════════

# We generate labels BEFORE adding noise so that pattern detection is clean.
# Noise is added after labelling to simulate real sensor imperfection.

is_fraud = np.zeros(n_main, dtype=int)

# ─── Pattern A: GPS Spoofing ──────────────────────────────────────────────────
# A fraudster using a GPS spoofing app shows a low natural travel score
# (no real trajectory) and a mismatched cell tower (not physically present).
# We mark 20% of rows as candidates for this pattern and apply 90% fraud rate.

pattern_a_mask = (gps_base < 50) & (cell_tower_base < 55)

# For rows matching Pattern A, override feature values to fraud-range
gps_base[pattern_a_mask] = rng.uniform(5, 30, pattern_a_mask.sum())
cell_tower_base[pattern_a_mask] = rng.uniform(0, 30, pattern_a_mask.sum())

# Apply 90% fraud rate to Pattern A rows
fraud_roll_a = rng.random(pattern_a_mask.sum()) < 0.70
is_fraud[pattern_a_mask] = fraud_roll_a.astype(int)

# ─── Pattern B: Fake Motion ───────────────────────────────────────────────────
# A phone sitting at home shows near-zero accelerometer activity and stable
# indoor pressure that does not match the storm zone reading.

pattern_b_mask = (accel_base < 50) & (pressure_base < 50)

accel_base[pattern_b_mask] = rng.uniform(5, 30, pattern_b_mask.sum())
pressure_base[pattern_b_mask] = rng.uniform(10, 40, pattern_b_mask.sum())

fraud_roll_b = rng.random(pattern_b_mask.sum()) < 0.60
is_fraud[pattern_b_mask] = np.maximum(
    is_fraud[pattern_b_mask], fraud_roll_b.astype(int)
)

# ─── Pattern C: New Rider Fraud ───────────────────────────────────────────────
# Fraudsters often create fresh accounts to avoid detection. A new rider
# with very little work history who has no active order is suspicious because
# experienced riders usually have orders even on slow days.
# Counterintuitively, no_active_order > 70 here means they never had orders —
# not that they are stranded. Context matters.

pattern_c_mask = (work_history_base < 40) & (no_order_base > 75)

work_history_base[pattern_c_mask] = rng.uniform(5, 35, pattern_c_mask.sum())

fraud_roll_c = rng.random(pattern_c_mask.sum()) < 0.50
is_fraud[pattern_c_mask] = np.maximum(
    is_fraud[pattern_c_mask], fraud_roll_c.astype(int)
)

# ─── Genuine Pattern: All signals strong ─────────────────────────────────────
# If all six features are above 70, the rider is almost certainly genuine.
# 95% genuine rate applied here.

genuine_mask = (
    (gps_base > 70) &
    (accel_base > 70) &
    (pressure_base > 70) &
    (cell_tower_base > 70) &
    (work_history_base > 70) &
    (no_order_base > 70)
)

# 5% fraud despite clean signals
fraud_roll_genuine = rng.random(genuine_mask.sum()) < 0.05
is_fraud[genuine_mask] = fraud_roll_genuine.astype(int)

# ─── Remaining rows: random label at 15% fraud rate ─────────────────────────
# Rows that did not hit any pattern and are not clearly genuine get a random
# label at a slightly elevated 15% fraud rate. This represents ambiguous cases
# the model will find hard to classify — a realistic property of real data.

remaining_mask = ~pattern_a_mask & ~pattern_b_mask & ~pattern_c_mask & ~genuine_mask
fraud_roll_remaining = rng.random(remaining_mask.sum()) < 0.15
is_fraud[remaining_mask] = fraud_roll_remaining.astype(int)

# ─── Adjust fraud labels to match fraud targets for non-pattern rows ─────────
# Override no_active_order for confirmed fraud rows to be low (has active order)
fraud_rows = is_fraud == 1
no_order_base[fraud_rows] = rng.uniform(0, 40, fraud_rows.sum())


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — ADD NOISE TO ALL MAIN FEATURES
# ══════════════════════════════════════════════════════════════════════════════

gps_final = clip(add_noise(gps_base))
accel_final = clip(add_noise(accel_base))
pressure_final = clip(add_noise(pressure_base))
cell_final = clip(add_noise(cell_tower_base))
work_final = clip(add_noise(work_history_base))
no_order_final = clip(add_noise(no_order_base))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — EDGE CASES (500 rows)
# ══════════════════════════════════════════════════════════════════════════════
# Real assumption: any robust model must handle extreme inputs without breaking.
# We generate two types of edge cases:
#   - All features < 20: extreme fraud signal. Label = fraud.
#   - All features > 90: extreme genuine signal. Label = genuine.
# Split 50/50 between the two types.

n_extreme_fraud = n_edge // 2       # 250 rows: everything broken
n_extreme_genuine = n_edge - n_extreme_fraud  # 250 rows: everything clean

# Extreme fraud edge cases
ef_gps = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_accel = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_pressure = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_cell = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_work = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_noorder = clip(add_noise(rng.uniform(2, 18,  n_extreme_fraud), scale=2))
ef_label = np.ones(n_extreme_fraud, dtype=int)

# Extreme genuine edge cases
eg_gps = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_accel = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_pressure = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_cell = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_work = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_noorder = clip(add_noise(rng.uniform(90, 99, n_extreme_genuine), scale=2))
eg_label = np.zeros(n_extreme_genuine, dtype=int)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — ASSEMBLE FINAL DATAFRAME
# ══════════════════════════════════════════════════════════════════════════════

main_df = pd.DataFrame({
    "gps_natural_travel":   gps_final,
    "accelerometer_active": accel_final,
    "pressure_consistency": pressure_final,
    "cell_tower_match":     cell_final,
    "work_history_match":   work_final,
    "no_active_order":      no_order_final,
    "is_fraud":             is_fraud,
})

edge_fraud_df = pd.DataFrame({
    "gps_natural_travel":   ef_gps,
    "accelerometer_active": ef_accel,
    "pressure_consistency": ef_pressure,
    "cell_tower_match":     ef_cell,
    "work_history_match":   ef_work,
    "no_active_order":      ef_noorder,
    "is_fraud":             ef_label,
})

edge_genuine_df = pd.DataFrame({
    "gps_natural_travel":   eg_gps,
    "accelerometer_active": eg_accel,
    "pressure_consistency": eg_pressure,
    "cell_tower_match":     eg_cell,
    "work_history_match":   eg_work,
    "no_active_order":      eg_noorder,
    "is_fraud":             eg_label,
})

df = pd.concat([main_df, edge_fraud_df, edge_genuine_df], ignore_index=True)

# Shuffle the final dataset so edge cases are not clustered at the end
df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

# Round all feature columns to 2 decimal places for clean CSV output
feature_cols = [
    "gps_natural_travel", "accelerometer_active", "pressure_consistency",
    "cell_tower_match", "work_history_match", "no_active_order"
]
df[feature_cols] = df[feature_cols].round(2)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — SAVE TO CSV
# ══════════════════════════════════════════════════════════════════════════════

output_path = "ml/fraud_data_realistic.csv"
df.to_csv(output_path, index=False)
print(f"Dataset saved to {output_path}\n")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — DIAGNOSTICS
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("CLASS DISTRIBUTION")
print("=" * 60)
counts = df["is_fraud"].value_counts().rename({0: "Genuine", 1: "Fraud"})
print(counts.to_string())
print(f"\nFraud rate: {df['is_fraud'].mean() * 100:.2f}%")

print("\n" + "=" * 60)
print("FEATURE CORRELATION MATRIX")
print("=" * 60)
corr = df[feature_cols].corr().round(3)
print(corr.to_string())

print("\n" + "=" * 60)
print("FIRST 10 ROWS")
print("=" * 60)
print(df.head(10).to_string(index=False))

print("\n" + "=" * 60)
print("FEATURE SUMMARY STATISTICS")
print("=" * 60)
print(df[feature_cols].describe().round(2).to_string())
