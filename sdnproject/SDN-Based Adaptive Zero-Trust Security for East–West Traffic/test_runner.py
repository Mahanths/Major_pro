#!/usr/bin/env python3
"""
Two-Laptop Model Accuracy Testing Script
Tests ML models on Laptop A from Laptop B
Comprehensive accuracy, latency, and throughput metrics
"""

import requests
import pandas as pd
import numpy as np
import time
import json
import sys
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# CONFIGURATION - MODIFY THESE!
BRAIN_IP = "192.168.1.100"  # ← CHANGE THIS to your Laptop A IP!
BRAIN_PORT = 8000
API_BASE_URL = f"http://{BRAIN_IP}:{BRAIN_PORT}"

TEST_DATASET = "data/nslkdd_training_8features.csv"  # Or CICIDS
BATCH_SIZE = 100  # Send 100 flows per request
TEST_LIMIT = 5000  # Test on 5000 flows (change for more/less)

class RemoteModelTester:
    """Test remote ML models via API"""
    
    def __init__(self, api_url):
        self.api_url = api_url
        self.results = []
        self.true_labels = []
        self.pred_labels = []
        self.timings = []
        
    def health_check(self):
        """Verify API is online"""
        try:
            print("   Connecting to API...")
            resp = requests.get(f"{self.api_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                print("   ✅ Brain API is ONLINE")
                print(f"      Status: {data.get('status')}")
                print(f"      Models: {data.get('models')}")
                return True
            else:
                print(f"   ❌ Brain API returned {resp.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to {self.api_url}")
            print(f"      Make sure Brain API is running on Laptop A")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def load_test_data(self, csv_file, limit=5000):
        """Load test dataset"""
        print(f"   Loading from: {csv_file}")
        try:
            df = pd.read_csv(csv_file)
            
            print(f"   Dataset shape: {df.shape}")
            
            # Check if CSV has enough columns (8 features + 1 label)
            if df.shape[1] < 2:
                print(f"   ❌ CSV should have at least 9 columns (8 features + label)")
                return None, None
            
            # Take only first 'limit' rows
            df = df.head(limit)
            
            # Separate features and labels (assume last column is label)
            X = df.iloc[:, :-1].values  # All columns except last
            y = df.iloc[:, -1].values   # Last column is label
            
            # Count attack types
            unique_labels = np.unique(y)
            label_counts = {}
            for label in unique_labels:
                count = np.sum(y == label)
                label_counts[label] = count
            
            print(f"   ✓ Loaded {len(X)} samples with {X.shape[1]} features")
            print(f"   Label distribution: {label_counts}")
            
            # Verify numerical features
            try:
                X = X.astype(float)
                y = y.astype(int)  # Convert labels to integers
            except:
                print(f"   ❌ Features must be numerical")
                return None, None
            
            return X, y
        except FileNotFoundError:
            print(f"   ❌ File not found: {csv_file}")
            return None, None
        except Exception as e:
            print(f"   ❌ Error loading data: {e}")
            return None, None
    
    def test_single_flow(self, features):
        """Send single flow to API and get prediction"""
        payload = {
            "features": features.tolist(),
            "source_ip": "192.168.1.100",
            "dest_ip": "192.168.1.200",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            start = time.time()
            resp = requests.post(
                f"{self.api_url}/infer",
                json=payload,
                timeout=10
            )
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                result = resp.json()
                # Get malicious prediction
                pred = 1 if result.get('is_malicious', False) else 0
                confidence = result.get('malicious_probability', 0)
                return pred, confidence, elapsed
            else:
                return None, None, None
        except Exception as e:
            return None, None, None
    
    def run_batch_test(self, X, y, batch_size=100):
        """Test all samples"""
        print(f"   Testing {len(X)} samples in batches of {batch_size}...")
        
        total = len(X)
        
        for i in range(0, total, batch_size):
            batch_X = X[i:i+batch_size]
            batch_y = y[i:i+batch_size]
            
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            for j, (features, true_label) in enumerate(zip(batch_X, batch_y)):
                pred, conf, elapsed = self.test_single_flow(features)
                
                if pred is not None:
                    self.pred_labels.append(pred)
                    self.true_labels.append(true_label)
                    self.timings.append(elapsed)
            
            # Progress update every batch
            if len(self.true_labels) > 0:
                accuracy_so_far = accuracy_score(self.true_labels, self.pred_labels)
                progress = len(self.true_labels)
                print(f"   Batch {batch_num}/{total_batches}: {progress} samples processed | Accuracy: {accuracy_so_far:.2%}")
    
    def calculate_metrics(self):
        """Calculate accuracy metrics"""
        if len(self.true_labels) == 0:
            print("   ❌ No results to analyze")
            return None
        
        # Calculate metrics
        accuracy = accuracy_score(self.true_labels, self.pred_labels)
        precision = precision_score(self.true_labels, self.pred_labels, average='binary', zero_division=0)
        recall = recall_score(self.true_labels, self.pred_labels, average='binary', zero_division=0)
        f1 = f1_score(self.true_labels, self.pred_labels, average='binary', zero_division=0)
        cm = confusion_matrix(self.true_labels, self.pred_labels)
        
        # Calculate rates from confusion matrix
        if cm.size == 4:
            tn, fp, fn, tp = cm.ravel()
        else:
            # Handle edge cases
            tn, fp, fn, tp = 0, 0, 0, len(self.true_labels)
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        # Latency statistics
        avg_latency = np.mean(self.timings) * 1000  # Convert to ms
        max_latency = np.max(self.timings) * 1000
        min_latency = np.min(self.timings) * 1000
        
        # Calculate throughput
        total_time = np.sum(self.timings)
        throughput = len(self.timings) / total_time if total_time > 0 else 0
        
        # Print results
        print("\n╔════════════════════════════════════════════════════════╗")
        print("║           MODEL ACCURACY TEST RESULTS                  ║")
        print("╚════════════════════════════════════════════════════════╝\n")
        
        print(f"📊 OVERALL METRICS:")
        accuracy_status = "✅" if accuracy > 0.95 else "⚠️" if accuracy > 0.85 else "❌"
        print(f"   Accuracy:   {accuracy:.4f} ({accuracy*100:.2f}%) {accuracy_status}")
        print(f"   Precision:  {precision:.4f} ({precision*100:.2f}%)")
        print(f"   Recall:     {recall:.4f} ({recall*100:.2f}%)")
        print(f"   F1-Score:   {f1:.4f}")
        
        print(f"\n🎯 CONFUSION MATRIX:")
        print(f"   TP (Caught Attacks):     {tp:,}")
        print(f"   TN (Correct Normal):     {tn:,}")
        print(f"   FP (False Alarms):       {fp:,}")
        print(f"   FN (Missed Attacks):     {fn:,}")
        
        print(f"\n⚠️  ERROR RATES:")
        print(f"   False Positive Rate:     {fpr:.4f} ({fpr*100:.2f}%)")
        print(f"   False Negative Rate:     {fnr:.4f} ({fnr*100:.2f}%)")
        
        print(f"\n⏱️  LATENCY METRICS:")
        print(f"   Average Latency:         {avg_latency:.2f} ms")
        print(f"   Min Latency:             {min_latency:.2f} ms")
        print(f"   Max Latency:             {max_latency:.2f} ms")
        print(f"   Throughput:              {throughput:.1f} req/sec")
        print(f"   Total Time:              {total_time:.1f} sec")
        
        print(f"\n📈 DATASET METRICS:")
        print(f"   Total Samples:           {len(self.true_labels):,}")
        print(f"   Samples/sec:             {len(self.true_labels)/total_time:.1f}")
        
        print(f"\n{''.join(['═']*58)}\n")
        
        # Return metrics dict
        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "confusion_matrix": cm.tolist(),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr),
            "avg_latency_ms": float(avg_latency),
            "min_latency_ms": float(min_latency),
            "max_latency_ms": float(max_latency),
            "throughput_req_sec": float(throughput),
            "total_time_sec": float(total_time),
            "total_samples": len(self.true_labels),
            "timestamp": datetime.now().isoformat(),
            "brain_api": API_BASE_URL,
            "dataset": TEST_DATASET,
            "test_limit": TEST_LIMIT,
            "batch_size": BATCH_SIZE
        }

