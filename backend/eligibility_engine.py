"""
eligibility_engine.py — Kavach Rider Eligibility Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fully dynamic: every run generates a fresh, randomised rider database
(names, IDs, zones, shift states) so no two executions are identical.

Eligibility Rules (applied in order):
  1. VERIFIED      — rider_id must exist in the live database.
  2. ZONE MATCH    — rider's assigned zone must equal the triggered zone.
  3. SHIFT ACTIVE  — the real-time shift signal must be True.
  All three must pass for eligible = True.
"""

import random
import string
import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# Seed with current timestamp — different result on every execution
# ---------------------------------------------------------------------------
random.seed(datetime.now().timestamp())


# ---------------------------------------------------------------------------
# Procedural name / ID / zone generators  (zero hardcoded strings)
# ---------------------------------------------------------------------------

_CONSONANTS = "bdfghjklmnprstvwz"
_VOWELS     = "aeiou"


def _random_syllable() -> str:
    """Return one CV or CVC syllable built from random phoneme pools."""
    syl = random.choice(_CONSONANTS).upper() + random.choice(_VOWELS)
    if random.random() > 0.5:
        syl += random.choice(_CONSONANTS)
    return syl


def _random_name(syllable_count: int = 2) -> str:
    """Compose a plausible-sounding word from N random syllables."""
    return "".join(_random_syllable() for _ in range(syllable_count)).capitalize()


def _generate_full_name() -> str:
    """Generate a random first + last name pair."""
    first = _random_name(random.randint(2, 3))
    last  = _random_name(random.randint(2, 3))
    return f"{first} {last}"


def _generate_rider_id() -> str:
    """Return a short, collision-resistant ID like R-4A7F."""
    return "R-" + uuid.uuid4().hex[:4].upper()


def _generate_zone_id() -> str:
    """Return a random zone label like ZN-7K."""
    letter = random.choice(string.ascii_uppercase)
    digit  = random.randint(1, 9)
    return f"ZN-{digit}{letter}"


# ---------------------------------------------------------------------------
# Database generator
# ---------------------------------------------------------------------------

def build_rider_db(n: int = 5):
    """
    Build a fresh rider database with `n` unique entries each run.

    Returns
    -------
    db        : dict  { rider_id -> {name, home_zone, shift_on} }
    zone_pool : list  of all zone IDs used in this session
    """
    # Fewer unique zones than riders so clashes (and interesting cases) occur
    zone_pool = [_generate_zone_id() for _ in range(max(2, n - 1))]

    db       = {}
    used_ids = set()

    for _ in range(n):
        rider_id = _generate_rider_id()
        while rider_id in used_ids:          # guarantee uniqueness
            rider_id = _generate_rider_id()
        used_ids.add(rider_id)

        db[rider_id] = {
            "name":      _generate_full_name(),
            "home_zone": random.choice(zone_pool),
            "shift_on":  random.choice([True, False]),
        }

    return db, zone_pool


# ---------------------------------------------------------------------------
# Core eligibility function
# ---------------------------------------------------------------------------

