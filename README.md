# CURB65 Pneumonia Score

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`score_curb65()`**: Calculate CURB-65 score.

Parameters (all bool):
    confusion            – New-onset confusion (AMT < 8 or equivalent)
    urea_elevated        – Urea > 7 mmol/L  (BUN > 20 mg/dL)
    respiratory_rate_high – Respiratory rate >= 30 breaths/min
    blood_pressure_low   – Systolic < 90 mmHg OR diastolic <= 60 mmHg
    age_ge_65            – Age >= 65 years

Returns dict with score, criteria met, mortality estimate, and management.
- **`score_crb65()`**: Calculate CRB-65 score (no urea/BUN required).

Parameters (all bool):
    confusion             – New-onset confusion
    respiratory_rate_high – Respiratory rate >= 30 breaths/min
    blood_pressure_low    – Systolic < 90 mmHg OR diastolic <= 60 mmHg
    age_ge_65             – Age >= 65 years

Returns dict with score (0-4), criteria met, and management.
- **`score_psi()`**: Calculate simplified PSI/PORT score and risk class.

Returns dict with total points, risk class, mortality estimate, and management.
- **`score_ats_idsa()`**: Evaluate ATS/IDSA 2007 severe CAP criteria.

Parameters:
    major_criteria – list of strings from ATS_IDSA_MAJOR_CRITERIA that are met
    minor_criteria – list of strings from ATS_IDSA_MINOR_CRITERIA that are met

Severe CAP if:
  - 1 or more major criteria met, OR
  - 3 or more minor criteria met

Returns dict with major count, minor count, is_severe, and recommendation.
- **`evaluate_patient()`**: Score a patient from a dict (e.g. CSV row).

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

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate CURB-65 score.
  score = sum(flags.values())
  Calculate CRB-65 score (no urea/BUN required).
  Calculate simplified PSI/PORT score and risk class.
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --confusion <value> --urea <value> --rr <value> --sbp <value>
```

### Parameter Reference
- `--confusion`: Specifies input measurement or parameter value.
- `--urea`: Specifies input measurement or parameter value.
- `--rr`: Specifies input measurement or parameter value.
- `--sbp`: Specifies input measurement or parameter value.
- `--age`: Specifies input measurement or parameter value.
- `--dbp`: Specifies input measurement or parameter value.
- `--sex`: Specifies input measurement or parameter value.
- `--altered-mental-status`: Specifies input measurement or parameter value.
- `--bun-ge-30`: Specifies input measurement or parameter value.
- `--major`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Parameter / observation metric | Required |
| `age` | Parameter / observation metric | Required |
| `confusion` | Parameter / observation metric | Required |
| `urea` | Parameter / observation metric | Required |
| `respiratory_rate` | Parameter / observation metric | Required |
| `systolic_bp` | Parameter / observation metric | Required |
| `diastolic_bp` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t curb65-pneumonia-score .
docker run -p 8000:8000 curb65-pneumonia-score
```
