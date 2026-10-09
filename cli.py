#!/usr/bin/env python3
"""
CLI for CURB-65 Pneumonia Severity Calculator.

Usage:
    python cli.py score --confusion --urea 25 --rr 32 --sbp 85 --age 70
    python cli.py score --age 45 --rr 20 --sbp 120 --dbp 80
    python cli.py crb65 --confusion --rr 32 --sbp 85 --age 70
    python cli.py psi --age 70 --sex male --altered-mental-status --bun-ge-30
    python cli.py ats-idsa --major septic_shock_requiring_vasopressors --minor respiratory_rate_ge_30 --minor confusion --minor bun_ge_20
    python cli.py batch --input patients.csv --output scored.csv
"""
import argparse
import csv
import json
import sys

from curb65 import (
    score_curb65,
    score_crb65,
    score_psi,
    score_ats_idsa,
    evaluate_patient,
    ATS_IDSA_MAJOR_CRITERIA,
    ATS_IDSA_MINOR_CRITERIA,
)

try:
    from agents.supervisor import SystemSupervisor
    from agents.base import AuditLogger
    from agents.models import SystemTaskPayload
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


def _print_result(result, label="Result"):
    """Pretty-print a result dict."""
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")
    for k, v in result.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for dk, dv in v.items():
                print(f"    {dk}: {dv}")
        elif isinstance(v, list):
            print(f"  {k}: {', '.join(str(i) for i in v) if v else '(none)'}")
        else:
            print(f"  {k}: {v}")
    print()


