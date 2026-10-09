"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { computeScores } = require("../web/app.js");

const baseline = {
  age: 45, respiratoryRate: 18, systolic: 120, diastolic: 80,
  confusion: false, labUnit: "urea", labValue: 5
};

test("zero criteria with all data", () => {
  assert.deepEqual([computeScores(baseline).crb65, computeScores(baseline).curb65], [0, 0]);
});

test("five CURB-65 criteria at clinical boundaries", () => {
  const result = computeScores({
    age: 65, respiratoryRate: 30, systolic: 90, diastolic: 60,
    confusion: true, labUnit: "bun", labValue: 21
  });
  assert.equal(result.curb65, 5);
  assert.equal(result.crb65, 4);
});

test("exact urea and BUN thresholds do not score", () => {
  assert.equal(computeScores({ ...baseline, labUnit: "urea", labValue: 7 }).curb65, 0);
  assert.equal(computeScores({ ...baseline, labUnit: "bun", labValue: 20 }).curb65, 0);
  assert.equal(computeScores({ ...baseline, labUnit: "urea", labValue: 7.1 }).curb65, 1);
  assert.equal(computeScores({ ...baseline, labUnit: "bun", labValue: 20.1 }).curb65, 1);
});

test("blood-pressure, respiratory rate, and age boundaries", () => {
  assert.equal(computeScores({ ...baseline, systolic: 89 }).crb65, 1);
  assert.equal(computeScores({ ...baseline, systolic: 90, diastolic: 61 }).crb65, 0);
  assert.equal(computeScores({ ...baseline, respiratoryRate: 30 }).crb65, 1);
  assert.equal(computeScores({ ...baseline, age: 65 }).crb65, 1);
});

test("CRB-65 only when laboratory testing is unavailable", () => {
  const result = computeScores({ ...baseline, labUnit: "none", labValue: null });
  assert.equal(result.crb65, 0);
  assert.equal(result.curb65, null);
});

test("invalid or missing measurements fail explicitly", () => {
  for (const changes of [
    { age: NaN }, { age: 17 }, { age: 121 }, { age: 65.5 },
    { respiratoryRate: NaN }, { systolic: 70, diastolic: 80 },
    { labUnit: "invalid" }, { labValue: NaN }, { labValue: -2 },
    { confusion: "false" }
  ]) {
    assert.throws(() => computeScores({ ...baseline, ...changes }));
  }
});
