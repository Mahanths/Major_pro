# 🧪 Two-Laptop Model Accuracy Testing Guide

Complete step-by-step guide to test ML models using two physical laptops with real-world scenarios.

---

## 📊 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      NETWORK (WiFi/Ethernet)                 │
└─────────────────────────────────────────────────────────────┘
                    ▲                                    ▲
                    │                                    │
        ┌───────────┴──────────┐            ┌──────────┴──────────┐
        │                      │            │                     │
        │  🧠 LAPTOP A         │            │   💻 LAPTOP B       │
        │  (Brain Server)      │            │   (Test Client)     │
        │                      │            │                     │
        │ • API Server         │            │ • Dashboard UI      │
        │   :8000              │────────────│ • API Requests      │
        │ • Models Loaded      │            │ • Test Scripts      │
        │ • Inference Engine   │            │ • Accuracy Reports  │
        │ • Trust Calculator   │            │                     │
        │                      │            │                     │
        └──────────────────────┘            └─────────────────────┘
           Mahanth's Laptop                    Testing Laptop
```

**Role Distribution:**
- **Laptop A (Brain):** Runs FastAPI model server on port 8000
- **Laptop B (Tester):** Connects to Brain API, sends test data, measures accuracy

---

## ✅ PRE-TESTING CHECKLIST

### **Before You Start - DO NOT SKIP! ⚠️**

- [ ] Both laptops on same WiFi network
- [ ] Laptop A (Brain) has Python 3.12 + venv + dependencies installed
- [ ] Laptop B (Tester) has Python 3.12 installed
- [ ] Latest code pushed to GitHub
- [ ] Test datasets available (NSL-KDD or CICIDS)
- [ ] Both laptops have 8+ GB RAM free
- [ ] Network connectivity tested (ping between laptops)
- [ ] Firewall ports open (8000, 8080 on Laptop A)

---

## 🔧 PHASE 1: Setup Laptop A (Brain Server)

### **STEP 1.1: Verify Project Structure on Laptop A**

```bash
cd /home/mahanth-s/sdnproject/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic

# List structure
tree -L 2 -I '__pycache__|*.pyc'

# Expected output:
# ├── brain/
# │   ├── app.py
# │   ├── feature_handler.py
# │   ├── hybrid_engine.py
# │   ├── trust_calculator.py
# │   ├── models/
# │   │   ├── isolation_forest_model.pkl
# │   │   └── xgboost_model.pkl
# │   └── requirements.txt
# ├── data/
# │   ├── nslkdd_training_8features.csv
# │   └── [other CSVs]
# ├── dashboard/
# ├── training/
# └── [docs]
```

**✅ If structure is correct, continue. ❌ If missing, run:**
```bash
git pull origin master  # Get latest code
```

---

### **STEP 1.2: Activate Virtual Environment on Laptop A**

```bash
# Create venv if doesn't exist
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify (you should see (venv) in terminal)
which python3
# Output: /path/to/venv/bin/python3

# Install dependencies
pip install -r brain/requirements.txt

# Verify installations
python3 -c "import fastapi, xgboost, sklearn; print('✓ All packages installed')"
```

**Expected output:**
```
✓ All packages installed
```

---

### **STEP 1.3: Get Laptop A's IP Address**

**This is CRITICAL for Laptop B to connect!**

```bash
# Linux/Mac - Method 1
hostname -I
# Output: 192.168.1.100

# Linux/Mac - Method 2
ifconfig | grep inet
# Look for: inet 192.168.x.x

# Mac - Method 3
networksetup -getinfo Wi-Fi | grep "IP"

# Windows/All - Method 4
ipconfig (Windows) or ip addr (Linux)
```

**📝 WRITE DOWN THIS IP ADDRESS:**
```
Laptop A IP: ___________________  (Example: 192.168.1.100)
```

---

### **STEP 1.4: Start Brain API Server on Laptop A**

```bash
# Ensure you're in project root
pwd
# Should show: /home/mahanth-s/sdnproject/SDN-Based Adaptive Zero-Trust Security for East–West Traffic

# Activate venv
source venv/bin/activate

