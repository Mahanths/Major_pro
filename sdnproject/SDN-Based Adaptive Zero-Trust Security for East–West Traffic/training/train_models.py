"""
Train ML Models - Isolation Forest & XGBoost
Trains two-tier ML pipeline from CSV dataset.

Usage:
    python training/train_models.py --dataset training_dataset_final.csv
"""

import logging
import argparse
import os
from typing import Tuple
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train Isolation Forest and XGBoost models from dataset."""

    def __init__(self, model_dir: str = "brain/models"):
        """Initialize trainer."""
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.isolation_forest = None
        self.xgboost_model = None
        logger.info(f"Model directory: {model_dir}")

    def train_from_csv(self, csv_file: str) -> None:
        """Train both models from CSV dataset."""
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return

        logger.info(f"Loading dataset from {csv_file}...")
        df = pd.read_csv(csv_file)
        logger.info(f"Loaded {len(df)} samples")

        # Separate features and labels
        X = df.drop("label", axis=1).values.astype(np.float32)
        y = df["label"].values.astype(int)

        logger.info(f"Feature shape: {X.shape}")
        logger.info(f"Label distribution: {np.bincount(y)}")

        # === Train Tier 1: Isolation Forest (Unsupervised) ===
        logger.info("\n" + "=" * 80)
        logger.info("TIER 1: Training Isolation Forest (Unsupervised Anomaly Detection)")
        logger.info("=" * 80)

        # Train ONLY on normal traffic (label=0)
        X_normal = X[y == 0]
        logger.info(f"Training Isolation Forest on {len(X_normal)} normal samples...")

        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect ~10% anomalies in wild
            max_samples="auto",
            random_state=42,
            n_estimators=100,
        )
        self.isolation_forest.fit(X_normal)

        # Test on full dataset
        iso_predictions = self.isolation_forest.predict(X)
        iso_anomaly_count = np.sum(iso_predictions == -1)
        logger.info(f"✓ Isolation Forest trained and detected {iso_anomaly_count} anomalies in test set")

        # Save Tier 1 model
        iso_path = os.path.join(self.model_dir, "isolation_forest_model.pkl")
        joblib.dump(self.isolation_forest, iso_path)
        logger.info(f"✓ Saved Isolation Forest to {iso_path}")

        # === Train Tier 2: XGBoost (Supervised) ===
        logger.info("\n" + "=" * 80)
        logger.info("TIER 2: Training XGBoost (Supervised Classification)")
        logger.info("=" * 80)

        # Train on full dataset (both normal and malicious)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        logger.info(
            f"Training set: {len(X_train)} samples | Test set: {len(X_test)} samples"
        )

        self.xgboost_model = xgb.XGBClassifier(
            objective="binary:logistic",
            max_depth=5,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42,
            verbose=1,
        )

        logger.info("Training XGBoost classifier...")
        self.xgboost_model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

        # Evaluate
        y_pred = self.xgboost_model.predict(X_test)
        y_pred_proba = self.xgboost_model.predict_proba(X_test)

        logger.info("\nXGBoost Classification Report:")
        logger.info(
            f"\n{classification_report(y_test, y_pred, target_names=['Normal', 'Malicious'])}"
        )

        logger.info("\nConfusion Matrix:")
        logger.info(f"\n{confusion_matrix(y_test, y_pred)}")

        # Save Tier 2 model
        xgb_path = os.path.join(self.model_dir, "xgboost_model.pkl")
        joblib.dump(self.xgboost_model, xgb_path)
        logger.info(f"✓ Saved XGBoost model to {xgb_path}")

        # === Summary ===
        logger.info("\n" + "=" * 80)
        logger.info("✓ MODEL TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Isolation Forest: {iso_path}")
        logger.info(f"XGBoost: {xgb_path}")
        logger.info("\nNext step: Start the FastAPI Brain")
        logger.info("  cd brain/ && uvicorn app:app --host 0.0.0.0 --port 8000")
        logger.info("=" * 80)

    def load_models(self) -> Tuple:
        """Load pre-trained models."""
        iso_path = os.path.join(self.model_dir, "isolation_forest_model.pkl")
        xgb_path = os.path.join(self.model_dir, "xgboost_model.pkl")

        iso_model = None
        xgb_model = None

        if os.path.exists(iso_path):
            iso_model = joblib.load(iso_path)
            logger.info(f"Loaded Isolation Forest from {iso_path}")

        if os.path.exists(xgb_path):
            xgb_model = joblib.load(xgb_path)
            logger.info(f"Loaded XGBoost from {xgb_path}")

        return iso_model, xgb_model


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Train ML models from CSV dataset")
    parser.add_argument(
        "-d",
        "--dataset",
        required=True,
        help="Path to training dataset CSV file",
    )
    parser.add_argument(
        "-m",
        "--model-dir",
        default="brain/models",
        help="Output directory for trained models",
    )

    args = parser.parse_args()

    trainer = ModelTrainer(model_dir=args.model_dir)
    trainer.train_from_csv(args.dataset)


if __name__ == "__main__":
    main()
