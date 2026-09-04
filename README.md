# CURB65 Pneumonia Score

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

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

**Disclaimer:** This is a clinical decision SUPPORT tool. It does not replace clinical judgment. Treatment decisions must consider the full clinical picture.

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

## 💻 CLI Quickstart & Usage

### 1. Score a single patient (CURB-65)
```bash
python cli.py score --confusion --urea 25 --rr 32 --sbp 85 --age 70
```

### 2. Score without lab values (CRB-65)
```bash
python cli.py crb65 --confusion --rr 32 --sbp 85 --age 70
```

### 3. Calculate PSI/PORT risk class
```bash
python cli.py psi --age 70 --sex male --altered-mental-status --bun-ge-30
```

### 4. Evaluate ATS/IDSA severe CAP criteria
```bash
python cli.py ats-idsa --major septic_shock_requiring_vasopressors --minor respiratory_rate_ge_30 --minor confusion --minor bun_ge_20
```

### 5. Batch process a CSV file
```bash
python cli.py batch --input patients.csv --output scored.csv
```

### 6. Process a task through the audit trail
```bash
python cli.py audit --task-id TASK-001 --primary-metric 12.0
```

### 7. Query the LLM via the supervisor
```bash
python cli.py chat "Explain the CURB-65 criteria"
```

### 8. Verify audit trail integrity
```bash
python cli.py verify-audit
```

### Parameter Reference
- `--confusion`: New-onset confusion (flag)
- `--urea`: Urea in mmol/L
- `--bun`: BUN in mg/dL
- `--rr`: Respiratory rate (breaths/min)
- `--sbp`: Systolic BP (mmHg)
- `--dbp`: Diastolic BP (mmHg)
- `--age`: Patient age (years)
- `--sex`: Biological sex (male/female)
- `--json`: Output as JSON

### Input Data Schema (for batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Patient identifier | Optional |
| `age` | Patient age in years | Required |
| `confusion` | New-onset confusion (1/0/true/false) | Optional |
| `urea` | Urea in mmol/L (or `bun` in mg/dL) | Optional |
| `respiratory_rate` | Breaths per minute | Optional |
| `systolic_bp` | Systolic blood pressure | Optional |
| `diastolic_bp` | Diastolic blood pressure | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
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

Run tests for the core scoring module only (no external dependencies):

```bash
python -m pytest test_curb65.py -v
```

Run tests for the enterprise agents module (requires pydantic):

```bash
python -m pytest tests/ -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t curb65-pneumonia-score .
docker run -p 8000:8000 curb65-pneumonia-score
```

To run a specific command in the container:

```bash
docker run curb65-pneumonia-score python cli.py score --age 70 --confusion
```

---

## 📦 Dependencies

**Core module (`curb65.py`, `cli.py`):** Stdlib only — no external dependencies.

**Enterprise agents module (`agents/`):** Requires `pydantic` and `fastapi`.

Install optional dependencies:

```bash
pip install pydantic fastapi uvicorn pytest
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