def check_eligibility(
    rider_id: str,
    zone_id: str,
    shift_active: bool,
    db: dict,
) -> dict:
    """
    Evaluate Kavach eligibility for one rider against a live alert.

    Parameters
    ----------
    rider_id     : Dynamically generated rider identifier.
    zone_id      : Zone where the Kavach alert was triggered.
    shift_active : Real-time shift signal — True means rider is on duty now.
    db           : The live rider database for this session.

    Returns
    -------
    dict  { eligible, reason, rider_zone_match, shift_active, verified }
    """

    # ── Rule 1: Existence / verification ──────────────────────────────────
    if rider_id not in db:
        return {
            "eligible":         False,
            "reason":           f"Rider '{rider_id}' not found in system.",
            "rider_zone_match": False,
            "shift_active":     shift_active,
            "verified":         False,
        }

    rider    = db[rider_id]
    verified = True

    # ── Rule 2: Zone match ─────────────────────────────────────────────────
    # Rider may only respond to alerts from their assigned home zone.
    rider_zone_match = (rider["home_zone"] == zone_id)

    # ── Rule 3: Compose final eligibility decision ────────────────────────
    eligible = rider_zone_match and shift_active

    if eligible:
        reason = (
            f"{rider['name']} ({rider_id}) ELIGIBLE — "
            f"zone {zone_id} matches home zone and shift is active."
        )
    elif not rider_zone_match and not shift_active:
        reason = (
            f"{rider['name']} ({rider_id}) INELIGIBLE — "
            f"zone mismatch (home={rider['home_zone']}, alert={zone_id}) "
            f"AND shift is inactive."
        )
    elif not rider_zone_match:
        reason = (
            f"{rider['name']} ({rider_id}) INELIGIBLE — "
            f"zone mismatch (home={rider['home_zone']}, alert={zone_id})."
        )
    else:
        reason = (
            f"{rider['name']} ({rider_id}) INELIGIBLE — "
            f"zone matches but shift is inactive."
        )

    return {
        "eligible":         eligible,
        "reason":           reason,
        "rider_zone_match": rider_zone_match,
        "shift_active":     shift_active,
        "verified":         verified,
    }


# ---------------------------------------------------------------------------
# Scenario builder — derives test cases from the live DB, nothing assumed
# ---------------------------------------------------------------------------

def _build_test_cases(db: dict, zone_pool: list) -> list:
    """
    Construct three meaningful test cases directly from whatever database
    was generated this session.  No IDs, names or zones are assumed.

    Returns list of (label, rider_id, zone_id, shift_active) tuples.
    """
    riders = list(db.items())
    cases  = []

    # Case 1 — guaranteed ELIGIBLE
    # Pick any rider; use their exact home zone; force shift on.
    r1_id, r1 = random.choice(riders)
    cases.append((
        "Case 1 — Eligible (zone match + shift active)",
        r1_id,
        r1["home_zone"],   # exact match guaranteed
        True,
    ))

    # Case 2 — guaranteed ZONE MISMATCH
    # Pick a rider; select any zone that is NOT their home zone.
    r2_id, r2 = random.choice(riders)
    wrong_zones = [z for z in zone_pool if z != r2["home_zone"]]
    wrong_zone  = (random.choice(wrong_zones) if wrong_zones
                   else _generate_zone_id())   # edge-case: all zones collapsed
    cases.append((
        "Case 2 — Ineligible (zone mismatch)",
        r2_id,
        wrong_zone,
        True,    # shift is fine — zone is the only blocker
    ))

    # Case 3 — guaranteed SHIFT INACTIVE
    # Pick any rider; use their home zone (so zone passes); force shift off.
    r3_id, r3 = random.choice(riders)
    cases.append((
        "Case 3 — Ineligible (shift inactive)",
        r3_id,
        r3["home_zone"],   # zone matches — shift is the only blocker
        False,
    ))

    return cases


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

def _print_result(label: str, result: dict) -> None:
    bar = "─" * 64
    print(bar)
    print(f"  {label}")
    print(bar)
    for k, v in result.items():
        flag = ""
        if k == "eligible":
            flag = "  ✅" if v else "  ❌"
        print(f"  {k:<22}: {v}{flag}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 64)
    print("   KAVACH — Dynamic Eligibility Engine")
    print(f"   Session : {datetime.now().strftime('%Y-%m-%d  %H:%M:%S.%f')}")
    print("=" * 64)

    # Fresh random database — different every run
    db, zone_pool = build_rider_db(n=5)

    print("\n  [ Live Rider Database — generated this session ]\n")
    for rid, info in db.items():
        tag = "ON-SHIFT " if info["shift_on"] else "OFF-SHIFT"
        print(f"  {rid}  |  {info['name']:<24}  |  "
              f"Zone: {info['home_zone']}  |  {tag}")
    print()

    # Test cases derived entirely from the live DB
    test_cases = _build_test_cases(db, zone_pool)

    print("  [ Running Eligibility Checks ]\n")
    for label, rider_id, zone_id, shift_active in test_cases:
        result = check_eligibility(rider_id, zone_id, shift_active, db)
        _print_result(label, result)


if __name__ == "__main__":
    main()
