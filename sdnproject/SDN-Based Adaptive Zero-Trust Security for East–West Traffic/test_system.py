"""
COMPREHENSIVE TEST SUITE
Tests the entire zero-trust system end-to-end.

Usage:
    # Test 1: Unit tests
    python test_system.py --test unit
    
    # Test 2: Integration tests
    python test_system.py --test integration
    
    # Test 3: Attack simulation tests
    python test_system.py --test attacks
    
    # All tests
    python test_system.py --test all
"""

import sys
import os
import json
import logging
import random
from typing import Dict, List
import numpy as np

# Add brain module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brain.feature_handler import FeatureHandler
from brain.hybrid_engine import HybridEngine
from brain.trust_calculator import TrustCalculator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TestSuite:
    """Comprehensive test suite for zero-trust system."""

    def __init__(self):
        """Initialize all components."""
        self.feature_handler = FeatureHandler()
        self.ml_engine = HybridEngine()
        self.trust_calculator = TrustCalculator()
        self.test_results = {"passed": 0, "failed": 0, "errors": []}

    # ========================================================================
    # TEST 1: UNIT TESTS (Feature Extraction, ML Inference, Trust Calc)
    # ========================================================================

    def test_feature_extraction(self) -> bool:
        """Test 8-feature extraction from telemetry."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.1: Feature Extraction Module")
        logger.info("=" * 80)

        test_telemetry = {
            "flow_duration": 10.0,
            "fwd_packets": 100,
            "bwd_packets": 95,
            "fwd_bytes": 50000,
            "bwd_bytes": 45000,
            "dst_ports": [443, 80],
            "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
            "inter_arrival_times": [0.05, 0.05, 0.1, 0.05],
        }

        try:
            features = self.feature_handler.extract_features(test_telemetry)

            # Validate output
            assert len(features) == 8, f"Expected 8 features, got {len(features)}"
            assert all(
                0 <= f <= 1 for f in features
            ), "Features not in [0, 1] range"

            logger.info(f"✓ Extracted 8 features: {features}")
            logger.info(f"  Feature names: {self.feature_handler.feature_names}")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ Feature extraction failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_ml_inference_normal_traffic(self) -> bool:
        """Test Tier 1 + Tier 2 inference on normal traffic."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.2: ML Inference - Normal Traffic")
        logger.info("=" * 80)

        try:
            # Normal traffic: low packet rate, low entropy, single port
            normal_features = np.array([0.1, 0.05, 0.04, 0.1, 0.1, 0.1, 0.1, 0.2])

            result = self.ml_engine.infer(normal_features)

            logger.info(f"Tier 1 Anomaly Score: {result['tier1_anomaly_score']}")
            logger.info(f"Tier 1 Is Anomaly: {result['tier1_is_anomaly']}")
            logger.info(f"Tier 2 Triggered: {result['tier2_triggered']}")
            logger.info(
                f"Final Malicious Probability: {result['final_malicious_probability']}"
            )

            # Normal traffic should NOT be flagged as anomaly
            assert (
                result["final_malicious_probability"] < 0.3
            ), "Normal traffic flagged as malicious!"

            logger.info("✓ Normal traffic correctly identified")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ ML inference failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_ml_inference_attack_traffic(self) -> bool:
        """Test Tier 1 + Tier 2 inference on attack-like traffic."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.3: ML Inference - Attack-Like Traffic")
        logger.info("=" * 80)

        try:
            # Attack: high packet rate, many ports scanned, unusual timing
            attack_features = np.array([0.8, 0.9, 0.1, 0.7, 0.9, 0.8, 0.05, 0.95])

            result = self.ml_engine.infer(attack_features)

            logger.info(f"Tier 1 Anomaly Score: {result['tier1_anomaly_score']}")
            logger.info(f"Tier 1 Is Anomaly: {result['tier1_is_anomaly']}")
            logger.info(f"Tier 2 Triggered: {result['tier2_triggered']}")
            logger.info(
                f"Final Malicious Probability: {result['final_malicious_probability']}"
            )

            # Attack traffic should be flagged as anomaly
            assert (
                result["tier1_is_anomaly"] == True
            ), "Attack traffic not flagged as anomaly!"

            logger.info("✓ Attack traffic correctly detected as anomaly")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ ML inference failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_trust_calculation_normal(self) -> bool:
        """Test trust score calculation for normal traffic."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.4: Trust Score - Normal Traffic")
        logger.info("=" * 80)

        try:
            flow_id = "192.168.1.10:192.168.1.20:50000:443"
            result = self.trust_calculator.calculate_trust(
                flow_id=flow_id,
                ml_malicious_probability=0.0,
                ml_anomaly_score=0.0,
                is_clean_traffic=True,
            )

            logger.info(f"Old Trust: {result['old_trust']}")
            logger.info(f"New Trust: {result['trust_score']}")
            logger.info(f"Policy: {result['policy']}")

            # Should remain high (ALLOW policy)
            assert result["policy"] == "ALLOW", f"Expected ALLOW, got {result['policy']}"
            assert (
                result["trust_score"] >= 70
            ), "Trust score dropped unexpectedly for clean traffic"

            logger.info("✓ Trust score correctly maintained for clean traffic")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ Trust calculation failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_trust_calculation_attack(self) -> bool:
        """Test trust score calculation for attack traffic."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1.5: Trust Score - Attack Traffic")
        logger.info("=" * 80)

        try:
            flow_id = "10.0.0.100:192.168.1.50:65535:22"
            result = self.trust_calculator.calculate_trust(
                flow_id=flow_id,
                ml_malicious_probability=0.95,  # 95% malicious
                ml_anomaly_score=-1.0,  # Anomaly detected
                is_clean_traffic=False,
            )

            logger.info(f"Old Trust: {result['old_trust']}")
            logger.info(f"New Trust: {result['trust_score']}")
            logger.info(f"Total Penalty: {result['total_penalty']}")
            logger.info(f"Policy: {result['policy']}")

            # Should drop to BLOCK
            assert (
                result["policy"] == "BLOCK"
            ), f"Expected BLOCK, got {result['policy']}"
            assert (
                result["trust_score"] < 40
            ), f"Trust score should be < 40 for attack, got {result['trust_score']}"

            logger.info("✓ Trust score correctly dropped for malicious traffic")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ Trust calculation failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    # ========================================================================
    # TEST 2: INTEGRATION TESTS (Full Pipeline)
    # ========================================================================

    def test_end_to_end_pipeline(self) -> bool:
        """Test complete pipeline: telemetry → features → ML → trust → policy."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2.1: End-to-End Pipeline - Normal Flow")
        logger.info("=" * 80)

        try:
            # Simulate incoming telemetry
            telemetry = {
                "flow_id": "192.168.1.5:192.168.1.100:50000:443",
                "flow_duration": 15.0,
                "fwd_packets": 120,
                "bwd_packets": 110,
                "fwd_bytes": 60000,
                "bwd_bytes": 55000,
                "dst_ports": [443],
                "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
                "inter_arrival_times": [0.05, 0.05, 0.05, 0.05],
            }

            # Step 1: Extract features
            features = self.feature_handler.extract_features(telemetry)
            logger.info(f"Step 1 - Features extracted: {features}")

            # Step 2: ML Inference
            ml_result = self.ml_engine.infer(np.array(features))
            logger.info(f"Step 2 - ML Inference: anomaly={ml_result['tier1_is_anomaly']}, "
                       f"malicious_prob={ml_result['final_malicious_probability']}")

            # Step 3: Trust Score
            trust_result = self.trust_calculator.calculate_trust(
                flow_id=telemetry["flow_id"],
                ml_malicious_probability=ml_result["final_malicious_probability"],
                ml_anomaly_score=ml_result["tier1_anomaly_score"],
                is_clean_traffic=False,
            )
            logger.info(f"Step 3 - Trust Score: {trust_result['trust_score']}, "
                       f"policy={trust_result['policy']}")

            # Validate complete pipeline
            assert trust_result["policy"] in [
                "ALLOW",
                "VERIFY",
            ], f"Unexpected policy: {trust_result['policy']}"

            logger.info("✓ End-to-end pipeline completed successfully")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ End-to-end pipeline failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    # ========================================================================
    # TEST 3: ATTACK SIMULATION TESTS
    # ========================================================================

    def test_syn_flood_detection(self) -> bool:
        """Simulate SYN flood attack and verify detection."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3.1: SYN Flood Attack Detection")
        logger.info("=" * 80)

        try:
            # SYN flood telemetry: high packet rate, low responses, single port
            telemetry = {
                "flow_duration": 5.0,
                "fwd_packets": 50000,  # VERY HIGH
                "bwd_packets": 10,  # Few responses
                "fwd_bytes": 2000000,  # Huge
                "bwd_bytes": 500,
                "dst_ports": [443],  # Single target
                "tcp_flags": ["SYN"] * 1000,  # Mostly SYN flags
                "inter_arrival_times": [0.0001] * 100,  # Very fast
            }

            features = self.feature_handler.extract_features(telemetry)
            ml_result = self.ml_engine.infer(np.array(features))

            logger.info(f"Feature vector: {features}")
            logger.info(f"Tier 1 Anomaly: {ml_result['tier1_is_anomaly']}")
            logger.info(f"Malicious Probability: {ml_result['final_malicious_probability']}")

            # Should detect anomaly
            assert (
                ml_result["tier1_is_anomaly"]
            ), "SYN flood not detected as anomaly!"

            logger.info("✓ SYN flood correctly detected")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ SYN flood detection failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_port_scan_detection(self) -> bool:
        """Simulate port scan attack and verify detection."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3.2: Port Scanning Attack Detection")
        logger.info("=" * 80)

        try:
            # Port scan telemetry: many different ports, SYN+RST pattern
            telemetry = {
                "flow_duration": 30.0,
                "fwd_packets": 500,
                "bwd_packets": 100,
                "fwd_bytes": 20000,
                "bwd_bytes": 5000,
                "dst_ports": list(range(1, 256)),  # Scanning 255 ports!
                "tcp_flags": ["SYN", "RST"] * 250,  # SYN+RST pattern
                "inter_arrival_times": [0.05] * 500,
            }

            features = self.feature_handler.extract_features(telemetry)
            ml_result = self.ml_engine.infer(np.array(features))

            logger.info(f"Target ports scanned: {len(telemetry['dst_ports'])}")
            logger.info(f"Tier 1 Anomaly: {ml_result['tier1_is_anomaly']}")
            logger.info(f"Malicious Probability: {ml_result['final_malicious_probability']}")

            # Should detect many unique ports as suspicious
            assert features[4] > 0.5, "Port scan not flagged by unique_dst_ports feature!"

            logger.info("✓ Port scan correctly detected")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ Port scan detection failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def test_data_exfiltration_detection(self) -> bool:
        """Simulate data exfiltration and verify detection."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3.3: Data Exfiltration Detection")
        logger.info("=" * 80)

        try:
            # Data exfil: huge upload, small download (asymmetric)
            telemetry = {
                "flow_duration": 60.0,
                "fwd_packets": 2000,
                "bwd_packets": 200,
                "fwd_bytes": 50000000,  # 50MB upload!!!
                "bwd_bytes": 100000,  # Small download
                "dst_ports": [443],
                "tcp_flags": ["ACK"] * 2000,
                "inter_arrival_times": [0.01] * 100,
            }

            features = self.feature_handler.extract_features(telemetry)
            ml_result = self.ml_engine.infer(np.array(features))

            logger.info(f"Upload volume: {telemetry['fwd_bytes'] / 1e6:.1f}MB")
            logger.info(f"Byte Entropy (feature 4): {features[3]}")
            logger.info(f"Tier 1 Anomaly: {ml_result['tier1_is_anomaly']}")

            # High byte entropy should flag this
            assert features[3] > 0.3, "Data exfil not detected by byte_entropy!"

            logger.info("✓ Data exfiltration correctly detected")
            self.test_results["passed"] += 1
            return True

        except Exception as e:
            logger.error(f"✗ Data exfil detection failed: {e}")
            self.test_results["failed"] += 1
            self.test_results["errors"].append(str(e))
            return False

    def run_all_tests(self):
        """Run all tests and generate report."""
        logger.info(
            "\n"
            + "=" * 80
        )
        logger.info("🧪 STARTING COMPREHENSIVE TEST SUITE")
        logger.info("=" * 80)

        # Unit Tests
        logger.info("\n📋 UNIT TESTS")
        self.test_feature_extraction()
        self.test_ml_inference_normal_traffic()
        self.test_ml_inference_attack_traffic()
        self.test_trust_calculation_normal()
        self.test_trust_calculation_attack()

        # Integration Tests
        logger.info("\n🔗 INTEGRATION TESTS")
        self.test_end_to_end_pipeline()

        # Attack Simulation Tests
        logger.info("\n🚨 ATTACK SIMULATION TESTS")
        self.test_syn_flood_detection()
        self.test_port_scan_detection()
        self.test_data_exfiltration_detection()

        # Print Report
        self.print_report()

    def print_report(self):
        """Print test results report."""
        total = self.test_results["passed"] + self.test_results["failed"]
        pass_rate = (
            (self.test_results["passed"] / total * 100) if total > 0 else 0
        )

        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST RESULTS REPORT")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total}")
        logger.info(f"✓ Passed: {self.test_results['passed']}")
        logger.info(f"✗ Failed: {self.test_results['failed']}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")

        if self.test_results["errors"]:
            logger.info("\n⚠️  ERRORS:")
            for err in self.test_results["errors"]:
                logger.info(f"  - {err}")

        if pass_rate == 100:
            logger.info("\n🎉 ALL TESTS PASSED! System is ready.")
        else:
            logger.info(
                f"\n⚠️  {self.test_results['failed']} tests failed. See errors above."
            )

        logger.info("=" * 80)


def main():
    """Run test suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument(
        "--test",
        choices=["unit", "integration", "attacks", "all"],
        default="all",
        help="Test category to run",
    )

    args = parser.parse_args()

    suite = TestSuite()

    if args.test == "all":
        suite.run_all_tests()
    else:
        logger.info(f"Running {args.test} tests...")

        if args.test in ["unit", "all"]:
            suite.test_feature_extraction()
            suite.test_ml_inference_normal_traffic()
            suite.test_ml_inference_attack_traffic()
            suite.test_trust_calculation_normal()
            suite.test_trust_calculation_attack()

        if args.test in ["integration", "all"]:
            suite.test_end_to_end_pipeline()

        if args.test in ["attacks", "all"]:
            suite.test_syn_flood_detection()
            suite.test_port_scan_detection()
            suite.test_data_exfiltration_detection()

        suite.print_report()


if __name__ == "__main__":
    main()