# Start server (binds to 0.0.0.0:8000 so network-accessible)
uvicorn brain.app:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
# 🧠 Zero-Trust SDN Brain Starting Up [timestamp]
# ✓ Hybrid engine ready with real models
```

**✅ DO NOT CLOSE THIS TERMINAL - Keep it running!**

Verify server is working:
```bash
# In ANOTHER terminal on Laptop A
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "models": {"isolation_forest": "loaded", "xgboost": "loaded"},
#   "timestamp": "2026-03-26T..."
# }
```

---

## 🖥️ PHASE 2: Setup Laptop B (Test Client)

### **STEP 2.1: Clone Project on Laptop B**

**On Laptop B:**

```bash
# Go to home directory
cd ~

# Clone project (requires internet)
git clone https://github.com/Mahanths/Major_pro.git

# Go to project
cd Major_pro/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic

# List to verify
ls -la
# Should show: brain/, dashboard/, training/, data/, etc.
```

---

### **STEP 2.2: Create Python Virtual Environment on Laptop B**

```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install minimum requirements
pip install fastapi uvicorn pandas numpy scikit-learn xgboost

# Verify
python3 -c "import requests; print('✓ Testing libraries ready')"
```

---

### **STEP 2.3: Create Test Runner Script on Laptop B**

Create file: `test_runner.py`

```bash
cat > test_runner.py << 'EOF'
#!/usr/bin/env python3
"""
Two-Laptop Model Accuracy Testing Script
Tests ML models on Laptop A from Laptop B
"""

import requests
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# CONFIGURATION - MODIFY THESE!
BRAIN_IP = "192.168.1.100"  # ← CHANGE THIS to Laptop A IP!
BRAIN_PORT = 8000
API_BASE_URL = f"http://{BRAIN_IP}:{BRAIN_PORT}"

