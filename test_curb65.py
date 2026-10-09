#!/usr/bin/env python3
"""
Tests for CURB-65 Pneumonia Severity Calculator.

Covers:
  - CURB-65 scoring (score 0 through 5)
  - Individual criteria evaluation
  - CRB-65 variant
  - PSI/PORT risk classes
  - ATS/IDSA severe CAP criteria
  - Management recommendations
  - Age boundary (64 vs 65)
  - CLI interface
  - Batch CSV processing
"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest

from curb65 import (
    score_curb65,
    score_crb65,
    score_psi,
    score_ats_idsa,
    evaluate_patient,
    CURB65_MORTALITY,
    CURB65_MANAGEMENT,
    CRB65_MANAGEMENT,
    ATS_IDSA_MAJOR_CRITERIA,
    ATS_IDSA_MINOR_CRITERIA,
)


class TestCURB65ScoreZero(unittest.TestCase):
    """Score 0: no criteria met — lowest risk."""

    def test_all_false(self):
        r = score_curb65(False, False, False, False, False)
        self.assertEqual(r["score"], 0)
        self.assertEqual(r["mortality_pct"], 0.7)
        self.assertIn("outpatient", r["management"].lower())

    def test_young_healthy(self):
        """Young patient with normal vitals and labs."""
        r = score_curb65(
            confusion=False,
            urea_elevated=False,
            respiratory_rate_high=False,
            blood_pressure_low=False,
            age_ge_65=False,
        )
        self.assertEqual(r["score"], 0)
        self.assertEqual(r["criteria"]["confusion"], False)
        self.assertEqual(r["criteria"]["urea_elevated"], False)


class TestCURB65ScoreFive(unittest.TestCase):
    """Score 5: all criteria met — maximum severity."""

    def test_all_true(self):
        r = score_curb65(True, True, True, True, True)
        self.assertEqual(r["score"], 5)
        self.assertEqual(r["mortality_pct"], 57.0)
        self.assertIn("ICU", r["management"])

    def test_all_criteria_flagged(self):
        r = score_curb65(True, True, True, True, True)
        for crit, val in r["criteria"].items():
            self.assertTrue(val, f"{crit} should be True")


class TestCURB65IndividualCriteria(unittest.TestCase):
    """Each criterion contributes exactly 1 point."""

    def test_confusion_alone(self):
        r = score_curb65(True, False, False, False, False)
        self.assertEqual(r["score"], 1)

    def test_urea_alone(self):
        r = score_curb65(False, True, False, False, False)
        self.assertEqual(r["score"], 1)

    def test_respiratory_rate_alone(self):
        r = score_curb65(False, False, True, False, False)
        self.assertEqual(r["score"], 1)

    def test_blood_pressure_alone(self):
        r = score_curb65(False, False, False, True, False)
        self.assertEqual(r["score"], 1)

    def test_age_alone(self):
        r = score_curb65(False, False, False, False, True)
        self.assertEqual(r["score"], 1)

    def test_two_criteria(self):
        r = score_curb65(True, True, False, False, False)
        self.assertEqual(r["score"], 2)

    def test_three_criteria(self):
        r = score_curb65(True, True, True, False, False)
        self.assertEqual(r["score"], 3)

    def test_four_criteria(self):
        r = score_curb65(True, True, True, True, False)
        self.assertEqual(r["score"], 4)


class TestCURB65MortalityTable(unittest.TestCase):
    """Verify the full mortality table is correct."""

    def test_all_mortality_values(self):
        expected = {0: 0.7, 1: 3.2, 2: 13.0, 3: 17.0, 4: 42.0, 5: 57.0}
        for score, mortality in expected.items():
            self.assertEqual(CURB65_MORTALITY[score], mortality,
                             f"Mortality for score {score} should be {mortality}")

    def test_mortality_monotonically_increases(self):
        values = [CURB65_MORTALITY[i] for i in range(6)]
        for i in range(len(values) - 1):
            self.assertGreater(values[i + 1], values[i],
                               f"Mortality should increase from score {i} to {i+1}")


class TestCURB65Management(unittest.TestCase):
    """Management recommendations for each score level."""

    def test_score_0_outpatient(self):
        self.assertIn("outpatient", CURB65_MANAGEMENT[0].lower())

    def test_score_1_outpatient(self):
        self.assertIn("outpatient", CURB65_MANAGEMENT[1].lower())

    def test_score_2_moderate(self):
        self.assertIn("moderate", CURB65_MANAGEMENT[2].lower())

    def test_score_3_severe(self):
        self.assertIn("severe", CURB65_MANAGEMENT[3].lower())

    def test_score_4_severe(self):
        self.assertIn("severe", CURB65_MANAGEMENT[4].lower())

    def test_score_5_severe(self):
        self.assertIn("severe", CURB65_MANAGEMENT[5].lower())

    def test_scores_3_to_5_mention_icu(self):
        for s in (3, 4, 5):
            self.assertIn("ICU", CURB65_MANAGEMENT[s],
                          f"Score {s} management should mention ICU")


class TestAgeBoundary(unittest.TestCase):
    """Age boundary: 64 vs 65."""

    def test_age_64_not_triggered(self):
        r = score_curb65(False, False, False, False, age_ge_65=False)
        self.assertEqual(r["score"], 0)
        self.assertFalse(r["criteria"]["age_ge_65"])

    def test_age_65_triggered(self):
        r = score_curb65(False, False, False, False, age_ge_65=True)
        self.assertEqual(r["score"], 1)
        self.assertTrue(r["criteria"]["age_ge_65"])

    def test_evaluate_patient_age_64(self):
        """evaluate_patient with age=64 should NOT trigger age criterion."""
        r = evaluate_patient({"age": "64"})
        self.assertEqual(r["curb65"]["score"], 0)
        self.assertFalse(r["curb65"]["criteria"]["age_ge_65"])

    def test_evaluate_patient_age_65(self):
        """evaluate_patient with age=65 SHOULD trigger age criterion."""
        r = evaluate_patient({"age": "65"})
        self.assertEqual(r["curb65"]["score"], 1)
        self.assertTrue(r["curb65"]["criteria"]["age_ge_65"])

    def test_evaluate_patient_age_66(self):
        r = evaluate_patient({"age": "66"})
        self.assertEqual(r["curb65"]["score"], 1)
        self.assertTrue(r["curb65"]["criteria"]["age_ge_65"])


class TestCRB65(unittest.TestCase):
    """CRB-65 variant (no urea/BUN)."""

    def test_score_zero(self):
        r = score_crb65(False, False, False, False)
        self.assertEqual(r["score"], 0)
        self.assertIn("outpatient", r["management"].lower())

    def test_score_four(self):
        r = score_crb65(True, True, True, True)
        self.assertEqual(r["score"], 4)
        self.assertIn("ICU", r["management"])

    def test_individual_criteria(self):
        for i, (c, rr, bp, age) in enumerate([
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ]):
            r = score_crb65(c, rr, bp, age)
            self.assertEqual(r["score"], 1, f"Criterion index {i} should give score 1")

    def test_management_score_1(self):
        r = score_crb65(True, False, False, False)
        self.assertEqual(r["score"], 1)
        self.assertIn("outpatient", r["management"].lower())

    def test_management_score_2(self):
        r = score_crb65(True, True, False, False)
        self.assertEqual(r["score"], 2)
        self.assertIn("hospital", r["management"].lower())

    def test_management_score_3(self):
        r = score_crb65(True, True, True, False)
        self.assertEqual(r["score"], 3)
        self.assertIn("ICU", r["management"])


class TestPSI(unittest.TestCase):
    """PSI/PORT risk class scoring."""

    def test_young_healthy_class_i(self):
        self.assertEqual(score_psi(age=20, sex="male")["risk_class"], "I")

    def test_age_50_without_findings_class_i(self):
        self.assertEqual(score_psi(age=50, sex="female")["risk_class"], "I")

    def test_class_ii(self):
        r = score_psi(age=60, sex="male")
        self.assertEqual((r["points"], r["risk_class"]), (60, "II"))

    def test_class_iii(self):
        r = score_psi(age=80, sex="male")
        self.assertEqual((r["points"], r["risk_class"]), (80, "III"))

    def test_class_iv(self):
        r = score_psi(age=80, sex="male", congestive_heart_failure=True,
                      cerebrovascular_disease=True)
        self.assertEqual((r["points"], r["risk_class"]), (100, "IV"))

    def test_class_v(self):
        r = score_psi(
            age=85, sex="male", neoplastic_disease=True, liver_disease=True,
            altered_mental_status=True, respiratory_rate_ge_30=True,
            systolic_bp_lt_90=True,
        )
        self.assertEqual((r["points"], r["risk_class"]), (195, "V"))

    def test_female_age_adjustment(self):
        self.assertEqual(score_psi(age=80, sex="female")["points"], 70)
        self.assertEqual(score_psi(age=80, sex="male")["points"], 80)

    def test_stage_one_bypassed_by_abnormal_clinical_findings(self):
        r = score_psi(age=40, sex="male", respiratory_rate_ge_30=True)
        self.assertEqual((r["points"], r["risk_class"]), (60, "II"))

    def test_invalid_adult_age_and_sex_rejected(self):
        for age in (10, -1, float("nan"), 121):
            with self.assertRaises(ValueError):
                score_psi(age)
        with self.assertRaises(ValueError):
            score_psi(60, sex="other")

    def test_mortality_increases_by_class(self):
        """Higher risk classes should have higher mortality."""
        classes = ["I", "II", "III", "IV", "V"]
        from curb65 import PSI_RISK_CLASS
        mortalities = [PSI_RISK_CLASS[c]["mortality_pct"] for c in classes]
        for i in range(len(mortalities) - 1):
            self.assertGreater(mortalities[i + 1], mortalities[i])


class TestATSIDSA(unittest.TestCase):
    """ATS/IDSA 2007 severe CAP criteria."""

    def test_no_criteria_not_severe(self):
        r = score_ats_idsa([], [])
        self.assertFalse(r["is_severe"])
        self.assertEqual(r["major_count"], 0)
        self.assertEqual(r["minor_count"], 0)

    def test_one_major_is_severe(self):
        r = score_ats_idsa(
            major_criteria=["septic_shock_requiring_vasopressors"],
            minor_criteria=[],
        )
        self.assertTrue(r["is_severe"])
        self.assertEqual(r["major_count"], 1)

    def test_two_major_is_severe(self):
        r = score_ats_idsa(
            major_criteria=[
                "septic_shock_requiring_vasopressors",
                "invasive_mechanical_ventilation",
            ],
            minor_criteria=[],
        )
        self.assertTrue(r["is_severe"])
        self.assertEqual(r["major_count"], 2)

    def test_three_minor_is_severe(self):
        r = score_ats_idsa(
            major_criteria=[],
            minor_criteria=[
                "respiratory_rate_ge_30",
                "confusion",
                "bun_ge_20",
            ],
        )
        self.assertTrue(r["is_severe"])
        self.assertEqual(r["minor_count"], 3)

    def test_two_minor_not_severe(self):
        r = score_ats_idsa(
            major_criteria=[],
            minor_criteria=["respiratory_rate_ge_30", "confusion"],
        )
        self.assertFalse(r["is_severe"])
        self.assertEqual(r["minor_count"], 2)

    def test_one_major_plus_minors_is_severe(self):
        r = score_ats_idsa(
            major_criteria=["invasive_mechanical_ventilation"],
            minor_criteria=["confusion", "bun_ge_20"],
        )
        self.assertTrue(r["is_severe"])

    def test_invalid_major_raises(self):
        with self.assertRaises(ValueError):
            score_ats_idsa(major_criteria=["bogus_criterion"])

    def test_invalid_minor_raises(self):
        with self.assertRaises(ValueError):
            score_ats_idsa(minor_criteria=["not_a_real_criterion"])

    def test_recommendation_severe(self):
        r = score_ats_idsa(major_criteria=["septic_shock_requiring_vasopressors"])
        self.assertIn("ICU", r["recommendation"])

    def test_recommendation_not_severe(self):
        r = score_ats_idsa([], ["confusion"])
        self.assertIn("standard", r["recommendation"].lower())


class TestEvaluatePatient(unittest.TestCase):
    """evaluate_patient() from dict (CSV row)."""

    def test_young_healthy(self):
        row = {"age": "30", "confusion": "0", "respiratory_rate": "18",
               "systolic_bp": "120", "diastolic_bp": "80"}
        r = evaluate_patient(row)
        self.assertEqual(r["curb65"]["score"], 0)
        self.assertEqual(r["crb65"]["score"], 0)

    def test_elderly_sick(self):
        row = {"age": "75", "confusion": "1", "urea": "10",
               "respiratory_rate": "32", "systolic_bp": "80"}
        r = evaluate_patient(row)
        self.assertEqual(r["curb65"]["score"], 5)
        self.assertEqual(r["crb65"]["score"], 4)

    def test_numeric_urea_mmol(self):
        """Urea > 7 mmol/L should trigger."""
        row = {"age": "50", "urea": "8"}
        r = evaluate_patient(row)
        self.assertTrue(r["curb65"]["criteria"]["urea_elevated"])

    def test_numeric_urea_normal(self):
        """Urea <= 7 mmol/L should not trigger."""
        row = {"age": "50", "urea": "5"}
        r = evaluate_patient(row)
        self.assertFalse(r["curb65"]["criteria"]["urea_elevated"])

    def test_completeness_signals_missing_assessments(self):
        partial = evaluate_patient({"age": "60"})
        self.assertFalse(partial["curb65_complete"])
        self.assertFalse(partial["crb65_complete"])
        self.assertIn("urea_or_bun", partial["missing_inputs"])
        complete = evaluate_patient({
            "age": "60", "confusion": "0", "respiratory_rate": "20",
            "systolic_bp": "120", "diastolic_bp": "80", "urea": "6"
        })
        self.assertTrue(complete["curb65_complete"])
        self.assertTrue(complete["crb65_complete"])

    def test_numeric_lab_units_are_not_inferred(self):
        self.assertFalse(evaluate_patient({"age": "50", "bun": "10"})["curb65"]["criteria"]["urea_elevated"])
        self.assertTrue(evaluate_patient({"age": "50", "urea": "10"})["curb65"]["criteria"]["urea_elevated"])
        self.assertFalse(evaluate_patient({"age": "50", "bun": "20"})["curb65"]["criteria"]["urea_elevated"])
        self.assertTrue(evaluate_patient({"age": "50", "bun": "21"})["curb65"]["criteria"]["urea_elevated"])

    def test_invalid_age_and_nonfinite_lab_rejected(self):
        for row in ({"age": ""}, {"age": "10"}, {"age": "65", "bun": "nan"},
                    {"age": "70", "urea": "no data"}):
            with self.assertRaises(ValueError):
                evaluate_patient(row)

    def test_bun_mgdl(self):
        """BUN > 20 mg/dL should trigger."""
        row = {"age": "50", "bun": "25"}
        r = evaluate_patient(row)
        self.assertTrue(r["curb65"]["criteria"]["urea_elevated"])

    def test_rr_boundary(self):
        """RR = 30 should trigger; RR = 29 should not."""
        row_30 = {"age": "50", "respiratory_rate": "30"}
        row_29 = {"age": "50", "respiratory_rate": "29"}
        self.assertTrue(evaluate_patient(row_30)["curb65"]["criteria"]["respiratory_rate_high"])
        self.assertFalse(evaluate_patient(row_29)["curb65"]["criteria"]["respiratory_rate_high"])

    def test_sbp_boundary(self):
        """SBP = 89 should trigger; SBP = 90 should not."""
        row_89 = {"age": "50", "systolic_bp": "89"}
        row_90 = {"age": "50", "systolic_bp": "90"}
        self.assertTrue(evaluate_patient(row_89)["curb65"]["criteria"]["blood_pressure_low"])
        self.assertFalse(evaluate_patient(row_90)["curb65"]["criteria"]["blood_pressure_low"])

    def test_dbp_boundary(self):
        """DBP = 60 should trigger; DBP = 61 should not."""
        row_60 = {"age": "50", "diastolic_bp": "60"}
        row_61 = {"age": "50", "diastolic_bp": "61"}
        self.assertTrue(evaluate_patient(row_60)["curb65"]["criteria"]["blood_pressure_low"])
        self.assertFalse(evaluate_patient(row_61)["curb65"]["criteria"]["blood_pressure_low"])

    def test_case_insensitive_keys(self):
        """Keys should be case-insensitive."""
        row = {"Age": "70", "Confusion": "1", "Respiratory_Rate": "30"}
        r = evaluate_patient(row)
        self.assertEqual(r["curb65"]["score"], 3)  # age + confusion + RR

    def test_explicit_flags(self):
        """Explicit boolean flags should work."""
        row = {"age": "50", "confusion": "true", "urea_elevated": "yes",
               "respiratory_rate_high": "y", "blood_pressure_low": "1"}
        r = evaluate_patient(row)
        self.assertEqual(r["curb65"]["score"], 4)


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing and output."""

    def setUp(self):
        from cli import build_parser
        self.parser = build_parser()

    def test_score_basic(self):
        args = self.parser.parse_args(["score", "--age", "70"])
        self.assertEqual(args.cmd, "score")
        self.assertEqual(args.age, 70)

    def test_score_with_flags(self):
        args = self.parser.parse_args([
            "score", "--confusion", "--urea", "25", "--rr", "32",
            "--sbp", "85", "--age", "70",
        ])
        self.assertTrue(args.confusion)
        self.assertEqual(args.urea, 25)
        self.assertEqual(args.rr, 32)
        self.assertEqual(args.sbp, 85)
        self.assertEqual(args.age, 70)

    def test_crb65_basic(self):
        args = self.parser.parse_args(["crb65", "--confusion", "--age", "70"])
        self.assertEqual(args.cmd, "crb65")
        self.assertTrue(args.confusion)

    def test_batch_args(self):
        args = self.parser.parse_args(["batch", "--input", "in.csv", "--output", "out.csv"])
        self.assertEqual(args.cmd, "batch")
        self.assertEqual(args.input, "in.csv")
        self.assertEqual(args.output, "out.csv")

    def test_cli_score_integration(self):
        """Run CLI score command and verify output."""
        from cli import main
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            rc = main(["score", "--confusion", "--urea", "25", "--rr", "32",
                        "--sbp", "85", "--age", "70"])
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("5", output)  # score should be 5
        self.assertIn("ICU", output)

    def test_cli_score_json(self):
        """CLI score with --json should produce valid JSON."""
        from cli import main
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            rc = main(["score", "--age", "30", "--json"])
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        self.assertEqual(rc, 0)
        data = json.loads(output)
        self.assertEqual(data["score"], 0)

    def test_cli_crb65_integration(self):
        """Run CLI crb65 command."""
        from cli import main
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            rc = main(["crb65", "--confusion", "--rr", "32", "--sbp", "85", "--age", "70"])
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("4", output)  # all 4 CRB-65 criteria


