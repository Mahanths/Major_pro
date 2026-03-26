#!/usr/bin/env python3
"""
Improved Model Trainer with Multi-Dataset Support
Combines NSL-KDD with CICIDS for better performance
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import xgboost as xgb
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedModelTrainer:
    """Train models on combined CICIDS + NSL-KDD datasets"""
    
    def __init__(self, model_dir='brain/models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.isolation_forest = None
        self.xgboost_model = None
        logger.info(f"Model directory: {model_dir}")
    
    def load_multiple_datasets(self, dataset_paths):
        """Load and combine multiple CSV datasets"""
        dfs = []
        total_rows = 0
        
        for path in dataset_paths:
            if os.path.exists(path):
                logger.info(f"Loading {path}...")
                df = pd.read_csv(path)
                dfs.append(df)
                total_rows += len(df)
                logger.info(f"  ✓ Loaded {len(df)} rows")
            else:
                logger.warning(f"  ⚠️ File not found: {path}")
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            logger.info(f"✓ Combined dataset: {len(combined_df)} total rows from {len(dfs)} files")
            return combined_df
        else:
            logger.error("No datasets loaded!")
            return None
    
    def train_from_datasets(self, dataset_paths, model_name='cicids_combined'):
        """Train models from multiple datasets"""
        
        # Load data
        df = self.load_multiple_datasets(dataset_paths)
        if df is None:
            return False
        
        # Prepare data
        X = df.drop('label', axis=1).values.astype(np.float32)
        y = df['label'].values
        
        logger.info(f"\n📊 Dataset Statistics:")
        logger.info(f"  - Total samples: {len(X)}")
        logger.info(f"  - Normal (0): {np.sum(y == 0)} ({np.sum(y == 0) / len(y) * 100:.1f}%)")
        logger.info(f"  - Attack (1): {np.sum(y == 1)} ({np.sum(y == 1) / len(y) * 100:.1f}%)")
        logger.info(f"  - Features: {len(X[0])}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"\n📈 Train/Test Split:")
        logger.info(f"  - Training: {len(X_train)} samples")
        logger.info(f"  - Testing: {len(X_test)} samples")
        
        # Train Isolation Forest (only on normal data)
        logger.info("\n🌲 Training Isolation Forest (Anomaly Detection)...")
        X_normal = X_train[y_train == 0]
        logger.info(f"  - Using {len(X_normal)} normal samples for training")
        
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        self.isolation_forest.fit(X_normal)
        logger.info("  ✓ Isolation Forest trained")
        
        # Train XGBoost (on all data)
        logger.info("\n🚀 Training XGBoost (Supervised Classification)...")
        self.xgboost_model = xgb.XGBClassifier(
            max_depth=7,
            learning_rate=0.1,
            n_estimators=200,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric='logloss'
        )
        self.xgboost_model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        logger.info("  ✓ XGBoost trained")
        
        # Evaluate
        logger.info("\n📊 Evaluation Results:")
        self._evaluate(X_test, y_test)
        
        # Save models
        logger.info("\n💾 Saving models...")
        self._save_models(model_name)
        
        return True
    
    def _evaluate(self, X_test, y_test):
        """Evaluate model performance"""
        
        # Isolation Forest
        if_pred = self.isolation_forest.predict(X_test)
        if_pred_binary = (if_pred == -1).astype(int)
        
        logger.info("\n  🌲 Isolation Forest (Anomaly Detection):")
        logger.info(f"    - Anomalies detected: {np.sum(if_pred_binary)} / {len(y_test)}")
        logger.info(f"    - Accuracy: {accuracy_score(y_test, if_pred_binary) * 100:.2f}%")
        
        # XGBoost
        xgb_pred = self.xgboost_model.predict(X_test)
        xgb_accuracy = accuracy_score(y_test, xgb_pred)
        xgb_precision, xgb_recall, xgb_f1, _ = precision_recall_fscore_support(
            y_test, xgb_pred, average='binary'
        )
        
        logger.info(f"\n  🚀 XGBoost (Supervised Classification):")
        logger.info(f"    - Accuracy: {xgb_accuracy * 100:.2f}%")
        logger.info(f"    - Precision: {xgb_precision * 100:.2f}%")
        logger.info(f"    - Recall: {xgb_recall * 100:.2f}%")
        logger.info(f"    - F1-Score: {xgb_f1 * 100:.2f}%")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, xgb_pred)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        logger.info(f"\n  📋 Confusion Matrix:")
        logger.info(f"    - True Positives: {tp} (caught attacks)")
        logger.info(f"    - True Negatives: {tn} (allowed normal)")
        logger.info(f"    - False Positives: {fp} (false alarms: {fpr*100:.2f}%)")
        logger.info(f"    - False Negatives: {fn} (missed: {fnr*100:.2f}%)")
        
        logger.info(f"\n✅ Model Performance Summary:")
        logger.info(f"   Overall: {xgb_accuracy*100:.1f}% accurate")
        logger.info(f"   False Alarm Rate: {fpr*100:.2f}%")
        logger.info(f"   Miss Rate: {fnr*100:.2f}%")
    
    def _save_models(self, model_name):
        """Save trained models"""
        
        if_path = os.path.join(self.model_dir, f'isolation_forest_{model_name}.pkl')
        xgb_path = os.path.join(self.model_dir, f'xgboost_{model_name}.pkl')
        
        joblib.dump(self.isolation_forest, if_path)
        self.xgboost_model.save_model(xgb_path)
        
        logger.info(f"  ✓ Isolation Forest: {if_path}")
        logger.info(f"  ✓ XGBoost: {xgb_path}")
        
        # Also save as default models for production
        joblib.dump(self.isolation_forest, 
                   os.path.join(self.model_dir, 'isolation_forest_model.pkl'))
        self.xgboost_model.save_model(
                   os.path.join(self.model_dir, 'xgboost_model.pkl'))
        logger.info(f"  ✓ Also saved as default models (production)")

def main():
    """Main execution"""
    import sys
    
    logger.info("🚀 Training models with CICIDS datasets\n")
    
    # Check what datasets we have
    data_files = [
        'data/nslkdd_training_8features.csv',
        'data/cicids2018_8features.csv',
        'data/cicids2019_8features.csv',
        'data/cicids2023_8features.csv'
    ]
    
    # Find existing files
    existing_files = [f for f in data_files if os.path.exists(f)]
    
    if not existing_files:
        logger.error("❌ No training datasets found!")
        logger.info("Available datasets:")
        logger.info("  - data/nslkdd_training_8features.csv")
        logger.info("  - data/cicids2018_8features.csv (convert using cicids_converter.py)")
        logger.info("  - data/cicids2019_8features.csv (convert using cicids_converter.py)")
        logger.info("  - data/cicids2023_8features.csv (convert using cicids_converter.py)")
        sys.exit(1)
    
    logger.info(f"📂 Found {len(existing_files)} dataset(s):")
    for f in existing_files:
        logger.info(f"  ✓ {f}")
    
    # Train
    trainer = ImprovedModelTrainer()
    success = trainer.train_from_datasets(existing_files, model_name='cicids_combined')
    
    if success:
        logger.info("\n✅ Training complete!")
        logger.info("Models saved to: brain/models/")
    else:
        logger.error("\n❌ Training failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
