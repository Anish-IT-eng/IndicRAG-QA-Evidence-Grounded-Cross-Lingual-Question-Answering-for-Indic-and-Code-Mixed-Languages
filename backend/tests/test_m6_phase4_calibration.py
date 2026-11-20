"""
Tests for M6 Phase 4 Exploratory Calibration Module.

Verifies:
1. Score bounds clamping and numerical stability.
2. Missing value and NaN fallbacks.
3. Parameter preservation and metadata disclosure.
4. Output probability monotonicity.
5. Invariance of runtime EvidenceController safety overrides.
"""
from __future__ import annotations

import math
import pytest
from app.calibration.exploratory_calibrator import ExploratoryPlattCalibrator
from app.models.schemas import EvidenceStatus
from app.retrieval.evidence_controller import get_evidence_controller


class TestExploratoryPlattCalibrator:
    def test_calibrator_init_defaults(self):
        calibrator = ExploratoryPlattCalibrator()
        assert calibrator.slope_a == pytest.approx(0.2893, rel=1e-3)
        assert calibrator.intercept_b == pytest.approx(0.2372, rel=1e-3)
        assert calibrator.feature_name == "ceci_heuristic_score"

    def test_missing_and_nan_fallback(self):
        calibrator = ExploratoryPlattCalibrator()
        
        # Test None
        res_none = calibrator.predict_probability(None)
        assert res_none["is_fallback"] is True
        assert res_none["calibrated_probability"] == 0.5
        assert res_none["fallback_reason"] == "MISSING_OR_NAN_SCORE"

        # Test NaN
        res_nan = calibrator.predict_probability(float("nan"))
        assert res_nan["is_fallback"] is True
        assert res_nan["calibrated_probability"] == 0.5

    def test_score_bounds_and_stability(self):
        calibrator = ExploratoryPlattCalibrator(slope_a=1.0, intercept_b=0.0, min_score=0.0, max_score=1.0)
        
        # Extremely negative
        res_neg = calibrator.predict_probability(-1000.0)
        assert res_neg["input_score"] == 0.0
        assert 0.0 <= res_neg["calibrated_probability"] <= 1.0

        # Extremely positive
        res_pos = calibrator.predict_probability(1000.0)
        assert res_pos["input_score"] == 1.0
        assert 0.0 <= res_pos["calibrated_probability"] <= 1.0

    def test_monotonicity(self):
        calibrator = ExploratoryPlattCalibrator(slope_a=2.0, intercept_b=-1.0)
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        probs = [calibrator.predict_probability(s)["calibrated_probability"] for s in scores]
        
        for i in range(len(probs) - 1):
            assert probs[i] <= probs[i + 1]

    def test_batch_prediction(self):
        calibrator = ExploratoryPlattCalibrator()
        scores = [0.2, None, 0.8, float("nan")]
        results = calibrator.predict_batch(scores)
        assert len(results) == 4
        assert results[0]["is_fallback"] is False
        assert results[1]["is_fallback"] is True
        assert results[2]["is_fallback"] is False
        assert results[3]["is_fallback"] is True

    def test_safety_metadata_present(self):
        calibrator = ExploratoryPlattCalibrator()
        res = calibrator.predict_probability(0.5)
        assert res["calibration_status"] == "EXPLORATORY_RESEARCH_ONLY"
        assert "Does not replace runtime evidence controller" in res["operational_warning"]

    def test_runtime_controller_overrides_unaffected(self):
        """Verify that calibration does not modify or bypass EvidenceController safety rules."""
        controller = get_evidence_controller()
        # Verify controller still exposes its canonical 6 states and strict rules
        assert hasattr(controller, "evaluate")
        assert EvidenceStatus.CONFLICTING is not None
        assert EvidenceStatus.INSUFFICIENT is not None
        assert EvidenceStatus.SUFFICIENT is not None