TEST_DATASET = "data/nslkdd_training_8features.csv"  # Or CICIDS
BATCH_SIZE = 100  # Send 100 flows per request
TEST_LIMIT = 5000  # Test on 5000 flows (not all, saves time)

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
            resp = requests.get(f"{self.api_url}/health", timeout=5)
            if resp.status_code == 200:
                print("✅ Brain API is ONLINE")
                print(f"   Models: {resp.json().get('models')}")
                return True
            else:
                print(f"❌ Brain API returned {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to Brain API: {e}")
            return False
    
    def load_test_data(self, csv_file, limit=5000):
        """Load test dataset"""
        print(f"\n📂 Loading test data from {csv_file}...")
        try:
            df = pd.read_csv(csv_file)
            
            # Separate features and labels
            # Assuming last column is label (0=benign, 1=malicious)
            X = df.iloc[:limit, :-1].values  # All columns except last
            y = df.iloc[:limit, -1].values   # Last column is label
            
            print(f"✓ Loaded {len(X)} samples")
            print(f"  Features per sample: {X.shape[1]}")
            print(f"  Label distribution: {np.bincount(y.astype(int))}")
            
            return X, y
        except Exception as e:
            print(f"❌ Error loading data: {e}")
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
                pred = 1 if result.get('is_malicious', False) else 0
                confidence = result.get('malicious_probability', 0)
                return pred, confidence, elapsed
            else:
                print(f"❌ API error: {resp.status_code}")
                return None, None, None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None, None, None
    
    def run_batch_test(self, X, y, batch_size=100):
        """Test all samples"""
        print(f"\n🧪 Running batch test ({len(X)} samples)...")
        print(f"   Batch size: {batch_size}")
        
        total = len(X)
        processed = 0
        
        for i in range(0, total, batch_size):
            batch_X = X[i:i+batch_size]
            batch_y = y[i:i+batch_size]
            
            print(f"\n📊 Batch {i//batch_size + 1}: Samples {i} to {min(i+batch_size, total)}")
            
            for j, (features, true_label) in enumerate(zip(batch_X, batch_y)):
                pred, conf, elapsed = self.test_single_flow(features)
                
                if pred is not None:
                    self.pred_labels.append(pred)
                    self.true_labels.append(true_label)
                    self.timings.append(elapsed)
                    
                    # Print every 50 samples
                    if (j + 1) % 50 == 0:
                        print(f"  ✓ Processed {j+1}/{len(batch_X)}")
                else:
                    print(f"  ❌ Failed on sample {j}")
            
            processed += len(batch_X)
            accuracy_so_far = accuracy_score(self.true_labels, self.pred_labels)
            print(f"  Accuracy so far: {accuracy_so_far:.2%}")
    
    def calculate_metrics(self):
        """Calculate accuracy metrics"""
        print(f"\n📈 CALCULATING METRICS...\n")
        
        if len(self.true_labels) == 0:
            print("❌ No results to analyze")
            return
        
        accuracy = accuracy_score(self.true_labels, self.pred_labels)
        precision = precision_score(self.true_labels, self.pred_labels, average='binary')
        recall = recall_score(self.true_labels, self.pred_labels, average='binary')
        f1 = f1_score(self.true_labels, self.pred_labels, average='binary')
        cm = confusion_matrix(self.true_labels, self.pred_labels)
        
        # Calculate rates
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        avg_latency = np.mean(self.timings) * 1000  # Convert to ms
        max_latency = np.max(self.timings) * 1000
        
        print("╔════════════════════════════════════════════════════════╗")
        print("║           MODEL ACCURACY TEST RESULTS                  ║")
        print("╚════════════════════════════════════════════════════════╝\n")
        
        print(f"📊 OVERALL METRICS:")
        print(f"   Accuracy:   {accuracy:.4f} ({accuracy*100:.2f}%) {'✅' if accuracy > 0.95 else '⚠️'}")
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
        print(f"   Max Latency:             {max_latency:.2f} ms")
        print(f"   Total Requests:          {len(self.true_labels):,}")
        
        print(f"\n{''.join(['═']*58)}\n")
        
        # Return metrics dict
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "confusion_matrix": cm.tolist(),
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "avg_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "total_samples": len(self.true_labels),
            "timestamp": datetime.now().isoformat()
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
        print("   2. Laptop B IP can reach Laptop A")
        print("   3. Firewall port 8000 is open")
        return
    
    # Step 2: Load data
    print("\nSTEP 2: Load Test Dataset")
    print("-" * 60)
    X_test, y_test = tester.load_test_data(TEST_DATASET, limit=TEST_LIMIT)
    if X_test is None:
        return
    
    # Step 3: Run tests
    print("\nSTEP 3: Run Accuracy Tests")
    print("-" * 60)
    tester.run_batch_test(X_test, y_test, batch_size=BATCH_SIZE)
    
    # Step 4: Calculate metrics
    print("\nSTEP 4: Calculate Metrics")
    print("-" * 60)
    metrics = tester.calculate_metrics()
    
    # Step 5: Save report
    print("\nSTEP 5: Save Report")
    print("-" * 60)
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Report saved to {report_file}")
    
    print("\n✅ TESTING COMPLETE!\n")

if __name__ == "__main__":
    main()
EOF
```

Make it executable:
```bash
chmod +x test_runner.py
```

---

### **STEP 2.4: Configure Test Runner for Your Network**

Edit `test_runner.py` and change:

```python
# Line ~20 - CHANGE THIS!
BRAIN_IP = "192.168.1.100"  # ← Your Laptop A IP from STEP 1.3
```

Example:
```python
BRAIN_IP = "192.168.x.x"  # Replace with actual IP
```

---

## 🚀 PHASE 3: Run Accuracy Tests

### **STEP 3.1: Verify Both Laptops Are Ready**

**On Laptop A:**
```bash
# Terminal 1 - Already running Brain API
uvicorn brain.app:app --host 0.0.0.0 --port 8000

# Terminal 2 - Verify connectivity from other apps
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

**On Laptop B:**
```bash
# Test network connectivity to Laptop A
ping 192.168.1.100
# Should get: "type ctrl+c to quit" and response times

# Test port connectivity
curl http://192.168.1.100:8000/health
# Should return same JSON as above
```

✅ If both work, proceed. ❌ If not, troubleshoot network first.

---

### **STEP 3.2: Run Test on Laptop B**

```bash
cd /path/to/project
source venv/bin/activate

# Run the test script
python3 test_runner.py

# Expected output:
# ===============================================================
# 🧪 TWO-LAPTOP ML MODEL ACCURACY TESTING
# ===============================================================
# 
# Configuration:
#   Brain API:  http://192.168.1.100:8000
#   Dataset:    data/nslkdd_training_8features.csv
#   Test limit: 5000 samples
#   Batch size: 100
#
# STEP 1: Health Check
# ---------------------------------------------------------------
# ✅ Brain API is ONLINE
#    Models: {'isolation_forest': 'loaded', 'xgboost': 'loaded'}
```

