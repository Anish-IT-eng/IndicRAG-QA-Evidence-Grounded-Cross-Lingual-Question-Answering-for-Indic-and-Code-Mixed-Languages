"""
IndicRAG-QA — Exploratory Calibration Module (Research Mode Only).

IMPORTANT:
- This module is strictly for exploratory research and offline evaluation.
- It does NOT replace or modify the runtime EvidenceController thresholds.
- All safety overrides (version conflicts, ungrounded claims, zero citations) remain authoritative.
- Implements univariate Platt scaling (logistic sigmoid) with parameter bounds, missing value safety,
  and numerical stability protection.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class ExploratoryPlattCalibrator:
    """
    Research-only univariate Platt calibrator.
    Maps an uncalibrated continuous score s into an empirical probability estimate p:
        p(s) = 1 / (1 + exp(-(A * s + B)))
    
    Includes:
    - Parameter bounds and stability clamping.
    - Missing value handling.
    - Explicit disclaimer metadata designating scores as exploratory research estimates.
    """

    def __init__(
        self,
        slope_a: float = 0.2893,
        intercept_b: float = 0.2372,
        feature_name: str = "ceci_heuristic_score",
        min_score: float = 0.0,
        max_score: float = 1.0,
    ) -> None:
        self.slope_a = float(slope_a)
        self.intercept_b = float(intercept_b)
        self.feature_name = feature_name
        self.min_score = min_score
        self.max_score = max_score
        self._is_fitted = True

    def predict_probability(self, score: Optional[float]) -> Dict[str, Any]:
        """
        Calibrates a single input score.
        Returns a dictionary with probability, input score, and safety metadata.
        """
        if score is None or math.isnan(score):
            return {
                "calibrated_probability": 0.5,
                "input_score": None,
                "is_fallback": True,
                "fallback_reason": "MISSING_OR_NAN_SCORE",
                "calibration_status": "EXPLORATORY_RESEARCH_ONLY",
                "operational_warning": "Do not use as production confidence guarantee."
            }

        # Clamp input score to expected operational bounds
        clamped_score = max(self.min_score, min(float(score), self.max_score))
        
        # Linear log-odds
        z = (self.slope_a * clamped_score) + self.intercept_b
        
        # Numerically stable sigmoid
        if z >= 0:
            prob = 1.0 / (1.0 + math.exp(-z))
        else:
            exp_z = math.exp(z)
            prob = exp_z / (1.0 + exp_z)

        return {
            "calibrated_probability": round(float(prob), 4),
            "input_score": round(clamped_score, 4),
            "is_fallback": False,
            "fallback_reason": None,
            "calibration_status": "EXPLORATORY_RESEARCH_ONLY",
            "fitted_parameters": {
                "slope_a": self.slope_a,
                "intercept_b": self.intercept_b,
                "feature": self.feature_name
            },
            "operational_warning": "Exploratory research estimate. Does not replace runtime evidence controller safety rules."
        }

    def predict_batch(self, scores: List[Optional[float]]) -> List[Dict[str, Any]]:
        return [self.predict_probability(s) for s in scores]

