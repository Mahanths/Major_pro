"""
Trust Calculator Module
Implements the Trust Score formula per architecture specification.

Formula: T_new = λ * T_old - (α * P_malicious) - (β * S_anomaly) + R_bonus

Where:
  λ (lambda) = decay factor (historical weight)
  α (alpha) = malicious penalty weight
  β (beta) = anomaly penalty weight
  R_bonus = recovery bonus if clean
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TrustCalculator:
    """Calculates dynamic trust scores for network flows."""

    # Model Parameters (tunable)
    LAMBDA_DECAY = 0.90  # How much to weight historical trust
    ALPHA_MALICIOUS = 40.0  # Penalty multiplier for XGBoost malicious probability
    BETA_ANOMALY = 25.0  # Penalty multiplier for Isolation Forest anomaly score
    RECOVERY_BONUS = 0.5  # Points added per N seconds of clean traffic
    RECOVERY_INTERVAL = 5.0  # Seconds between recovery bonus applications

    # Trust Range Constants
    MIN_TRUST = 0.0
    MAX_TRUST = 100.0
    INITIAL_TRUST = 100.0  # "Trust but Verify" default for internal assets

    # Policy Decision Thresholds
    THRESHOLD_TRUSTED = 80  # >= 80: Allow
    THRESHOLD_SUSPICIOUS = 60  # 60-79: Verify
    THRESHOLD_DEGRADED = 40  # 40-59: Limit
    # < 40: Block

    def __init__(self):
        """Initialize trust calculator with default parameters."""
        self.trust_history = {}  # {flow_id: {"trust": 100.0, "last_clean": time}}
        logger.info("TrustCalculator initialized")

    def calculate_trust(
        self,
        flow_id: str,
        ml_malicious_probability: float,
        ml_anomaly_score: float,
        is_clean_traffic: bool = False,
    ) -> Dict:
        """
        Calculate new trust score for a flow.

        Args:
            flow_id: Unique identifier for flow (e.g., "src_ip:dst_ip:sport:dport")
            ml_malicious_probability: XGBoost output [0-1]
            ml_anomaly_score: Isolation Forest output [0-1]
            is_clean_traffic: Override flag if traffic known to be clean

        Returns:
            Dict with keys:
                - trust_score: New trust score [0-100]
                - old_trust: Previous trust value
                - policy: Action name (ALLOW, VERIFY, LIMIT, BLOCK)
                - penalty: Total penalty applied
                - recovery_applied: Whether recovery bonus was added
        """
        try:
            # Get historical trust (default to INITIAL_TRUST if new flow)
            old_trust = self.trust_history.get(flow_id, {}).get(
                "trust", self.INITIAL_TRUST
            )

            # Start with decay of historical trust
            trust_new = self.LAMBDA_DECAY * old_trust

            penalty_malicious = 0.0
            penalty_anomaly = 0.0
            recovery_applied = False

            if is_clean_traffic:
                # Clean traffic gets recovery bonus
                recovery_bonus = self.RECOVERY_BONUS
                trust_new += recovery_bonus
                recovery_applied = True
                logger.debug(
                    f"Flow {flow_id}: Clean traffic detected, +{recovery_bonus} recovery bonus"
                )
            else:
                # Apply penalties based on ML scores
                penalty_malicious = self.ALPHA_MALICIOUS * ml_malicious_probability
                penalty_anomaly = self.BETA_ANOMALY * ml_anomaly_score

                trust_new -= penalty_malicious
                trust_new -= penalty_anomaly

                logger.debug(
                    f"Flow {flow_id}: Malicious penalty={penalty_malicious:.2f}, "
                    f"Anomaly penalty={penalty_anomaly:.2f}"
                )

            # Clamp trust score to [0, 100]
            trust_new = max(self.MIN_TRUST, min(self.MAX_TRUST, trust_new))

            # Determine policy based on trust threshold
            policy = self._get_policy_from_trust(trust_new)

            # Update history
            self.trust_history[flow_id] = {"trust": trust_new}

            result = {
                "flow_id": flow_id,
                "trust_score": round(trust_new, 2),
                "old_trust": round(old_trust, 2),
                "penalty_malicious": round(penalty_malicious, 2),
                "penalty_anomaly": round(penalty_anomaly, 2),
                "total_penalty": round(penalty_malicious + penalty_anomaly, 2),
                "recovery_applied": recovery_applied,
                "policy": policy,
                "threshold_block": self.THRESHOLD_DEGRADED,
                "threshold_limit": self.THRESHOLD_DEGRADED,
                "threshold_verify": self.THRESHOLD_SUSPICIOUS,
                "threshold_allow": self.THRESHOLD_TRUSTED,
            }

            logger.info(
                f"Trust update: flow={flow_id}, trust={result['trust_score']}, policy={policy}"
            )
            return result

        except Exception as e:
            logger.error(f"Trust calculation error for flow {flow_id}: {e}")
            return {
                "flow_id": flow_id,
                "trust_score": 0.0,
                "old_trust": 0.0,
                "penalty_malicious": 0.0,
                "penalty_anomaly": 0.0,
                "total_penalty": 0.0,
                "recovery_applied": False,
                "policy": "BLOCK",
                "error": str(e),
            }

    def _get_policy_from_trust(self, trust_score: float) -> str:
        """Map trust score to policy decision."""
        if trust_score >= self.THRESHOLD_TRUSTED:
            return "ALLOW"
        elif trust_score >= self.THRESHOLD_SUSPICIOUS:
            return "VERIFY"
        elif trust_score >= self.THRESHOLD_DEGRADED:
            return "LIMIT"
        else:
            return "BLOCK"

    def get_trust_state(self, flow_id: str) -> Dict:
        """Retrieve current trust state for a flow."""
        if flow_id in self.trust_history:
            return {
                "flow_id": flow_id,
                "trust_score": self.trust_history[flow_id]["trust"],
                "policy": self._get_policy_from_trust(
                    self.trust_history[flow_id]["trust"]
                ),
            }
        return {
            "flow_id": flow_id,
            "trust_score": self.INITIAL_TRUST,
            "policy": "ALLOW",  # New flows default to ALLOW with verification
        }

    def reset_flow(self, flow_id: str) -> None:
        """Reset trust history for a flow (e.g., after timeout or policy change)."""
        if flow_id in self.trust_history:
            del self.trust_history[flow_id]
            logger.info(f"Trust history reset for flow {flow_id}")
