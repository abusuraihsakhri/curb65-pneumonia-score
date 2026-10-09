"use strict";

/** Pure adult CURB-65 / CRB-65 calculator; no network calls or persistence. */
function computeScores({ age, respiratoryRate, systolic, diastolic, confusion, labUnit, labValue }) {
  function inRange(value, lower, upper, name) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < lower || value > upper) {
      throw new RangeError(name + " must be between " + lower + " and " + upper + ".");
    }
  }
  inRange(age, 18, 120, "Age (years)");
  if (!Number.isInteger(age)) throw new RangeError("Age must be a whole number.");
  inRange(respiratoryRate, 1, 100, "Respiratory rate");
  inRange(systolic, 40, 300, "Systolic blood pressure");
  inRange(diastolic, 20, 200, "Diastolic blood pressure");
  if (diastolic > systolic) throw new RangeError("Diastolic blood pressure cannot exceed systolic.");
  if (typeof confusion !== "boolean") throw new TypeError("Confusion must be a boolean value.");
  if (!["urea", "bun", "none"].includes(labUnit)) throw new RangeError("Invalid laboratory unit.");
  if (labUnit === "urea") inRange(labValue, 0, 80, "Urea (mmol/L)");
  if (labUnit === "bun") inRange(labValue, 0, 200, "BUN (mg/dL)");

  const flags = {
    confusion,
    respiratoryRateHigh: respiratoryRate >= 30,
    bloodPressureLow: systolic < 90 || diastolic <= 60,
    age65: age >= 65
  };
  const crb65 = Object.values(flags).filter(Boolean).length;
  const labElevated = labUnit === "urea" ? labValue > 7 : labUnit === "bun" ? labValue > 20 : null;
  return {
    crb65,
    curb65: labElevated === null ? null : crb65 + Number(labElevated),
    labElevated,
    flags
  };
}

if (typeof module !== "undefined" && module.exports) module.exports = { computeScores };

if (typeof document !== "undefined") {
  const form = document.getElementById("score-form");
  const result = document.getElementById("result");
  const errors = document.getElementById("errors");
  const labUnit = document.getElementById("lab-unit");
  const labWrap = document.getElementById("lab-wrap");
  const labLabel = document.getElementById("lab-label");
  const labInput = document.getElementById("lab-value");
  const criteria = document.getElementById("criteria");

  function toggleLab() {
    const unit = labUnit.value;
    labWrap.hidden = unit === "none";
    labInput.required = unit !== "none";
    labInput.value = "";
    if (unit === "urea") {
      labLabel.textContent = "Serum urea (mmol/L)";
      labInput.max = "80";
      labInput.step = "0.1";
    } else if (unit === "bun") {
      labLabel.textContent = "Blood urea nitrogen (mg/dL)";
      labInput.max = "200";
      labInput.step = "0.1";
    }
  }
  labUnit.addEventListener("change", toggleLab);

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    errors.textContent = "";
    result.hidden = true;
    try {
      const input = {
        age: document.getElementById("age").valueAsNumber,
        respiratoryRate: document.getElementById("rr").valueAsNumber,
        systolic: document.getElementById("sbp").valueAsNumber,
        diastolic: document.getElementById("dbp").valueAsNumber,
        confusion: document.getElementById("confusion").checked,
        labUnit: labUnit.value,
        labValue: labUnit.value === "none" ? null : labInput.valueAsNumber
      };
      const scores = computeScores(input);
      document.getElementById("crb-score").textContent = scores.crb65 + " / 4";
      document.getElementById("curb-score").textContent =
        scores.curb65 === null ? "Not available (no urea/BUN)" : scores.curb65 + " / 5";
      const score = scores.curb65 === null ? scores.crb65 : scores.curb65;
      const isCrb = scores.curb65 === null;
      let interpretation;
      if (isCrb) {
        interpretation = score === 0 ? "CRB-65 0: lower risk; assess all other clinical factors." :
          score <= 2 ? "CRB-65 1–2: increased risk; prompt clinical evaluation is needed." :
          "CRB-65 3–4: high risk; urgent hospital assessment is indicated.";
      } else {
        interpretation = score <= 1 ? "CURB-65 0–1: lower score; outpatient care may be considered after clinical assessment." :
          score === 2 ? "CURB-65 2: intermediate severity; hospital or supervised care should be considered." :
          "CURB-65 3–5: severe score; urgent hospital assessment and evaluation for higher-level care.";
      }
      document.getElementById("interpretation").textContent = interpretation;
      const checks = [
        ["New-onset confusion", scores.flags.confusion],
        ["Respiratory rate ≥30/min", scores.flags.respiratoryRateHigh],
        ["Systolic <90 or diastolic ≤60 mmHg", scores.flags.bloodPressureLow],
        ["Age ≥65 years", scores.flags.age65]
      ];
      if (scores.labElevated !== null) {
        checks.splice(1, 0, ["Urea >7 mmol/L or BUN >20 mg/dL", scores.labElevated]);
      }
      criteria.replaceChildren();
      for (const [name, met] of checks) {
        const li = document.createElement("li");
        li.textContent = (met ? "Met: " : "Not met: ") + name;
        li.className = met ? "met" : "not-met";
        criteria.appendChild(li);
      }
      result.hidden = false;
      result.focus();
    } catch (error) {
      errors.textContent = error.message || "Unable to calculate from these inputs.";
    }
  });
  form.addEventListener("reset", function () {
    result.hidden = true;
    errors.textContent = "";
    // reset event precedes resetting the control values
    labWrap.hidden = false;
    labInput.required = true;
    labLabel.textContent = "Serum urea (mmol/L)";
    labInput.max = "80";
  });
}
