#!/usr/bin/env python3
"""
CURB-65 Pneumonia Severity Calculator

Implements four clinical scoring systems for community-acquired pneumonia:
  1. CURB-65  (original, with urea/BUN)
  2. CRB-65   (no lab required — for outpatient / field use)
  3. PSI/PORT (Pneumonia Severity Index — simplified risk classes I-V)
  4. ATS/IDSA severe pneumonia criteria (major + minor)

References:
  - Lim WS et al. Thorax 2003;58:377-382
  - Fine MJ et al. NEJM 1997;336:243-250
  - Mandell LA et al. Clin Infect Dis 2007;44:S27-S72

This is a clinical decision SUPPORT tool. It does not replace clinical
judgment. Treatment decisions must consider the full clinical picture.
Stdlib only — no external dependencies.
"""

import math


# ---------------------------------------------------------------------------
# CURB-65 scoring
# ---------------------------------------------------------------------------

# Each criterion is worth 1 point. Total range: 0-5.
CURB65_CRITERIA = [
    "confusion",
    "urea_elevated",
    "respiratory_rate_high",
    "blood_pressure_low",
    "age_ge_65",
]

# 30-day mortality rates from Lim et al. 2003
CURB65_MORTALITY = {
    0: 0.7,
    1: 3.2,
    2: 13.0,
    3: 17.0,
    4: 42.0,
    5: 57.0,
}

# Management recommendations by score
CURB65_MANAGEMENT = {
    0: "Low severity. Consider outpatient treatment.",
    1: "Low severity. Consider outpatient treatment; assess social circumstances.",
    2: "Moderate severity. Consider short inpatient stay or supervised outpatient treatment.",
    3: "Severe pneumonia. Manage as severe; consider ICU admission.",
    4: "Severe pneumonia. Manage as severe; consider ICU admission.",
    5: "Severe pneumonia. Manage as severe; consider ICU admission.",
}


def score_curb65(confusion, urea_elevated, respiratory_rate_high,
                 blood_pressure_low, age_ge_65):
    """
    Calculate CURB-65 score.

    Parameters (all bool):
        confusion            – New-onset confusion (AMT < 8 or equivalent)
        urea_elevated        – Urea > 7 mmol/L  (BUN > 20 mg/dL)
        respiratory_rate_high – Respiratory rate >= 30 breaths/min
        blood_pressure_low   – Systolic < 90 mmHg OR diastolic <= 60 mmHg
        age_ge_65            – Age >= 65 years

    Returns dict with score, criteria met, mortality estimate, and management.
    """
    flags = {
        "confusion": bool(confusion),
        "urea_elevated": bool(urea_elevated),
        "respiratory_rate_high": bool(respiratory_rate_high),
        "blood_pressure_low": bool(blood_pressure_low),
        "age_ge_65": bool(age_ge_65),
    }
    score = sum(flags.values())
    return {
        "score": score,
        "criteria": flags,
        "mortality_pct": CURB65_MORTALITY[score],
        "management": CURB65_MANAGEMENT[score],
    }


# ---------------------------------------------------------------------------
# CRB-65 scoring  (same but without urea — for settings without lab access)
# ---------------------------------------------------------------------------

CRB65_MANAGEMENT = {
    0: "Low risk. Suitable for outpatient treatment.",
    1: "Low-moderate risk. Consider outpatient treatment with close follow-up.",
    2: "Moderate risk. Consider hospital admission or closely supervised outpatient.",
    3: "High risk. Urgent hospital admission; consider ICU.",
    4: "High risk. Urgent hospital admission; consider ICU.",
}


