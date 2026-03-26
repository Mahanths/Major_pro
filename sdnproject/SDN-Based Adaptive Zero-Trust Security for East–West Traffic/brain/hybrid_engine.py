"""
Hybrid ML Inference Engine
Two-tier verification pipeline:
  Tier 1: Isolation Forest (unsupervised anomaly detection)
  Tier 2: XGBoost (supervised malicious classification)

Only runs Tier 2 if Tier 1 flags anomaly.
"""

import logging
import os
import json
from typing import Dict, Tuple, Optional
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
import xgboost as xgb

logger = logging.getLogger(__name__)


class HybridEngine:
    """Two-tier ML inference engine for zero-trust decision making."""

    def __init__(self, model_dir: str = "brain/models"):
        """
        Initialize the hybrid ML engine.

        Args:
            model_dir: Path to directory containing trained .pkl models
        """
        self.model_dir = model_dir
        self.isolation_forest = None
        self.xgboost_model = None
        self.is_ready = False
        self.use_mock_models = True  # Default to mock for dev until real models exist

        # Load models if they exist
        self._load_models()

    def _load_models(self) -> None:
        """Load pre-trained models from disk if available."""
        iso_forest_path = os.path.join(
            self.model_dir, "isolation_forest_model.pkl"
        )
        xgboost_path = os.path.join(self.model_dir, "xgboost_model.pkl")

        try:
            if os.path.exists(iso_forest_path):
                self.isolation_forest = joblib.load(iso_forest_path)
                logger.info(f"Loaded Isolation Forest from {iso_forest_path}")
            else:
                logger.warning(
                    f"Isolation Forest model not found at {iso_forest_path}, using mock"
                )

            if os.path.exists(xgboost_path):
                self.xgboost_model = joblib.load(xgboost_path)
                logger.info(f"Loaded XGBoost from {xgboost_path}")
            else:
                logger.warning(
                    f"XGBoost model not found at {xgboost_path}, using mock"
                )

            if self.isolation_forest and self.xgboost_model:
                self.is_ready = True
                self.use_mock_models = False
                logger.info("✓ Hybrid engine ready with real models")
            else:
                logger.warning(
                    "⚠ Running in MOCK MODE. Please train models via training/train_models.py"
                )

        except Exception as e:
            logger.error(f"Error loading models: {e}. Falling back to mock mode.")

    def infer(
        self, features: np.ndarray, flow_metadata: Dict = None
    ) -> Dict:
        """
        Run two-tier inference on feature vector.

        Args:
            features: numpy array of shape (8,) with ML features
            flow_metadata: Optional dict with src_ip, dst_ip, etc.

        Returns:
            Dict with keys:
                - tier1_anomaly_score: Isolation Forest output [-1, 1]
                - tier1_is_anomaly: Boolean (True if -1)
                - tier2_malicious_probability: XGBoost probability [0, 1]
                - tier2_triggered: Boolean (True if Tier 1 flagged)
                - final_malicious_probability: Recommended value for trust calc
                - inference_latency_ms: Total inference time
                - models_ready: Whether real models loaded
        """
        import time

        start_time = time.time()

        try:
            # Input validation
            if features is None or len(features) != 8:
                logger.error(
                    f"Invalid feature vector: expected length 8, got {len(features) if features is not None else 0}"
                )
                return self._error_response("Invalid feature vector")

            features = np.array(features).reshape(1, -1).astype(np.float32)

            # === TIER 1: Isolation Forest (Anomaly Detection) ===
            tier1_anomaly_score, tier1_is_anomaly = self._tier1_anomaly_detection(
                features
            )

            # === TIER 2: XGBoost (Malicious Classification) ===
            # Only run if Tier 1 flagged anomaly (optimization)
            tier2_triggered = tier1_is_anomaly
            tier2_malicious_probability = 0.0

            if tier2_triggered:
                tier2_malicious_probability = self._tier2_classification(features)

            # Final recommendation for trust calculator
            final_malicious_prob = (
                tier2_malicious_probability if tier2_triggered else 0.0
            )

            inference_time = (time.time() - start_time) * 1000  # milliseconds

            result = {
                "tier1_anomaly_score": float(tier1_anomaly_score),
                "tier1_is_anomaly": bool(tier1_is_anomaly),
                "tier2_triggered": bool(tier2_triggered),
                "tier2_malicious_probability": float(tier2_malicious_probability),
                "final_malicious_probability": float(final_malicious_prob),
                "inference_latency_ms": round(inference_time, 3),
                "models_ready": self.is_ready,
                "using_mock_models": self.use_mock_models,
            }

            logger.debug(
                f"Inference complete: anomaly={tier1_is_anomaly}, "
                f"malicious_prob={final_malicious_prob:.3f}, "
                f"latency={inference_time:.1f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            return self._error_response(str(e))

    def _tier1_anomaly_detection(self, features: np.ndarray) -> Tuple[float, bool]:
        """
        Tier 1: Isolation Forest for unsupervised anomaly detection.

        Returns:
            (anomaly_score: float [-1, 1], is_anomaly: bool)
            -1 = anomalies, +1 = normal
        """
        try:
            if self.use_mock_models:
                # Mock: anomaly if feature sum is extreme
                feature_sum = float(np.sum(features))
                if feature_sum > 6.0 or feature_sum < 0.5:
                    return (-1.0, True)  # Anomalous
                return (1.0, False)  # Normal

            if self.isolation_forest is None:
                logger.warning("Isolation Forest not available")
                return (0.0, False)

            prediction = self.isolation_forest.predict(features)[0]
            return (float(prediction), bool(prediction == -1))

        except Exception as e:
            logger.error(f"Tier 1 detection error: {e}")
            return (0.0, False)

    def _tier2_classification(self, features: np.ndarray) -> float:
        """
        Tier 2: XGBoost for supervised malicious classification.

        Returns:
            malicious_probability: float [0-1]
        """
        try:
            if self.use_mock_models:
                # Mock: use feature anomaly as proxy
                feature_mean = float(np.mean(features))
                high_entropy_features = float(features[0, 4])  # 5th feature = dst_ports
                malicious_prob = min(
                    (high_entropy_features * 0.7) + (feature_mean * 0.3), 1.0
                )
                return malicious_prob

            if self.xgboost_model is None:
                logger.warning("XGBoost model not available")
                return 0.0

            # XGBoost predict_proba returns probabilities for both classes
            predictions = self.xgboost_model.predict_proba(features)
            malicious_probability = predictions[0, 1]  # Probability of class 1
            return float(malicious_probability)

        except Exception as e:
            logger.error(f"Tier 2 classification error: {e}")
            return 0.0

    def _error_response(self, error_msg: str) -> Dict:
        """Generate error response."""
        return {
            "tier1_anomaly_score": 0.0,
            "tier1_is_anomaly": False,
            "tier2_triggered": False,
            "tier2_malicious_probability": 0.0,
            "final_malicious_probability": 0.0,
            "inference_latency_ms": 0.0,
            "models_ready": self.is_ready,
            "using_mock_models": self.use_mock_models,
            "error": error_msg,
        }

    def get_model_status(self) -> Dict:
        """Return current model loading status."""
        return {
            "isolation_forest_loaded": self.isolation_forest is not None,
            "xgboost_loaded": self.xgboost_model is not None,
            "engine_ready": self.is_ready,
            "using_mock_models": self.use_mock_models,
            "model_directory": self.model_dir,
        }
