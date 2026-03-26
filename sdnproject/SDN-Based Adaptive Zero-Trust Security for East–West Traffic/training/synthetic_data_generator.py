"""
SYNTHETIC TRAINING DATA GENERATOR
Generate realistic network flows for ML model training.

Usage:
    python training/synthetic_data_generator.py --output training_data.csv

Generates:
  - Normal flows: HTTP, HTTPS, DNS, SSH traffic patterns
  - Attack flows: SYN floods, port scans, UDP floods, data exfiltration
"""

import csv
import random
import math
import logging
from typing import List, Dict, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic network flow dataset for ML training."""

    # Normal traffic patterns (these are realistic)
    NORMAL_PATTERNS = {
        "https": {
            "fwd_packets": (50, 500),
            "bwd_packets": (40, 400),
            "fwd_bytes": (10000, 200000),
            "bwd_bytes": (5000, 150000),
            "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
            "dst_port": 443,
            "duration": (0.5, 30),
        },
        "http": {
            "fwd_packets": (30, 100),
            "bwd_packets": (25, 80),
            "fwd_bytes": (2000, 50000),
            "bwd_bytes": (5000, 100000),
            "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
            "dst_port": 80,
            "duration": (0.1, 5),
        },
        "ssh": {
            "fwd_packets": (150, 1000),
            "bwd_packets": (140, 950),
            "fwd_bytes": (50000, 500000),
            "bwd_bytes": (40000, 400000),
            "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
            "dst_port": 22,
            "duration": (60, 600),
        },
        "dns": {
            "fwd_packets": (1, 3),
            "bwd_packets": (1, 3),
            "fwd_bytes": (50, 200),
            "bwd_bytes": (100, 500),
            "tcp_flags": ["SYN", "ACK", "FIN"],
            "dst_port": 53,
            "duration": (0.01, 0.1),
        },
    }

    # Attack patterns
    ATTACK_PATTERNS = {
        "syn_flood": {
            "name": "SYN Flood DoS",
            "fwd_packets": (10000, 50000),  # Very high
            "bwd_packets": (0, 100),  # Few responses
            "fwd_bytes": (500000, 2000000),  # Huge bytes
            "bwd_bytes": (0, 1000),
            "tcp_flags": ["SYN", "SYN", "SYN"],  # Mostly SYN
            "unique_dst_ports": (1, 5),  # Single/few target ports
            "duration": (0.1, 10),
        },
        "port_scan": {
            "name": "Port Scanning",
            "fwd_packets": (100, 1000),
            "bwd_packets": (0, 50),
            "fwd_bytes": (3000, 30000),
            "bwd_bytes": (0, 500),
            "tcp_flags": ["SYN", "RST", "SYN", "RST"],
            "unique_dst_ports": (50, 500),  # MANY ports
            "duration": (1, 60),
        },
        "udp_flood": {
            "name": "UDP Flood DoS",
            "fwd_packets": (5000, 20000),
            "bwd_packets": (0, 100),
            "fwd_bytes": (1000000, 5000000),  # Huge
            "bwd_bytes": (0, 500),
            "tcp_flags": [],  # UDP has no TCP flags
            "unique_dst_ports": (1, 10),
            "duration": (0.5, 30),
        },
        "data_exfil": {
            "name": "Data Exfiltration",
            "fwd_packets": (100, 500),
            "bwd_packets": (50, 200),
            "fwd_bytes": (5000000, 50000000),  # HUGE upload
            "bwd_bytes": (1000, 10000),  # Small download
            "tcp_flags": ["SYN", "ACK", "ACK", "ACK"],
            "unique_dst_ports": (1, 3),
            "duration": (10, 300),
        },
        "slowloris": {
            "name": "Slowloris Attack",
            "fwd_packets": (50, 200),  # Slow packet rate
            "bwd_packets": (40, 180),
            "fwd_bytes": (1000, 5000),
            "bwd_bytes": (2000, 10000),
            "tcp_flags": ["SYN", "ACK", "ACK"],
            "unique_dst_ports": (1, 1),  # Single port
            "duration": (300, 1800),  # Very long
        },
    }

    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility."""
        random.seed(seed)
        self.feature_names = [
            "flow_duration",
            "fwd_packet_rate",
            "bwd_packet_rate",
            "byte_entropy",
            "unique_dst_ports",
            "tcp_flags_count",
            "inter_arrival_time_min",
            "inter_arrival_time_max",
            "label",
        ]

    def generate_normal_flow(self) -> Dict:
        """Generate a single normal (benign) flow."""
        traffic_type = random.choice(list(self.NORMAL_PATTERNS.keys()))
        pattern = self.NORMAL_PATTERNS[traffic_type]

        fwd_packets = random.randint(*pattern["fwd_packets"])
        bwd_packets = random.randint(*pattern["bwd_packets"])
        fwd_bytes = random.randint(*pattern["fwd_bytes"])
        bwd_bytes = random.randint(*pattern["bwd_bytes"])
        duration = random.uniform(*pattern["duration"])

        return {
            "flow_duration": duration,
            "fwd_packet_rate": fwd_packets / max(duration, 0.001),
            "bwd_packet_rate": bwd_packets / max(duration, 0.001),
            "byte_entropy": self._calculate_entropy(fwd_bytes, bwd_bytes),
            "unique_dst_ports": 1,  # Normal traffic to single port
            "tcp_flags_count": 0.1,  # Normal flag pattern
            "inter_arrival_time_min": 0.001,
            "inter_arrival_time_max": 0.1,
            "label": 0,  # Normal
        }

    def generate_attack_flow(self) -> Dict:
        """Generate a single malicious (attack) flow."""
        attack_type = random.choice(list(self.ATTACK_PATTERNS.keys()))
        pattern = self.ATTACK_PATTERNS[attack_type]

        fwd_packets = random.randint(*pattern["fwd_packets"])
        bwd_packets = random.randint(*pattern["bwd_packets"])
        fwd_bytes = random.randint(*pattern["fwd_bytes"])
        bwd_bytes = random.randint(*pattern["bwd_bytes"])
        duration = random.uniform(*pattern["duration"])
        unique_dst_ports = random.randint(*pattern["unique_dst_ports"])

        return {
            "flow_duration": duration,
            "fwd_packet_rate": fwd_packets / max(duration, 0.001),
            "bwd_packet_rate": bwd_packets / max(duration, 0.001),
            "byte_entropy": self._calculate_entropy(fwd_bytes, bwd_bytes),
            "unique_dst_ports": unique_dst_ports,
            "tcp_flags_count": 0.7,  # Anomalous flag pattern
            "inter_arrival_time_min": 0.0001,  # Very fast
            "inter_arrival_time_max": 50.0,  # Bursty
            "label": 1,  # Malicious
        }

    def _calculate_entropy(self, fwd_bytes: int, bwd_bytes: int) -> float:
        """Simulate byte entropy (0-1 where 1 = random/encrypted)."""
        total = fwd_bytes + bwd_bytes
        if total == 0:
            return 0.0
        # Asymmetry + volume as proxy for entropy
        ratio = min(fwd_bytes, bwd_bytes) / max(1, max(fwd_bytes, bwd_bytes))
        return 1.0 - ratio

    def generate_dataset(
        self, num_normal: int = 1000, num_attacks: int = 1000
    ) -> List[Dict]:
        """Generate complete balanced dataset."""
        logger.info(
            f"Generating {num_normal} normal flows + {num_attacks} attack flows..."
        )

        dataset = []

        # Generate normal flows
        for i in range(num_normal):
            dataset.append(self.generate_normal_flow())
            if (i + 1) % 250 == 0:
                logger.info(f"  Generated {i + 1}/{num_normal} normal flows")

        # Generate attack flows
        for i in range(num_attacks):
            dataset.append(self.generate_attack_flow())
            if (i + 1) % 250 == 0:
                logger.info(f"  Generated {i + 1}/{num_attacks} attack flows")

        # Shuffle to avoid bias
        random.shuffle(dataset)

        return dataset

    def save_to_csv(self, dataset: List[Dict], output_file: str) -> None:
        """Save dataset to CSV file."""
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.feature_names)
            writer.writeheader()
            writer.writerows(dataset)

        logger.info(f"✓ Saved {len(dataset)} flows to {output_file}")


def main():
    """Generate and save synthetic training dataset."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic training data")
    parser.add_argument(
        "-o",
        "--output",
        default="training_data/synthetic_training_data.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "-n",
        "--normal",
        type=int,
        default=1000,
        help="Number of normal flows to generate",
    )
    parser.add_argument(
        "-a",
        "--attacks",
        type=int,
        default=1000,
        help="Number of attack flows to generate",
    )

    args = parser.parse_args()

    generator = SyntheticDataGenerator(seed=42)
    dataset = generator.generate_dataset(
        num_normal=args.normal, num_attacks=args.attacks
    )
    generator.save_to_csv(dataset, args.output)

    logger.info("\n" + "=" * 80)
    logger.info("✓ SYNTHETIC DATASET READY")
    logger.info("=" * 80)
    logger.info(f"Output: {args.output}")
    logger.info(f"Total flows: {len(dataset)}")
    logger.info(f"Normal: {args.normal} | Attacks: {args.attacks}")
    logger.info("Labels: 0=Normal, 1=Malicious")
    logger.info("\nNext step: Train models")
    logger.info(f"  python training/train_models.py -d {args.output}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