def score_crb65(confusion, respiratory_rate_high, blood_pressure_low, age_ge_65):
    """
    Calculate CRB-65 score (no urea/BUN required).

    Parameters (all bool):
        confusion             – New-onset confusion
        respiratory_rate_high – Respiratory rate >= 30 breaths/min
        blood_pressure_low    – Systolic < 90 mmHg OR diastolic <= 60 mmHg
        age_ge_65             – Age >= 65 years

    Returns dict with score (0-4), criteria met, and management.
    """
    flags = {
        "confusion": bool(confusion),
        "respiratory_rate_high": bool(respiratory_rate_high),
        "blood_pressure_low": bool(blood_pressure_low),
        "age_ge_65": bool(age_ge_65),
    }
    score = sum(flags.values())
    return {
        "score": score,
        "criteria": flags,
        "management": CRB65_MANAGEMENT[score],
    }


# ---------------------------------------------------------------------------
# PSI / PORT  (Pneumonia Severity Index — simplified risk classes)
# ---------------------------------------------------------------------------

# Simplified PSI point assignments.
# Full PSI uses ~20 variables; this captures the major contributors.
PSI_RISK_CLASS = {
    "I":   {"max_score": 0,   "mortality_pct": 0.1,  "management": "Low risk. Outpatient treatment."},
    "II":  {"max_score": 70,  "mortality_pct": 0.6,  "management": "Low risk. Outpatient treatment."},
    "III": {"max_score": 90,  "mortality_pct": 2.8,  "management": "Low risk. Outpatient treatment or brief observation."},
    "IV":  {"max_score": 130, "mortality_pct": 8.2,  "management": "Moderate risk. Hospital admission recommended."},
    "V":   {"max_score": 999, "mortality_pct": 29.2, "management": "High risk. Hospital admission; consider ICU."},
}

# PSI point assignments for common factors
PSI_POINTS = {
    "age_male": lambda age: age,                    # males: age in years
    "age_female": lambda age: max(0, age - 10),      # females: age minus 10
    "nursing_home": 10,
    "neoplastic_disease": 30,
    "liver_disease": 20,
    "congestive_heart_failure": 10,
    "cerebrovascular_disease": 10,
    "renal_disease": 10,
    "altered_mental_status": 20,
    "respiratory_rate_ge_30": 20,
    "systolic_bp_lt_90": 20,
    "temperature_lt_35_or_ge_40": 15,
    "pulse_ge_125": 10,
    "ph_lt_735": 30,
    "bun_ge_30": 20,
    "sodium_lt_130": 20,
    "glucose_ge_250": 10,
    "hematocrit_lt_30": 10,
    "pao2_lt_60_or_spo2_lt_90": 10,
    "pleural_effusion": 10,
}