class TestBatchCSV(unittest.TestCase):
    """Test batch CSV processing."""

    def test_batch_processing(self):
        """Write a temp CSV, process it, verify output."""
        from cli import main

        # Create temp input CSV
        input_data = [
            {"patient_id": "P001", "age": "30", "confusion": "0",
             "respiratory_rate": "18", "systolic_bp": "120", "diastolic_bp": "80"},
            {"patient_id": "P002", "age": "75", "confusion": "1", "urea": "10",
             "respiratory_rate": "32", "systolic_bp": "80"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                          newline="") as f:
            fieldnames = ["patient_id", "age", "confusion", "urea",
                          "respiratory_rate", "systolic_bp", "diastolic_bp"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(input_data)
            input_path = f.name

        output_path = input_path.replace(".csv", "_out.csv")

        try:
            rc = main(["batch", "--input", input_path, "--output", output_path])
            self.assertEqual(rc, 0)

            with open(output_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 2)

            # P001: young, healthy -> score 0
            self.assertEqual(int(rows[0]["curb65_score"]), 0)
            self.assertIn("outpatient", rows[0]["curb65_management"].lower())

            # P002: elderly, confused, high urea, high RR, low BP -> score 5
            self.assertEqual(int(rows[1]["curb65_score"]), 5)
            self.assertIn("ICU", rows[1]["curb65_management"])

        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestCLIWithSampleCSV(unittest.TestCase):
    """Test batch processing with the project's sample.csv."""

    def test_sample_csv(self):
        """Process sample.csv and verify it runs without error."""
        from cli import main

        sample_path = os.path.join(os.path.dirname(__file__), "sample.csv")
        if not os.path.exists(sample_path):
            self.skipTest("sample.csv not found")

        output_path = os.path.join(tempfile.gettempdir(), "test_sample_out.csv")
        try:
            rc = main(["batch", "--input", sample_path, "--output", output_path])
            self.assertEqual(rc, 0)

            with open(output_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertGreater(len(rows), 0)
            # Verify output has the expected columns
            self.assertIn("curb65_score", rows[0])
            self.assertIn("crb65_score", rows[0])
            self.assertIn("curb65_management", rows[0])
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
