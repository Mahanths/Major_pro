"""
Feature Handler Module
Converts raw network telemetry (JSON) into 8-feature ML vector for inference.

Features extracted:
1. flow_duration - Total active time (seconds)
2. fwd_packet_rate - Forward packets per second
3. bwd_packet_rate - Backward packets per second
4. byte_entropy - Payload randomness (0-8 scale)
5. unique_dst_ports - Count of unique destination ports
6. tcp_flags_count - Ratio of SYN/ACK/FIN/RST flags
7. inter_arrival_time_min - Minimum time between packets (ms)
8. inter_arrival_time_max - Maximum time between packets (ms)
"""

import logging
from typing import Dict, List
import numpy as np

logger = logging.getLogger(__name__)


class FeatureHandler:
    """Extracts 8-feature ML vector from network telemetry JSON."""

    def __init__(self):
        self.feature_names = [
            "flow_duration",
            "fwd_packet_rate",
            "bwd_packet_rate",
            "byte_entropy",
            "unique_dst_ports",
            "tcp_flags_count",
            "inter_arrival_time_min",
            "inter_arrival_time_max",
        ]

    def extract_features(self, telemetry: Dict) -> List[float]:
        """
        Extract 8 features from raw telemetry JSON.

        Args:
            telemetry: Dict with keys:
                - flow_duration: seconds (float)
                - fwd_packets: count (int)
                - bwd_packets: count (int)
                - fwd_bytes: count (int)
                - bwd_bytes: count (int)
                - src_ip: string
                - dst_ip: string
                - dst_ports: list of ints [80, 443, 22, ...]
                - tcp_flags: list of strings ['SYN', 'ACK', 'FIN', ...]
                - inter_arrival_times: list of floats [0.1, 0.05, 0.2, ...] in ms

        Returns:
            List of 8 floats, one per feature, normalized [0-1] range.
        """
        try:
            # Feature 1: flow_duration (seconds, clip to [0, 300])
            flow_duration = min(float(telemetry.get("flow_duration", 0)), 300.0)
            f1 = flow_duration / 300.0  # Normalize [0-1]

            # Features 2 & 3: Packet rates (packets/sec)
            fwd_packets = float(telemetry.get("fwd_packets", 1))
            bwd_packets = float(telemetry.get("bwd_packets", 1))
            fwd_pps = fwd_packets / max(flow_duration, 0.001)
            bwd_pps = bwd_packets / max(flow_duration, 0.001)
            f2 = min(fwd_pps / 1000.0, 1.0)  # Cap at 1000 pps
            f3 = min(bwd_pps / 1000.0, 1.0)

            # Feature 4: Byte entropy (0-8, higher = more random/encrypted)
            f4 = self._calculate_byte_entropy(
                telemetry.get("fwd_bytes", 0), telemetry.get("bwd_bytes", 0)
            )

            # Feature 5: Unique destination ports (0-65535, normalize to [0-1])
            dst_ports = telemetry.get("dst_ports", [])
            unique_dst_ports = len(set(dst_ports)) if dst_ports else 0
            f5 = min(unique_dst_ports / 100.0, 1.0)  # Suspicious if > 100 ports

            # Feature 6: TCP flags ratio (SYN/ACK/FIN/RST)
            f6 = self._calculate_tcp_flags_ratio(telemetry.get("tcp_flags", []))

            # Features 7 & 8: Inter-arrival times (min/max in ms)
            inter_arrivals = telemetry.get("inter_arrival_times", [0.001])
            if not inter_arrivals or len(inter_arrivals) == 0:
                inter_arrivals = [0.001]
            f7 = min(min(inter_arrivals) / 1000.0, 1.0)  # Min IAT, cap at 1s
            f8 = min(max(inter_arrivals) / 1000.0, 1.0)  # Max IAT, cap at 1s

            features = [f1, f2, f3, f4, f5, f6, f7, f8]

            logger.debug(
                f"Extracted features: {dict(zip(self.feature_names, features))}"
            )
            return features

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            # Return all-zero features if extraction fails
            return [0.0] * 8

    def _calculate_byte_entropy(self, fwd_bytes: int, bwd_bytes: int) -> float:
        """
        Estimate byte entropy from traffic volume asymmetry.
        Higher entropy = more random/encrypted payload (suspicious indicator).
        Returns value in [0, 1] range where 1 = perfect entropy.
        """
        total_bytes = fwd_bytes + bwd_bytes
        if total_bytes == 0:
            return 0.0

        # Asymmetry in fwd vs bwd suggests encryption or obfuscation
        ratio = min(fwd_bytes, bwd_bytes) / max(1, max(fwd_bytes, bwd_bytes))
        asymmetry = 1.0 - ratio

        # High byte volume also correlates with data exfiltration
        volume_score = min(total_bytes / 1_000_000, 1.0)  # Cap at 1MB

        # Combine asymmetry and volume
        entropy = (asymmetry * 0.6) + (volume_score * 0.4)
        return min(entropy, 1.0)

    def _calculate_tcp_flags_ratio(self, tcp_flags: List[str]) -> float:
        """
        Measure anomalous TCP flag patterns.
        Normal: mostly SYN, ACK, FIN. Anomalous: many RST, duplicate SYN.
        Returns [0, 1] where high=anomalous.
        """
        if not tcp_flags:
            return 0.0

        flag_counts = {
            "SYN": tcp_flags.count("SYN"),
            "ACK": tcp_flags.count("ACK"),
            "FIN": tcp_flags.count("FIN"),
            "RST": tcp_flags.count("RST"),
        }

        total_flags = len(tcp_flags)
        normal_flags = flag_counts["SYN"] + flag_counts["ACK"] + flag_counts["FIN"]
        anomalous_flags = flag_counts["RST"]

        # High RST ratio or low normal flag ratio = anomalous
        anomaly_score = anomalous_flags / max(1, total_flags)
        return min(anomaly_score, 1.0)

    def validate_telemetry(self, telemetry: Dict) -> bool:
        """Check if telemetry JSON has required fields."""
        required_fields = [
            "flow_duration",
            "fwd_packets",
            "bwd_packets",
            "fwd_bytes",
            "bwd_bytes",
        ]
        return all(field in telemetry for field in required_fields)