def score_psi(age, sex="male", nursing_home=False, neoplastic_disease=False,
              liver_disease=False, congestive_heart_failure=False,
              cerebrovascular_disease=False, renal_disease=False,
              altered_mental_status=False, respiratory_rate_ge_30=False,
              systolic_bp_lt_90=False, temperature_lt_35_or_ge_40=False,
              pulse_ge_125=False, ph_lt_735=False, bun_ge_30=False,
              sodium_lt_130=False, glucose_ge_250=False, hematocrit_lt_30=False,
              pao2_lt_60_or_spo2_lt_90=False, pleural_effusion=False):
    """
    Calculate the adult PSI/PORT two-step risk classification (Fine 1997).

    Stage 1: age <= 50 with no specified comorbidities or abnormal vital
    signs is Class I. Nursing-home residence conservatively bypasses Stage 1.
    Otherwise use age points (male: age; female: age - 10) and add the
    original comorbidity, examination, and investigation points.

    All unspecified risk factors are assumed absent. Clinical use requires
    an actual assessment; a missing observation is not a normal observation.
    """
    try:
        age = float(age)
    except (ValueError, TypeError):
        raise ValueError("Age must be a finite number of adult years") from None
    if not math.isfinite(age) or not 18 <= age <= 120:
        raise ValueError("PSI applies to adults aged 18–120 years")
    sex = str(sex).lower()
    if sex not in ("male", "m", "female", "f"):
        raise ValueError("sex must be male or female for the historical PSI formula")

    clinical_findings = (
        neoplastic_disease, liver_disease, congestive_heart_failure,
        cerebrovascular_disease, renal_disease, altered_mental_status,
        respiratory_rate_ge_30, systolic_bp_lt_90,
        temperature_lt_35_or_ge_40, pulse_ge_125,
    )
    if age <= 50 and not nursing_home and not any(clinical_findings):
        info = PSI_RISK_CLASS["I"]
        return {
            "points": 0,  # Class I is determined by the first step, not points.
            "risk_class": "I",
            "mortality_pct": info["mortality_pct"],
            "management": info["management"],
        }

    pts = int(age) if sex in ("male", "m") else max(0, int(age) - 10)
    point_flags = {
        "nursing_home": nursing_home,
        "neoplastic_disease": neoplastic_disease,
        "liver_disease": liver_disease,
        "congestive_heart_failure": congestive_heart_failure,
        "cerebrovascular_disease": cerebrovascular_disease,
        "renal_disease": renal_disease,
        "altered_mental_status": altered_mental_status,
        "respiratory_rate_ge_30": respiratory_rate_ge_30,
        "systolic_bp_lt_90": systolic_bp_lt_90,
        "temperature_lt_35_or_ge_40": temperature_lt_35_or_ge_40,
        "pulse_ge_125": pulse_ge_125,
        "ph_lt_735": ph_lt_735,
        "bun_ge_30": bun_ge_30,
        "sodium_lt_130": sodium_lt_130,
        "glucose_ge_250": glucose_ge_250,
        "hematocrit_lt_30": hematocrit_lt_30,
        "pao2_lt_60_or_spo2_lt_90": pao2_lt_60_or_spo2_lt_90,
        "pleural_effusion": pleural_effusion,
    }
    pts += sum(PSI_POINTS[name] for name, enabled in point_flags.items() if enabled)
    risk_class = next(
        cls for cls in ("II", "III", "IV", "V")
        if pts <= PSI_RISK_CLASS[cls]["max_score"]
    )
    info = PSI_RISK_CLASS[risk_class]
    return {
        "points": pts,
        "risk_class": risk_class,
        "mortality_pct": info["mortality_pct"],
        "management": info["management"],
    }

# ---------------------------------------------------------------------------
# ATS / IDSA  2007 severe CAP criteria
# ---------------------------------------------------------------------------

ATS_IDSA_MAJOR_CRITERIA = [
    "septic_shock_requiring_vasopressors",
    "invasive_mechanical_ventilation",
]

ATS_IDSA_MINOR_CRITERIA = [
    "respiratory_rate_ge_30",
    "pao2_fio2_ratio_le_250",
    "multilobar_infiltrates",
    "confusion",
    "bun_ge_20",
    "leukopenia_wbc_lt_4000",
    "thrombocytopenia_platelets_lt_100000",
    "hypothermia_core_lt_36",
    "hypotension_requiring_aggressive_fluid",
]


def score_ats_idsa(major_criteria=None, minor_criteria=None):
    """
    Evaluate ATS/IDSA 2007 severe CAP criteria.

    Parameters:
        major_criteria – list of strings from ATS_IDSA_MAJOR_CRITERIA that are met
        minor_criteria – list of strings from ATS_IDSA_MINOR_CRITERIA that are met

    Severe CAP if:
      - 1 or more major criteria met, OR
      - 3 or more minor criteria met

    Returns dict with major count, minor count, is_severe, and recommendation.
    """
    major = set(major_criteria or [])
    minor = set(minor_criteria or [])

    # Validate
    valid_major = set(ATS_IDSA_MAJOR_CRITERIA)
    valid_minor = set(ATS_IDSA_MINOR_CRITERIA)
    unknown_major = major - valid_major
    unknown_minor = minor - valid_minor
    if unknown_major or unknown_minor:
        raise ValueError(
            f"Unknown criteria: {unknown_major | unknown_minor}. "
            f"Valid major: {ATS_IDSA_MAJOR_CRITERIA}, valid minor: {ATS_IDSA_MINOR_CRITERIA}"
        )

    major_count = len(major)
    minor_count = len(minor)
    is_severe = major_count >= 1 or minor_count >= 3

    if is_severe:
        rec = "Severe CAP per ATS/IDSA criteria. ICU admission recommended."
    else:
        rec = "Does not meet ATS/IDSA severe CAP criteria. Standard ward management."

    return {
        "major_criteria_met": sorted(major),
        "minor_criteria_met": sorted(minor),
        "major_count": major_count,
        "minor_count": minor_count,
        "is_severe": is_severe,
        "recommendation": rec,
    }