---

### **STEP 3.3: Monitor Results**

Test will run and show:

```
📊 Batch 1: Samples 0 to 100
  ✓ Processed 50/100
  ✓ Processed 100/100
  Accuracy so far: 0.98%

📈 CALCULATING METRICS...

╔════════════════════════════════════════════════════════╗
║           MODEL ACCURACY TEST RESULTS                  ║
╚════════════════════════════════════════════════════════╝

📊 OVERALL METRICS:
   Accuracy:   0.9990 (99.90%) ✅
   Precision:  0.9991 (99.91%)
   Recall:     0.9989 (99.89%)
   F1-Score:   0.9990

🎯 CONFUSION MATRIX:
   TP (Caught Attacks):     4987
   TN (Correct Normal):     12000
   FP (False Alarms):       0
   FN (Missed Attacks):     13

⚠️  ERROR RATES:
   False Positive Rate:     0.0000 (0.00%)
   False Negative Rate:     0.0026 (0.26%)

⏱️  LATENCY METRICS:
   Average Latency:         45.23 ms
   Max Latency:             156.78 ms
   Total Requests:          5000

✅ TESTING COMPLETE!
```

---

## 📝 PHASE 4: Advanced Testing Scenarios

### **SCENARIO 1: Stress Testing (High-Volume Requests)**

```bash
cat > stress_test.py << 'EOF'
import concurrent.futures
import requests
import numpy as np
import time

API_URL = "http://192.168.1.100:8000/infer"
THREADS = 10
REQUESTS_PER_THREAD = 100

def send_request(request_id):
    """Send single request"""
    features = np.random.rand(8).tolist()
    payload = {"features": features}
    
    try:
        start = time.time()
        resp = requests.post(API_URL, json=payload, timeout=5)
        elapsed = time.time() - start
        return request_id, resp.status_code, elapsed
    except Exception as e:
        return request_id, None, None

# Run stress test
with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
    futures = [
        executor.submit(send_request, i)
        for i in range(REQUESTS_PER_THREAD * THREADS)
    ]
    
    successful = 0
    failed = 0
    latencies = []
    
    for f in concurrent.futures.as_completed(futures):
        req_id, status, elapsed = f.result()
        if status == 200:
            successful += 1
            latencies.append(elapsed)
        else:
            failed += 1
    
    print(f"\n📊 Stress Test Results:")
    print(f"   Total Requests:      {len(futures):,}")
    print(f"   Successful:          {successful:,}")
    print(f"   Failed:              {failed:,}")
    print(f"   Success Rate:        {successful/len(futures)*100:.2f}%")
    print(f"   Avg Latency:         {np.mean(latencies)*1000:.2f} ms")
    print(f"   Max Latency:         {np.max(latencies)*1000:.2f} ms")
    print(f"   Min Latency:         {np.min(latencies)*1000:.2f} ms")
EOF

python3 stress_test.py
```

---

### **SCENARIO 2: Real-Time Dashboard Testing**

**Run dashboard on Laptop B:**

```bash
cd dashboard
python3 server.py 8080

# Access from browser:
# http://localhost:8080
# or http://192.168.x.x:8080 from other device
```

Login with:
- **Admin:** admin / admin123
- **User:** user1 / pass123

Watch metrics update in real-time! 📊

---

### **SCENARIO 3: Compare Models (NSL-KDD vs CICIDS)**

```bash
cat > compare_models.py << 'EOF'
import pandas as pd
from test_runner import RemoteModelTester

API_URL = "http://192.168.1.100:8000"

datasets = [
    ("NSL-KDD", "data/nslkdd_training_8features.csv", 5000),
    ("CICIDS2023", "data/cicids2023_8features.csv", 5000),
]

results = {}

for name, csv, limit in datasets:
    print(f"\n🧪 Testing {name}...")
    tester = RemoteModelTester(API_URL)
    X, y = tester.load_test_data(csv, limit)
    if X is not None:
        tester.run_batch_test(X, y)
        metrics = tester.calculate_metrics()
        results[name] = metrics

# Compare
print("\n📊 MODEL COMPARISON:")
for name, metrics in results.items():
    print(f"   {name}: {metrics['accuracy']*100:.2f}% accuracy")
EOF

python3 compare_models.py
```