def cmd_score(args):
    """Score a single patient with CURB-65."""
    # Urea: if value given, check if elevated; otherwise use flag
    urea_elevated = args.urea_elevated
    if args.urea is not None:
        urea_elevated = args.urea > 7  # mmol/L
    elif args.bun is not None:
        urea_elevated = args.bun > 20  # mg/dL

    # RR
    rr_high = args.rr_high
    if args.rr is not None:
        rr_high = args.rr >= 30

    # BP
    bp_low = args.bp_low
    if args.sbp is not None:
        bp_low = args.sbp < 90
    if args.dbp is not None and args.dbp <= 60:
        bp_low = True

    # Age
    age_ge_65 = args.age >= 65

    result = score_curb65(
        confusion=args.confusion,
        urea_elevated=urea_elevated,
        respiratory_rate_high=rr_high,
        blood_pressure_low=bp_low,
        age_ge_65=age_ge_65,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_result(result, f"CURB-65 Score (Age: {args.age})")
    return 0


def cmd_crb65(args):
    """Score a single patient with CRB-65 (no lab)."""
    rr_high = args.rr_high
    if args.rr is not None:
        rr_high = args.rr >= 30

    bp_low = args.bp_low
    if args.sbp is not None:
        bp_low = args.sbp < 90
    if args.dbp is not None and args.dbp <= 60:
        bp_low = True

    age_ge_65 = args.age >= 65

    result = score_crb65(
        confusion=args.confusion,
        respiratory_rate_high=rr_high,
        blood_pressure_low=bp_low,
        age_ge_65=age_ge_65,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_result(result, f"CRB-65 Score (Age: {args.age})")
    return 0


def cmd_psi(args):
    """Score a single patient with PSI/PORT."""
    result = score_psi(
        age=args.age,
        sex=args.sex,
        nursing_home=args.nursing_home,
        neoplastic_disease=args.neoplastic_disease,
        liver_disease=args.liver_disease,
        congestive_heart_failure=args.chf,
        cerebrovascular_disease=args.cvd,
        renal_disease=args.renal,
        altered_mental_status=args.altered_mental_status,
        respiratory_rate_ge_30=args.rr_ge_30,
        systolic_bp_lt_90=args.sbp_lt_90,
        temperature_lt_35_or_ge_40=args.temp_extreme,
        pulse_ge_125=args.pulse_ge_125,
        ph_lt_735=args.ph_lt_735,
        bun_ge_30=args.bun_ge_30,
        sodium_lt_130=args.na_lt_130,
        glucose_ge_250=args.glucose_ge_250,
        hematocrit_lt_30=args.hct_lt_30,
        pao2_lt_60_or_spo2_lt_90=args.hypoxemia,
        pleural_effusion=args.pleural_effusion,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_result(result, f"PSI/PORT Score (Age: {args.age}, Sex: {args.sex})")
    return 0


def cmd_ats_idsa(args):
    """Evaluate ATS/IDSA severe CAP criteria."""
    result = score_ats_idsa(
        major_criteria=args.major,
        minor_criteria=args.minor,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_result(result, "ATS/IDSA Severe CAP Criteria")
    return 0


def cmd_batch(args):
    """Batch-process a CSV of patients."""
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "curb65_score", "curb65_mortality_pct", "curb65_management",
        "crb65_score", "crb65_management",
        "curb65_complete", "crb65_complete", "missing_inputs",
    ]

    out_fields = list(dict.fromkeys(out_fields))

    out_rows = []
    for row in rows:
        result = evaluate_patient(row)
        curb = result["curb65"]
        crb = result["crb65"]
        merged = dict(row)
        merged["curb65_score"] = curb["score"]
        merged["curb65_mortality_pct"] = curb["mortality_pct"]
        merged["curb65_management"] = curb["management"]
        merged["crb65_score"] = crb["score"]
        merged["crb65_management"] = crb["management"]
        merged["curb65_complete"] = result["curb65_complete"]
        merged["crb65_complete"] = result["crb65_complete"]
        merged["missing_inputs"] = ";".join(result["missing_inputs"])
        out_rows.append(merged)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    incomplete = sum(not r["curb65_complete"] for r in out_rows)
    print(f"Processed {len(out_rows)} patients -> {args.output}")
    if incomplete:
        print(f"Warning: {incomplete} rows have missing CURB-65 criteria; scores may underestimate severity.", file=sys.stderr)
    return 0


def cmd_audit(args):
    """Process a task through the supervisor and write to the audit trail."""
    if not AGENTS_AVAILABLE:
        print("Error: agents module not available (pydantic required).", file=sys.stderr)
        return 1
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id=args.task_id,
        target_identifier=args.target_identifier or args.task_id,
        primary_metric=args.primary_metric,
        secondary_metric=args.secondary_metric,
        status_descriptor=args.status_descriptor,
    )
    dossier = supervisor.process_task(payload)
    if args.json:
        print(json.dumps(dossier.to_dict(), indent=2, default=str))
    else:
        _print_result(dossier.to_dict(), "Audit Dossier")
    return 0


def cmd_chat(args):
    """Query the LLM via the supervisor."""
    if not AGENTS_AVAILABLE:
        print("Error: agents module not available (pydantic required).", file=sys.stderr)
        return 1
    supervisor = SystemSupervisor(model_provider="mock")
    query = " ".join(args.query)
    response = supervisor.query_supervisory_chat(query)
    if args.json:
        print(json.dumps({"query": query, "response": response}, indent=2))
    else:
        print(f"\nQuery: {query}\nResponse: {response}\n")
    return 0


def cmd_verify_audit(args):
    """Verify the integrity of the HMAC-SHA256 audit trail."""
    if not AGENTS_AVAILABLE:
        print("Error: agents module not available (pydantic required).", file=sys.stderr)
        return 1
    valid = AuditLogger.verify_integrity()
    trail_len = len(AuditLogger.get_trail())
    if args.json:
        print(json.dumps({"valid": valid, "trail_length": trail_len}, indent=2))
    else:
        status = "VALID" if valid else "TAMPERED"
        print(f"\nAudit Trail Integrity: {status}")
        print(f"Total audit blocks: {trail_len}\n")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="curb65",
        description="CURB-65 Pneumonia Severity Calculator",
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    # --- score (CURB-65) ---
    s = sub.add_parser("score", help="Calculate CURB-65 score for a single patient")
    s.add_argument("--confusion", action="store_true", help="New-onset confusion")
    s.add_argument("--urea", type=float, default=None, help="Urea in mmol/L")
    s.add_argument("--bun", type=float, default=None, help="BUN in mg/dL")
    s.add_argument("--urea-elevated", action="store_true", help="Urea/BUN elevated (flag)")
    s.add_argument("--rr", type=float, default=None, help="Respiratory rate (breaths/min)")
    s.add_argument("--rr-high", action="store_true", help="RR >= 30 (flag)")
    s.add_argument("--sbp", type=float, default=None, help="Systolic BP (mmHg)")
    s.add_argument("--dbp", type=float, default=None, help="Diastolic BP (mmHg)")
    s.add_argument("--bp-low", action="store_true", help="BP low (flag)")
    s.add_argument("--age", type=float, required=True, help="Patient age (years)")
    s.add_argument("--json", action="store_true", help="Output as JSON")

    # --- crb65 ---
    c = sub.add_parser("crb65", help="Calculate CRB-65 score (no lab required)")
    c.add_argument("--confusion", action="store_true", help="New-onset confusion")
    c.add_argument("--rr", type=float, default=None, help="Respiratory rate (breaths/min)")
    c.add_argument("--rr-high", action="store_true", help="RR >= 30 (flag)")
    c.add_argument("--sbp", type=float, default=None, help="Systolic BP (mmHg)")
    c.add_argument("--dbp", type=float, default=None, help="Diastolic BP (mmHg)")
    c.add_argument("--bp-low", action="store_true", help="BP low (flag)")
    c.add_argument("--age", type=float, required=True, help="Patient age (years)")
    c.add_argument("--json", action="store_true", help="Output as JSON")

    # --- psi ---
    psi = sub.add_parser("psi", help="Calculate PSI/PORT risk class")
    psi.add_argument("--age", type=float, required=True, help="Patient age")
    psi.add_argument("--sex", default="male", choices=["male", "female"], help="Biological sex")
    psi.add_argument("--nursing-home", action="store_true")
    psi.add_argument("--neoplastic-disease", action="store_true")
    psi.add_argument("--liver-disease", action="store_true")
    psi.add_argument("--chf", action="store_true", help="Congestive heart failure")
    psi.add_argument("--cvd", action="store_true", help="Cerebrovascular disease")
    psi.add_argument("--renal", action="store_true", help="Renal disease")
    psi.add_argument("--altered-mental-status", action="store_true")
    psi.add_argument("--rr-ge-30", action="store_true")
    psi.add_argument("--sbp-lt-90", action="store_true")
    psi.add_argument("--temp-extreme", action="store_true", help="Temp <35 or >=40 C")
    psi.add_argument("--pulse-ge-125", action="store_true")
    psi.add_argument("--ph-lt-735", action="store_true")
    psi.add_argument("--bun-ge-30", action="store_true")
    psi.add_argument("--na-lt-130", action="store_true")
    psi.add_argument("--glucose-ge-250", action="store_true")
    psi.add_argument("--hct-lt-30", action="store_true")
    psi.add_argument("--hypoxemia", action="store_true", help="PaO2 <60 or SpO2 <90%")
    psi.add_argument("--pleural-effusion", action="store_true")
    psi.add_argument("--json", action="store_true", help="Output as JSON")

    # --- ats-idsa ---
    ats = sub.add_parser("ats-idsa", help="Evaluate ATS/IDSA severe CAP criteria")
    ats.add_argument("--major", action="append", default=[],
                     choices=ATS_IDSA_MAJOR_CRITERIA,
                     help="Major criterion met (repeatable)")
    ats.add_argument("--minor", action="append", default=[],
                     choices=ATS_IDSA_MINOR_CRITERIA,
                     help="Minor criterion met (repeatable)")
    ats.add_argument("--json", action="store_true", help="Output as JSON")

    # --- batch ---
    b = sub.add_parser("batch", help="Batch-process a CSV of patients")
    b.add_argument("--input", required=True, help="Input CSV path")
    b.add_argument("--output", default="scored.csv", help="Output CSV path")

    # --- audit ---
    a = sub.add_parser("audit", help="Process a task through the supervisor and write to the audit trail")
    a.add_argument("--task-id", required=True, help="Task identifier")
    a.add_argument("--target-identifier", default=None, help="Target identifier (defaults to task-id)")
    a.add_argument("--primary-metric", type=float, default=0.0, help="Primary metric value")
    a.add_argument("--secondary-metric", type=float, default=0.0, help="Secondary metric value")
    a.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    a.add_argument("--json", action="store_true", help="Output as JSON")

    # --- chat ---
    ch = sub.add_parser("chat", help="Query the LLM via the supervisor")
    ch.add_argument("query", nargs="+", help="Query text")
    ch.add_argument("--json", action="store_true", help="Output as JSON")

    # --- verify-audit ---
    va = sub.add_parser("verify-audit", help="Verify the integrity of the HMAC-SHA256 audit trail")
    va.add_argument("--json", action="store_true", help="Output as JSON")

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "score":
        return cmd_score(args)
    elif args.cmd == "crb65":
        return cmd_crb65(args)
    elif args.cmd == "psi":
        return cmd_psi(args)
    elif args.cmd == "ats-idsa":
        return cmd_ats_idsa(args)
    elif args.cmd == "batch":
        return cmd_batch(args)
    elif args.cmd == "audit":
        return cmd_audit(args)
    elif args.cmd == "chat":
        return cmd_chat(args)
    elif args.cmd == "verify-audit":
        return cmd_verify_audit(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