# ---------------------------------------------------------------------------
# Convenience: evaluate a patient dict (used by CLI batch mode)
# ---------------------------------------------------------------------------

def evaluate_patient(row):
    """
    Score a patient from a dict (e.g. CSV row).

    Expected keys (case-insensitive, flexible):
        confusion          – 1/0/true/false/yes/no
        urea_elevated      – 1/0  (or urea_bun_elevated)
        respiratory_rate   – numeric (>=30 triggers criterion)
        respiratory_rate_high – 1/0 (explicit override)
        systolic_bp        – numeric (<90 triggers criterion)
        diastolic_bp       – numeric (<=60 triggers criterion)
        blood_pressure_low – 1/0 (explicit override)
        age                – numeric (>=65 triggers criterion)

    Returns dict with CURB-65, CRB-65, and PSI results.
    """
    def _bool(val):
        s = str(val).strip().lower()
        return s in ("1", "true", "yes", "y", "t")

    def _num(val, default=None):
        if val is None or str(val).strip() == "":
            return default
        try:
            number = float(val)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric input: {val!r}") from None
        if not math.isfinite(number):
            raise ValueError(f"Non-finite numeric input: {val!r}")
        return number

    # Normalize keys to lowercase
    norm = {}
    for k, v in row.items():
        norm[k.strip().lower()] = v

    # --- Confusion ---
    confusion = _bool(norm.get("confusion", "0"))

    # --- Urea / BUN (explicit columns have explicit units) ---
    urea_elevated = _bool(norm.get("urea_elevated", norm.get("urea_bun_elevated", "0")))
    urea_mmol = _num(norm.get("urea"))        # mmol/L
    bun_mgdl = _num(norm.get("bun"))          # mg/dL
    if urea_mmol is not None:
        if urea_mmol < 0:
            raise ValueError("Urea cannot be negative")
        urea_elevated = urea_elevated or urea_mmol > 7
    if bun_mgdl is not None:
        if bun_mgdl < 0:
            raise ValueError("BUN cannot be negative")
        urea_elevated = urea_elevated or bun_mgdl > 20

    # --- Respiratory rate ---
    rr_high = _bool(norm.get("respiratory_rate_high", "0"))
    rr = _num(norm.get("respiratory_rate", norm.get("rr", None)))
    if rr is not None and rr >= 30:
        rr_high = True

    # --- Blood pressure ---
    bp_low = _bool(norm.get("blood_pressure_low", "0"))
    sbp = _num(norm.get("systolic_bp", norm.get("sbp", None)))
    dbp = _num(norm.get("diastolic_bp", norm.get("dbp", None)))
    if sbp is not None and sbp < 90:
        bp_low = True
    if dbp is not None and dbp <= 60:
        bp_low = True

    # --- Age ---
    age = _num(norm.get("age"))
    if age is None or not 18 <= age <= 120:
        raise ValueError("Valid adult age (18–120 years) is required")
    age_ge_65 = age >= 65

    curb = score_curb65(confusion, urea_elevated, rr_high, bp_low, age_ge_65)
    crb = score_crb65(confusion, rr_high, bp_low, age_ge_65)

    return {
        "curb65": curb,
        "crb65": crb,
    }