---

## 📋 DO'S AND DON'Ts WHILE TESTING

### ✅ DO's (Best Practices)

1. **DO** keep Brain API running on Laptop A throughout testing
   ```bash
   # Use screen or tmux to keep it running
   screen -S brain
   # Then run: uvicorn brain.app:app --host 0.0.0.0 --port 8000
   ```

2. **DO** test with at least 1000-5000 samples for reliable metrics
   ```python
   TEST_LIMIT = 5000  # Not 10 or 100
   ```

3. **DO** monitor network connectivity during long tests
   ```bash
   # In separate terminal
   ping -c 100 192.168.1.100
   ```

4. **DO** use consistent datasets for comparison
   ```bash
   # Always use same test set when comparing
   TEST_DATASET = "data/nslkdd_training_8features.csv"
   ```

5. **DO** save results for future reference
   ```bash
   # Script auto-saves JSON reports
   # Check: test_report_*.json
   ```

6. **DO** test during off-peak WiFi hours
   - WiFi interference causes high latency
   - Test early morning or late evening

7. **DO** use ethernet if possible (better than WiFi)
   ```bash
   # Wired connection much more stable
   ```

8. **DO** document your test configuration
   ```
   Date: March 26, 2026
   Laptop A IP: 192.168.1.100
   Dataset: NSL-KDD (5000 samples)
   Results: 99.90% accuracy
   ```

9. **DO** verify models loaded correctly on Laptop A
   ```bash
   curl http://192.168.1.100:8000/health
   # Should show: "models": {"isolation_forest": "loaded", "xgboost": "loaded"}
   ```

10. **DO** start with small batch sizes and increase gradually
    ```python
    BATCH_SIZE = 50   # Start small
    # Then: 100, 500, 1000
    ```

---

### ❌ DON'Ts (Common Mistakes)

1. **DON'T** close Laptop A terminal running Brain API
   ```bash
   # ❌ DON'T press Ctrl+C here!
   # The API goes down and tests fail
   ```

2. **DON'T** use hardcoded localhost (127.0.0.1) on Laptop B
   ```bash
   # ❌ WRONG:
   BRAIN_IP = "127.0.0.1"  # Only works on same machine
   
   # ✅ RIGHT:
   BRAIN_IP = "192.168.1.100"  # Actual IP
   ```

3. **DON'T** test with tiny datasets (< 100 samples)
   ```python
   # ❌ Too small, unreliable:
   TEST_LIMIT = 10
   
   # ✅ Minimum reliable:
   TEST_LIMIT = 1000
   ```

4. **DON'T** mix different models in single test
   ```bash
   # ❌ DON'T retrain model mid-test
   # ✅ Finish test first, then retrain
   ```

5. **DON'T** assume high latency = model is slow
   ```bash
   # Network latency causes delays, not always the model
   # Test on wired connection to verify
   ```

6. **DON'T** ignore error messages in test output
   ```bash
   # ❌ DON'T: "Accuracy is low, moving on"
   # ✅ DO: Investigate why accuracy is low
   ```

7. **DON'T** test with incomplete datasets
   ```bash
   # ❌ DON'T run on CICIDS if converter not run first
   # ✅ Verify CSV has 8 features before testing
   ```

8. **DON'T** modify test script while test is running
   ```bash
   # ❌ Don't edit test_runner.py during execution
   ```

9. **DON'T** test from unreliable WiFi (coffee shops, etc.)
   ```bash
   # ❌ Inconsistent results due to WiFi interference
   # ✅ Use stable home WiFi or ethernet
   ```

10. **DON'T** forget to activate venv on Laptop B
    ```bash
    # ❌ This will fail:
    python3 test_runner.py
    
    # ✅ Always do:
    source venv/bin/activate
    python3 test_runner.py
    ```

---

## 🎯 EXPECTED RESULTS & BENCHMARKS

### **NSL-KDD Dataset (Should Expect)**