def main():
    print("\n" + "="*60)
    print("🧪 TWO-LAPTOP ML MODEL ACCURACY TESTING")
    print("="*60 + "\n")
    
    print(f"Configuration:")
    print(f"  Brain API:  {API_BASE_URL}")
    print(f"  Dataset:    {TEST_DATASET}")
    print(f"  Test limit: {TEST_LIMIT} samples")
    print(f"  Batch size: {BATCH_SIZE}\n")
    
    # Initialize tester
    tester = RemoteModelTester(API_BASE_URL)
    
    # Step 1: Health check
    print("STEP 1: Health Check")
    print("-" * 60)
    if not tester.health_check():
        print("\n❌ Cannot connect to Brain API. Make sure:")
        print("   1. Laptop A is running Brain API on port 8000")
        print("   2. Brain IP is correct (update BRAIN_IP in script)")
        print("   3. Firewall port 8000 is open")
        print("   4. Both laptops are on same network\n")
        return
    
    # Step 2: Load data
    print("\nSTEP 2: Load Test Dataset")
    print("-" * 60)
    X_test, y_test = tester.load_test_data(TEST_DATASET, limit=TEST_LIMIT)
    if X_test is None:
        print("\n❌ Failed to load dataset. Check:")
        print("   1. File path is correct")
        print("   2. CSV has at least 9 columns (8 features + label)")
        print("   3. Features are numerical\n")
        return
    
    # Step 3: Run tests
    print("\nSTEP 3: Run Accuracy Tests")
    print("-" * 60)
    tester.run_batch_test(X_test, y_test, batch_size=BATCH_SIZE)
    
    # Step 4: Calculate metrics
    print("\nSTEP 4: Calculate Metrics")
    print("-" * 60)
    metrics = tester.calculate_metrics()
    
    if metrics is None:
        return
    
    # Step 5: Save report
    print("STEP 5: Save Report")
    print("-" * 60)
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✓ Report saved to: {report_file}\n")
    
    # Step 6: Summary
    if metrics['accuracy'] > 0.95:
        print("✅ TESTING PASSED - Model accuracy is excellent!\n")
    elif metrics['accuracy'] > 0.85:
        print("⚠️  TESTING PASSED - Model accuracy is acceptable\n")
    else:
        print("❌ TESTING FAILED - Model accuracy is below acceptable threshold\n")

if __name__ == "__main__":
    # Ask for Laptop A IP if not configured
    default_ip = BRAIN_IP
    user_ip = input(f"Enter Laptop A IP address (or press Enter for {default_ip}): ").strip()
    if user_ip:
        BRAIN_IP = user_ip
        API_BASE_URL = f"http://{BRAIN_IP}:{BRAIN_PORT}"
    
    # Ask for dataset
    user_dataset = input(f"Enter dataset path (or press Enter for {TEST_DATASET}): ").strip()
    if user_dataset:
        TEST_DATASET = user_dataset
    
    # Ask for test limit
    user_limit = input(f"Enter number of samples to test (or press Enter for {TEST_LIMIT}): ").strip()
    if user_limit:
        try:
            TEST_LIMIT = int(user_limit)
        except:
            pass
    
    main()
