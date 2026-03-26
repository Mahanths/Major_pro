"""
PCAP to CSV Feature Extraction
Converts raw .pcap files into a clean training dataset.

Usage:
    python training/pcap_to_csv.py --input normal_traffic.pcap --output normal_features.csv --label 0
    python training/pcap_to_csv.py --input attack_traffic.pcap --output attack_features.csv --label 1
"""

import logging
import argparse
import json
from typing import List, Dict
import pandas as pd
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PCAPToCSVConverter:
    """Convert raw PCAP files into ML-ready CSV dataset."""

    def __init__(self):
        """Initialize converter."""
        self.flows = defaultdict(dict)
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

    def extract_features_from_pcap(
        self, pcap_file: str, label: int, output_csv: str
    ) -> pd.DataFrame:
        """
        Extract features from PCAP file using tshark.

        Args:
            pcap_file: Path to .pcap file
            label: 0 for normal, 1 for malicious
            output_csv: Output CSV filename

        Returns:
            DataFrame with extracted features
        """
        import subprocess
        import os

        if not os.path.exists(pcap_file):
            logger.error(f"PCAP file not found: {pcap_file}")
            return pd.DataFrame()

        logger.info(f"Extracting features from {pcap_file}...")

        # Use tshark to parse PCAP
        # Fields: src_ip, dst_ip, src_port, dst_port, protocol, flow_duration, pkt_count, bytes
        tshark_cmd = [
            "tshark",
            "-r",
            pcap_file,
            "-T",
            "fields",
            "-e",
            "ip.src",
            "-e",
            "ip.dst",
            "-e",
            "tcp.srcport",
            "-e",
            "tcp.dstport",
            "-e",
            "udp.srcport",
            "-e",
            "udp.dstport",
            "-e",
            "ip.proto",
            "-e",
            "frame.len",
            "-E",
            "separator=,",
        ]

        try:
            output = subprocess.check_output(tshark_cmd, universal_newlines=True)
            rows = output.strip().split("\n")
            logger.info(f"Parsed {len(rows)} packets from {pcap_file}")

            # Aggregate into flows and calculate features
            dataset = self._aggregate_flows_and_extract_features(rows, label)

            # Save to CSV
            dataset.to_csv(output_csv, index=False)
            logger.info(
                f"✓ Saved {len(dataset)} flow features to {output_csv}"
            )

            return dataset

        except subprocess.CalledProcessError as e:
            logger.error(f"tshark error: {e}")
            logger.warning("Ensure tshark is installed: sudo apt install tshark")
            return pd.DataFrame()

    def _aggregate_flows_and_extract_features(
        self, rows: List[str], label: int
    ) -> pd.DataFrame:
        """Aggregate packet-level data into flow-level features."""
        flows = defaultdict(lambda: {"packets": [], "bytes": 0})

        for row in rows:
            parts = row.split(",")
            if len(parts) < 8:
                continue

            try:
                src_ip = parts[0]
                dst_ip = parts[1]
                src_port = parts[2] or parts[4]  # TCP or UDP
                dst_port = parts[3] or parts[5]
                proto = parts[6]
                pkt_bytes = int(parts[7]) if parts[7] else 0

                # Create flow key (5-tuple)
                flow_key = (src_ip, dst_ip, src_port, dst_port, proto)

                flows[flow_key]["packets"].append(pkt_bytes)
                flows[flow_key]["bytes"] += pkt_bytes

            except (IndexError, ValueError):
                continue

        # Convert to feature vectors
        feature_rows = []
        for flow_key, flow_data in flows.items():
            features = self._compute_flow_features(flow_data, label)
            feature_rows.append(features)

        return pd.DataFrame(feature_rows, columns=self.feature_names)

    def _compute_flow_features(self, flow_data: Dict, label: int) -> Dict:
        """Compute 8 ML features from aggregated flow data."""
        packets = flow_data["packets"]
        total_bytes = flow_data["bytes"]

        # Placeholder feature computation
        # In production, you'd compute these from actual packet timing/flags
        return {
            "flow_duration": 1.0,  # seconds
            "fwd_packet_rate": len(packets),  # packets/sec
            "bwd_packet_rate": 0.5,  # placeholder
            "byte_entropy": min(total_bytes / 1000.0, 1.0),
            "unique_dst_ports": 1,  # placeholder
            "tcp_flags_count": 0.5,
            "inter_arrival_time_min": 0.001,
            "inter_arrival_time_max": 0.1,
            "label": label,
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert PCAP files to ML training CSV"
    )
    parser.add_argument("-i", "--input", required=True, help="Input PCAP file")
    parser.add_argument("-o", "--output", required=True, help="Output CSV file")
    parser.add_argument(
        "-l", "--label", type=int, required=True, help="0=normal, 1=malicious"
    )

    args = parser.parse_args()

    converter = PCAPToCSVConverter()
    converter.extract_features_from_pcap(args.input, args.label, args.output)


if __name__ == "__main__":
    main()