```
✅ Accuracy:           99.85% - 99.95%
✅ Precision:          99.80% - 99.95%
✅ Recall:             98.00% - 99.50%
✅ False Positive Rate: 0.00% - 0.10%
✅ False Negative Rate: 0.50% - 2.00%
✅ Avg Latency:        40 - 80 ms
✅ Throughput:         500-1000 req/sec
```

### **CICIDS Dataset (Real Data - Should Expect)**

```
✅ Accuracy:           97.00% - 99.00%
✅ Precision:          96.00% - 99.50%
✅ Recall:             95.00% - 98.00%
✅ False Positive Rate: 0.50% - 2.00%
✅ False Negative Rate: 1.00% - 5.00%
✅ Avg Latency:        50 - 100 ms
✅ Throughput:         400-800 req/sec
```

### **Red Flags (Something Wrong)**

```
❌ Accuracy < 70%              → Model not loaded correctly
❌ All predictions same value  → Model returning static output
❌ Latency > 500ms             → Network congestion or CPU bottleneck
❌ Connection refused          → Laptop A API crashed or port wrong
❌ Random results              → Data format mismatch
```

---

## 🔍 TROUBLESHOOTING COMMON ISSUES

### **Issue 1: "Connection refused" on Laptop B**

```bash
❌ Error: [Errno 111] Connection refused

Solution:
1. Verify Laptop A IP is correct
   ping 192.168.1.100
   
2. Verify API is running on Laptop A
   curl http://192.168.1.100:8000/health
   
3. Check firewall (port 8000 open?)
   sudo ufw allow 8000
   
4. Restart API on Laptop A
   pkill -f "uvicorn brain.app"
   uvicorn brain.app:app --host 0.0.0.0 --port 8000
```

---

### **Issue 2: "Accuracy is too low" (< 80%)**

```bash
❌ Result: Accuracy: 0.5876 (58.76%)

Solutions:
1. Check model files exist and are not corrupted
   ls -lh brain/models/*.pkl
   
2. Load model directly and test
   python3 -c "import joblib; m = joblib.load('brain/models/xgboost_model.pkl'); print('✓ OK')"
   
3. Verify dataset format (need exactly 8 features)
   head data/test_dataset.csv | wc -w
   # Should show 9 columns (8 features + 1 label)
   
4. Check for NaN values in test dataset
   python3 -c "import pandas as pd; df = pd.read_csv('data/nslkdd_training_8features.csv'); print(df.isna().sum())"
```

---

### **Issue 3: "Timeout waiting for response"**

```bash
❌ Error: requests.exceptions.Timeout: Connection timeout

Solutions:
1. Check network stability
   ping -c 20 192.168.1.100
   # Look for packet loss / high latency
   
2. Check Laptop A CPU usage
   # On Laptop A: top
   # Should be < 80% CPU utilization
   
3. Reduce batch size
   BATCH_SIZE = 10  # Instead of 100
   
4. Use wired connection instead of WiFi
   # Ethernet much more stable
   
5. Increase timeout in test script
   resp = requests.post(..., timeout=30)  # Up from 10
```

---

### **Issue 4: "Models not loaded in Brain"**

```bash
❌ Response: {"models": {"isolation_forest": "failed", "xgboost": "failed"}}

Solutions:
1. Check model files exist
   ls brain/models/
   # Should show .pkl files
   
2. Check model file permissions
   chmod 644 brain/models/*.pkl
   
3. Check app.py for errors
   python3 -c "from brain.app import app; print('✓ App loads')"
   
4. Look at Laptop A console for error messages
   # Check Brain API terminal for traceback
   
5. Retrain models
   source venv/bin/activate
   python3 training/train_models.py --dataset data/nslkdd_training_8features.csv
```

---

## 📊 TESTING CHECKLIST (Copy & Use)

