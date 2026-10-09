# CURB-65 / CRB-65 Pneumonia Severity Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/curb65-pneumonia-score/)

Clinical decision-support utilities for adult community-acquired pneumonia. Includes an offline browser calculator, Python scoring functions, a CLI for individual and CSV-based assessment, and an optional FastAPI demonstration service.

**Clinical limitation:** These rules estimate severity in adults with an established diagnosis; they do not diagnose pneumonia or replace assessment of oxygenation, sepsis, comorbidities, or clinical circumstances. Historical group mortality estimates must not be interpreted as individual predictions.

## Browser calculator

The static application is in [web/](web/). Use the [live application](https://abusuraihsakhri.github.io/curb65-pneumonia-score/) or open `web/index.html` locally.

- Calculates CURB-65 (0–5) when urea or BUN is available and CRB-65 (0–4) with or without laboratory testing.
- Validates adult age, respiratory rate, blood pressure, and laboratory values before calculating.
- Shows individual criteria, thresholds, and a contextual interpretation.
- Uses local JavaScript only. It does not transmit, store, or log entered observations. No patient identifiers are requested.

## Python scoring and CLI

`curb65.py` uses the Python standard library and exposes `score_curb65()`, `score_crb65()`, `score_psi()`, `score_ats_idsa()`, and `evaluate_patient()`.

Python 3.10 or later:

```bash
python cli.py score --confusion --urea 8 --rr 32 --sbp 85 --dbp 55 --age 70
python cli.py crb65 --rr 20 --sbp 120 --dbp 80 --age 40
python cli.py psi --age 70 --sex female --altered-mental-status
python cli.py ats-idsa --major invasive_mechanical_ventilation
python cli.py batch --input sample.csv --output scored.csv
```

For laboratory input, `--urea` means urea in **mmol/L** (abnormal above 7) and `--bun` means blood urea nitrogen in **mg/dL** (abnormal above 20). CSV input uses the columns `urea` and `bun` with those respective units. Units are not guessed from numeric values.

In CSV input, `age` must be an adult age (18–120). Other columns are optional for backward compatibility; omitted measurements still contribute no points, but the result includes `curb65_complete`, `crb65_complete`, and `missing_inputs` columns to flag incomplete assessments. **Do not treat an incomplete low score as a validated low-risk classification.**

The PSI/PORT function implements the original adult two-stage age/clinical screening and point classification. Historical male/female age adjustments are retained because they belong to the published model. The ATS/IDSA function evaluates severe-CAP major/minor criteria. These are distinct from CURB-65 and should not be used interchangeably.

## Optional API and demonstration agents

The `agents/` package and `enrichment.py` contain a separate **generic demonstration** workflow; its arbitrary measurement thresholds, mock language-model output, and regex-based identifier guard are **not validated clinical decision systems**. The identifier patterns do not establish PHI de-identification, HIPAA compliance, or certification. Do not submit real patient identifiers or sensitive clinical data.

Install the optional packages and run the API locally:

```bash
python -m pip install 'pydantic>=2,<3' fastapi uvicorn pytest
python -m uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

The API exposes `/health`, `/metrics`, and demonstration endpoints under `/api/`. A mock provider is used; there is no actual hosted LLM integration. The in-memory audit chain uses HMAC-SHA256 for signatures. Its key and history are not persisted automatically: set a private `AUDIT_SECRET_KEY` for a stable key and use persistent storage if an audit record is needed.

## Docker

```bash
docker build -t curb65-pneumonia-score .
docker run --rm -p 8000:8000 -e AUDIT_SECRET_KEY='replace-with-a-random-secret' curb65-pneumonia-score
# or: AUDIT_SECRET_KEY='replace-with-a-random-secret' docker compose up --build
```

The container launches the FastAPI server on port 8000. Generate a strong unique key for non-demo use; never commit it to the repository. Docker is optional for the browser calculator.

## Tests

```bash
python -m pip install 'pydantic>=2,<3' fastapi uvicorn pytest
python -m pytest -q
node --check web/app.js
node --test tests/browser.test.cjs
```

The GitHub Actions workflow tests Python 3.10–3.12 and Node 22 before attempting a Pages deployment from `web/` on pushes to `master`. Pages must be configured in repository settings to use **GitHub Actions** as the build and deployment source.

## References

- Lim WS et al. Defining community acquired pneumonia severity on presentation to hospital. *Thorax*. 2003;58:377–382.
- Fine MJ et al. A prediction rule to identify low-risk patients with community-acquired pneumonia. *N Engl J Med*. 1997;336:243–250.
- Mandell LA et al. IDSA/ATS consensus guidelines for community-acquired pneumonia in adults. *Clin Infect Dis*. 2007;44(Suppl 2):S27–S72.

## Compatibility and license

Browser: current Chrome, Firefox, Safari, and Edge with JavaScript enabled. Python: 3.10–3.12 in CI. Distributed under the [MIT License](LICENSE).
