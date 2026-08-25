# CURB-65 Pneumonia Severity Calculator

A command-line tool for scoring community-acquired pneumonia severity using four validated clinical scoring systems.

**This is a clinical decision support tool. It does not replace clinical judgment.**

## What it does

Calculates pneumonia severity scores from patient data:

| Score | Variables | Use case |
|-------|-----------|----------|
| **CURB-65** | Confusion, Urea, RR, BP, Age≥65 | Standard CAP severity (needs lab) |
| **CRB-65** | Confusion, RR, BP, Age≥65 | Field/outpatient use (no lab needed) |
| **PSI/PORT** | 20 clinical variables | Detailed risk stratification (classes I-V) |
| **ATS/IDSA** | Major + minor criteria | Severe CAP / ICU triage |

## Quick start

```bash
# Score a single patient (CURB-65)
python cli.py score --confusion --urea 25 --rr 32 --sbp 85 --age 70

# CRB-65 (no lab required)
python cli.py crb65 --confusion --rr 32 --sbp 85 --age 70

# PSI/PORT risk class
python cli.py psi --age 70 --sex male --altered-mental-status --bun-ge-30

# ATS/IDSA severe CAP criteria
python cli.py ats-idsa --major septic_shock_requiring_vasopressors \
    --minor respiratory_rate_ge_30 --minor confusion --minor bun_ge_20

# Batch process a CSV
python cli.py batch --input patients.csv --output scored.csv

# JSON output (add --json to score/crb65/psi/ats-idsa)
python cli.py score --age 30 --json
```

## CURB-65 scoring

Each criterion = 1 point. Total range: 0-5.

| Criterion | Definition |
|-----------|-----------|
| **C** - Confusion | New-onset confusion (AMT < 8 or equivalent) |
| **U** - Urea | Urea > 7 mmol/L (BUN > 20 mg/dL) |
| **R** - Respiratory rate | RR ≥ 30 breaths/min |
| **B** - Blood pressure | Systolic < 90 mmHg OR diastolic ≤ 60 mmHg |
| **65** - Age | Age ≥ 65 years |

| Score | 30-day mortality | Management |
|-------|-----------------|------------|
| 0 | 0.7% | Outpatient treatment |
| 1 | 3.2% | Outpatient; assess social circumstances |
| 2 | 13.0% | Short inpatient or supervised outpatient |
| 3 | 17.0% | Severe; consider ICU |
| 4 | 42.0% | Severe; consider ICU |
| 5 | 57.0% | Severe; consider ICU |

## CRB-65 (no lab variant)

Same as CURB-65 but without urea. Score range: 0-4.

| Score | Risk | Action |
|-------|------|--------|
| 0 | Low | Outpatient |
| 1 | Low-moderate | Outpatient with close follow-up |
| 2 | Moderate | Consider admission |
| 3-4 | High | Urgent admission; consider ICU |

## PSI/PORT (simplified)

Point-based system with risk classes I-V. Uses age, sex, comorbidities, and clinical findings. See `score_psi()` in `curb65.py` for the full parameter list.

## ATS/IDSA severe CAP criteria

Severe CAP if **1+ major** OR **3+ minor** criteria met:

**Major:** septic shock requiring vasopressors, invasive mechanical ventilation

**Minor:** RR ≥30, PaO2/FiO2 ≤250, multilobar infiltrates, confusion, BUN ≥20, leukopenia, thrombocytopenia, hypothermia, hypotension requiring fluids

## Batch CSV format

Input CSV should have these columns (case-insensitive):

```
patient_id,age,confusion,urea,respiratory_rate,systolic_bp,diastolic_bp
P001,30,0,,18,120,80
P002,75,1,10,32,80,55
```

- `urea` in mmol/L (>7 triggers criterion); or use `bun` in mg/dL (>20 triggers)
- `confusion`: 1/0, true/false, yes/no
- Numeric values for `respiratory_rate`, `systolic_bp`, `diastolic_bp` are auto-evaluated against thresholds

Output adds: `curb65_score`, `curb65_mortality_pct`, `curb65_management`, `crb65_score`, `crb65_management`

## Python API

```python
from curb65 import score_curb65, score_crb65, score_psi, score_ats_idsa

# CURB-65
r = score_curb65(confusion=True, urea_elevated=True, respiratory_rate_high=True,
                 blood_pressure_low=False, age_ge_65=True)
print(r["score"])          # 4
print(r["mortality_pct"])  # 42.0
print(r["management"])     # "Severe pneumonia. Manage as severe; consider ICU admission."

# CRB-65
r = score_crb65(confusion=False, respiratory_rate_high=False,
                blood_pressure_low=False, age_ge_65=True)
print(r["score"])  # 1

# PSI/PORT
r = score_psi(age=70, sex="male", congestive_heart_failure=True)
print(r["risk_class"])  # "III"

# ATS/IDSA
r = score_ats_idsa(major_criteria=[], minor_criteria=["respiratory_rate_ge_30", "confusion", "bun_ge_20"])
print(r["is_severe"])  # True
```

## Running tests

```bash
python -m pytest test_curb65.py -v
# or
python -m unittest test_curb65 -v
```

## Requirements

Python 3.7+ (stdlib only, no external dependencies).

## References

- Lim WS et al. "Defining community acquired pneumonia severity on presentation to hospital." *Thorax* 2003;58:377-382.
- Fine MJ et al. "A prediction rule to identify low-risk patients with community-acquired pneumonia." *NEJM* 1997;336:243-250.
- Mandell LA et al. "Infectious Diseases Society of America/American Thoracic Society consensus guidelines." *Clin Infect Dis* 2007;44:S27-S72.

## License

MIT