```
PRE-TEST SETUP:
☐ Laptop A has Python 3.12 + venv + dependencies
☐ Laptop B has Python 3.12 installed
☐ Both on same WiFi network
☐ Laptop A IP noted: _______________
☐ Test dataset available and verified
☐ Latest code pulled from GitHub

BRAIN API SETUP (Laptop A):
☐ venv activated
☐ dependencies installed (pip install -r brain/requirements.txt)
☐ models loaded (isolation_forest_model.pkl + xgboost_model.pkl present)
☐ API started (uvicorn brain.app:app --host 0.0.0.0 --port 8000)
☐ API responding to health check (curl http://localhost:8000/health)

TEST CLIENT SETUP (Laptop B):
☐ Project cloned from GitHub
☐ venv created and activated
☐ dependencies installed
☐ test_runner.py created and configured
☐ BRAIN_IP updated to correct value
☐ Network connectivity verified (ping to Laptop A works)

TEST EXECUTION:
☐ Laptop A Brain API still running (check console)
☐ Laptop B can reach Laptop A (curl works)
☐ Test dataset accessible on Laptop B
☐ test_runner.py executed successfully
☐ Results reviewed and documented

RESULTS VALIDATION:
☐ Accuracy ≥ 95% (red flag if < 70%)
☐ All metrics calculated (no NaN/None)
☐ Confusion matrix makes sense
☐ Latency < 200ms average
☐ Report saved to JSON file

NEXT STEPS:
☐ Save results to GitHub
☐ Document findings
☐ Plan improvements
```

---

## 🚀 QUICK START (5-MINUTE SUMMARY)

### **Laptop A (Brain):**
```bash
cd /path/to/project
source venv/bin/activate
uvicorn brain.app:app --host 0.0.0.0 --port 8000
# NOTE: Keep this running!
```

### **Laptop B (Tester):**
```bash
# Get IP from Laptop A (e.g., 192.168.1.100)
git clone https://github.com/Mahanths/Major_pro.git
cd Major_pro/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn pandas numpy scikit-learn xgboost requests

# Create & run test
python3 test_runner.py  # Will prompt for Laptop A IP

# Done! Results show accuracy, latency, etc.
```

---

## 📈 INTERPRET YOUR RESULTS

**If you see 99.90% accuracy:** ✅
```
✓ Perfect! Models working as expected
✓ Safe to deploy to production
✓ Next step: Test with real CICIDS data
```

**If you see 95-99% accuracy:** ✅
```
✓ Very good! Acceptable for production
✓ Minor tuning may help
✓ False positive rate is very low (good!)
```

**If you see 85-95% accuracy:** ⚠️
```
⚠️ Means something changed
⚠️ Check: Different dataset? Different models?
⚠️ Action: Retrain models on current data
```

**If you see < 85% accuracy:** ❌
```
❌ Major problem - investigate immediately
❌ Check: Model load errors? Wrong API?
❌ Action: Debug using troubleshooting guide
```

---

## 📝 SAVE YOUR RESULTS

After testing, create a summary:

```bash
# Results go here:
mkdir -p test_results
cp test_report_*.json test_results/

# Create summary
cat > test_results/SUMMARY.txt << 'EOF'
Test Date: March 26, 2026
Test Duration: 45 minutes
Laptop A IP: 192.168.1.100
Dataset: nslkdd_training_8features.csv
Samples Tested: 5000
Accuracy: 99.90%
Precision: 99.91%
Recall: 99.89%
F1-Score: 0.9990
Avg Latency: 45.23 ms
Status: ✅ PASSED

Next Actions:
1. Download real CICIDS data
2. Retrain models
3. Re-test with real data
4. Deploy to production
EOF

# Save to GitHub
git add test_results/
git commit -m "Add test results from two-laptop accuracy testing"
git push origin master
```

---

## 🎯 NEXT PHASE AFTER TESTING PASSES

Once testing is successful (accuracy > 95%):

1. **Deploy Dashboard on Laptop B**
   ```bash
   cd dashboard
   python3 server.py 8080
   # Access: http://localhost:8080
   ```

2. **Get Real CICIDS Data**
   - Download from https://www.unb.ca/cic/datasets/
   - Retrain models
   - Re-test against real attacks

3. **Continuous Monitoring**
   - Keep both laptops running
   - Monitor accuracy over time
   - Add new attack types as discovered

4. **Production Deployment**
   - Integrate with ONOS controller
   - Deploy to real network
   - Enable real-time threat response

---

## 📞 SUPPORT & NEXT STEPS

If you encounter issues or need clarification:

1. Check **Troubleshooting** section above
2. Review **DO's and DON'Ts**
3. Run models directly on Laptop A to isolate issue
4. Check GitHub issues: https://github.com/Mahanths/Major_pro/issues

---

**Good luck with testing! You've got this! 🚀**

