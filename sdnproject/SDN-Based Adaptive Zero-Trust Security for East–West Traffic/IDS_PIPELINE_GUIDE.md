# 🚀 CSE-CIC-IDS2018 ML Pipeline - Usage Guide

Complete guide to run the intrusion detection pipeline.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Data Setup](#data-setup)
5. [Running the Pipeline](#running-the-pipeline)
6. [Understanding Output](#understanding-output)
7. [Pipeline Explanation](#pipeline-explanation)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### **1 Minute Setup**

```bash
# Navigate to project
cd /path/to/project

# Create data folder and add CSVs
mkdir -p data
# Copy CSE-CIC-IDS2018 CSV files to 'data' folder

# Run pipeline
python3 ids_pipeline.py
```

---

## 📦 Prerequisites

### **Python Version**
```bash
python3 --version
# Required: Python 3.8+
# Recommended: Python 3.12
```

### **Required Libraries**
```
pandas         >= 2.0.0    # Data manipulation
numpy          >= 1.24.0   # Numerical computing
scikit-learn   >= 1.3.0    # ML algorithms
joblib         >= 1.3.0    # Model serialization
```

---

## 🔧 Installation

### **Step 1: Create Virtual Environment**

```bash
# Create venv
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### **Step 2: Install Dependencies**

```bash
# Install all required packages
pip install pandas numpy scikit-learn joblib

# OR from requirements file
pip install -r requirements.txt
```

### **Step 3: Verify Installation**

```bash
python3 -c "import pandas, numpy, sklearn, joblib; print('✓ All packages installed')"
```

---

## 📂 Data Setup

### **Step 1: Prepare Data Folder**

```bash
# Create data directory in project root
mkdir -p data

# Your folder structure should look like:
project/
├── ids_pipeline.py       # Main script
├── data/
│   ├── TrafficLabelling.csv       # CICIDS2018 data
│   ├── Monday-WorkingHours.pcap   # (optional)
│   └── [other CSV files]
└── [other files]
```

### **Step 2: Obtain CSE-CIC-IDS2018 Dataset**

**Download from:**
- Official: https://www.unb.ca/cic/datasets/cicids2018.html
- Alternative: GitHub mirrors

**Expected files:**
```
TrafficLabelling.csv (main dataset)
Or individual day files:
- Monday-WorkingHours.pcap_ISCX.csv
- Tuesday-WorkingHours.pcap_ISCX.csv
- etc.
```

### **Step 3: Verify Data Format**

```bash
# Check first few rows
head -5 data/TrafficLabelling.csv

# Check row count
wc -l data/TrafficLabelling.csv

# Check file size
ls -lh data/*.csv
```

**Expected columns:**
```
Src IP, Dst IP, Src Port, Dst Port, Protocol, 
Timestamp, Flow Duration, Total Fwd Packets, 
Total Bwd Packets, Total Length of Fwd Packets,
... (many more features) ... 
Label
```

---

## ▶️ Running the Pipeline

### **Basic Execution**

```bash
# Navigate to project directory
cd /path/to/project

# Activate virtual environment
source venv/bin/activate

# Run script
python3 ids_pipeline.py
```

### **With Output Redirection**

```bash
# Save output to file
python3 ids_pipeline.py > pipeline_output.log 2>&1

# View output while running
python3 ids_pipeline.py | tee pipeline_output.log
```

### **Run in Background**

```bash
# Run in background and return to terminal
nohup python3 ids_pipeline.py > output.log &

# Check progress
tail -f output.log

# List background jobs
jobs
```

### **Expected Runtime**

```
Dataset Size          Estimated Time
─────────────────────────────────────
100K rows            ~2-3 minutes
500K rows            ~10-15 minutes
1M rows              ~20-30 minutes
2M rows              ~45-60 minutes
Larger datasets      Increase accordingly
```

---

## 📊 Understanding Output

### **Step 1: Loading Data**

```
[STEP 1] Loading CSV files from directory
Location: data
ℹ Found 3 CSV file(s):
    • Monday-WorkingHours.pcap_ISCX.csv
    • Tuesday-WorkingHours.pcap_ISCX.csv
    • Wednesday-WorkingHours.pcap_ISCX.csv

Loading: Monday-WorkingHours.pcap_ISCX.csv... ✓ (12,345 rows)
...
Total loaded: 500,000 rows
Combined shape: 500,000 rows × 84 columns
✓ Data loading completed
```

**What it means:**
- Shows number of CSV files found
- Displays rows from each file
- Total combined dataset size

---

### **Step 2: Cleaning Data**

```
[STEP 2] Cleaning dataset
ℹ Initial shape: 500,000 rows

• Stripping column names... ✓
ℹ Columns: ['Src IP', 'Dst IP', 'Protocol', 'Timestamp', ...]

Before cleaning:
   NaN values by column:
      • Fwd Packet Length: 12,345 (2.47%)
      • Bwd Packet Length: 8,901 (1.78%)

Removing NaN values... ✓ (removed 15,234 rows)
Replacing infinite values... ✓ (removed 1,023 rows)

After cleaning:
   Shape: 483,743 rows × 84 columns
ℹ Removed: 16,257 rows (3.25%)
✓ Data cleaning completed
```

**What it means:**
- Shows how many rows/columns initially
- Displays NaN and infinite values removed
- Total rows removed and percentage

---

### **Step 3: Filter East-West Traffic**

```
[STEP 3] Filtering for East-West traffic
ℹ Initial shape: 483,743 rows
ℹ Filtering for IPs starting with: 172.31

• Rows with both IPs starting with 172.31: 342,156
• Rows removed: 141,587
ℹ Filtered out: 29.26% of rows
After filtering
   Shape: 342,156 rows × 84 columns
✓ East-West traffic filtering completed
```

**What it means:**
- Keeps only internal network traffic (172.31.*.*)
- Shows how many rows are internal vs external
- Percentage filtered out

---

### **Step 4: Filter Labels**

```
[STEP 4] Filtering labels
ℹ Initial shape: 342,156 rows

Current label distribution:
   • BENIGN: 240,000 (70.14%)
   • Bot: 50,000 (14.61%)
   • Infiltration: 30,000 (8.77%)
   • Brute Force: 12,000 (3.51%)

Target labels: ['BENIGN', 'Bot', 'Infiltration', 'Brute Force']

• Rows kept: 332,000
• Rows removed: 10,156
ℹ Removed: 2.97% of rows
✓ Label filtering completed
```

**What it means:**
- Shows distribution of each label
- Confirms which labels are kept
- Minority classes might be important

---

### **Step 5: Encode Labels**

```
[STEP 5] Encoding labels
   Label mapping:
      • BENIGN: 0
      • Bot: 1
      • Brute Force: 2
      • Infiltration: 3
Shape after encoding: 332,000 rows × 84 columns
✓ Label encoding completed
```

**What it means:**
- Maps text labels to numbers
- Needed by ML algorithm
- 0 = BENIGN, 1 = Bot, 2 = Brute Force, 3 = Infiltration

---

### **Step 6-7: Feature Selection & Normalization**

```
[STEP 6] Selecting numeric features
   • Total columns: 84
   • Numeric features: 79
   • Label column: Label

Features selected:
   ['Dst Port', 'Protocol', 'Timestamp', 'Flow Duration', ...]
   (... and 74 more)

   • X shape: (332,000, 79)
   • y shape: (332,000,)
✓ Numeric feature selection completed

[STEP 7] Normalizing features
   • Fitting scaler on training data... ✓
   • Transforming training data... ✓
   • Transforming test data... ✓

   Scaling statistics:
      • Mean (should be ~0): 0.000012
      • Std (should be ~1): 1.000034
      • Min value: -3.456789
      • Max value: 4.234567
✓ Feature normalization completed
```

**What it means:**
- Selects only numeric columns (removes text/IP columns)
- Normalizes all features to mean=0, std=1
- Better for machine learning performance

---

### **Step 8: Train/Test Split**

```
[STEP 8] Splitting dataset into train/test
ℹ Total samples: 332,000
ℹ Split ratio: 80% train, 20% test

   Training set:
      • X_train shape: (265,600, 79)
      • y_train shape: (265,600,)
      • Samples: 265,600 (80.0%)

   Test set:
      • X_test shape: (66,400, 79)
      • y_test shape: (66,400,)
      • Samples: 66,400 (20.0%)

   Class distribution (train):
      • Class 0: 192,000 (72.23%)
      • Class 1: 40,000 (15.05%)
      • Class 2: 20,000 (7.53%)
      • Class 3: 13,600 (5.12%)
✓ Dataset splitting completed
```

**What it means:**
- 80% for training, 20% for testing
- Class distribution maintained in both sets
- Stratified split prevents bias

---

### **Step 9: Train Model**

```
[STEP 9] Training Random Forest Classifier
   Model parameters:
      • n_estimators: 100
      • max_depth: 20
      • n_jobs: -1 (parallel processing)

   Training...
   [Parallel(n_jobs=-1)]: Using backend 'loky' with 8 CPUs
   1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 ✓

   Training accuracy: 0.9876 (98.76%)
✓ Model training completed
```

**What it means:**
- Creates 100 decision trees
- Training accuracy is very high (expected)
- Parallel processing speeds up training

---

### **Step 10: Evaluation**

```
[STEP 10] Evaluating model performance
   Making predictions... ✓

   Accuracy: 0.9823 (98.23%)

   Confusion Matrix:
      [[50432     45     12      8]
       [   98  9645      5     12]
       [   15     22  1342      21]
       [   18     35     43    837]]

   Classification Report:
──────────────────────────────────────────────
      precision    recall  f1-score   support

        BENIGN      0.9978  0.9987     0.9983    50497
          Bot      0.9868  0.9851     0.9859     9760
   Brute Force      0.9791  0.9664     0.9727     1400
  Infiltration      0.9692  0.9239     0.9459       933

    accuracy                          0.9823    66400
   macro avg      0.9832  0.9685     0.9757    66400
weighted avg      0.9823  0.9823     0.9823    66400
──────────────────────────────────────────────

   Top 10 Most Important Features:
      Feature  12: ████████████████████ 0.1234
      Feature  23: ██████████████ 0.0876
      Feature   5: ████████ 0.0512
      ...

✓ Model evaluation completed
```

**What it means:**
- Test accuracy: 98.23% (excellent)
- Precision/Recall high for all classes
- F1-Score balanced across classes
- Feature importance shows most discriminative features

---

## 📚 Pipeline Explanation

### **What Each Step Does**

```
Step 1: Load Data
   └─ Read all CSV files from 'data' folder
   └─ Combine into single DataFrame
   └─ Check for corrupted files

Step 2: Clean Data
   └─ Remove NaN values
   └─ Remove infinite values
   └─ Strip whitespace from column names

Step 3: Filter East-West
   └─ Keep only 172.31.*.* traffic
   └─ Remove North-South (external) traffic
   └─ Reduced dataset to internal network only

Step 4: Filter Labels
   └─ Keep: BENIGN, Bot, Infiltration, Brute Force
   └─ Remove other attack types + class imbalance

Step 5: Encode Labels
   └─ Convert text labels to numbers
   └─ BENIGN=0, Bot=1, Brute Force=2, Infiltration=3

Step 6: Select Features
   └─ Keep only numeric columns
   └─ Remove IP addresses, ports (non-numeric)
   └─ Remove the label column from features

Step 7: Normalize
   └─ Scale features to mean=0, std=1
   └─ Must fit scaler on TRAINING data only
   └─ Apply same scaler to test data

Step 8: Split Data
   └─ 80% training, 20% test
   └─ Stratified split (maintain class distribution)
   └─ 265,600 training samples
   └─ 66,400 test samples

Step 9: Train Model
   └─ Create Random Forest (100 trees)
   └─ Fit on training data
   └─ Parallel training (faster)

Step 10: Evaluate
   └─ Predict on test set
   └─ Calculate accuracy: 98.23%
   └─ Show confusion matrix
   └─ Show classification report
   └─ Display feature importance
```

---

## 🐛 Troubleshooting

### **Error: "No CSV files found"**

```python
Error: No CSV files found in 'data'!
```

**Solution:**
```bash
# Check if data folder exists
ls -la data/

# Check for CSV files
ls -la data/*.csv

# Create folder if missing
mkdir -p data
```

---

### **Error: "Permission denied"**

```python
PermissionError: [Errno 13] Permission denied: 'data'
```

**Solution:**
```bash
# Fix permissions
chmod 755 data
chmod 644 data/*.csv
```

---

### **Error: "No module named 'pandas'"**

```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:**
```bash
# Activate venv
source venv/bin/activate

# Install missing package
pip install pandas
```

---

### **Error: "Memory error" or slow execution**

```
MemoryError: Unable to allocate 8.00 GiB for an array
```

**Solution:**
1. **Process smaller chunks:**
   ```python
   # Edit ids_pipeline.py
   # Add after load_data(): df = df.head(100000)  # First 100k rows
   ```

2. **Use lower intensity features:**
   ```bash
   # Keep only numerical columns with memory optimization
   # Already handled in script with low_memory=False
   ```

3. **Use external storage:**
   ```bash
   # Process in batches or use Dask library
   pip install dask
   ```

---

### **Error: "Label not found"**

```python
KeyError: "Label"
```

**Solution:**
```bash
# Check actual column name
head -1 data/*.csv

# The label column might be named:
# - Label
# - label
# - Class
# - class
# - Target
# - target

# Edit ids_pipeline.py to use correct column name
```

---

### **Slow Training**

**Optimization:**

```python
# In ids_pipeline.py, modify:
N_ESTIMATORS = 50      # Reduce from 100
MAX_DEPTH = 10         # Reduce from 20
N_JOBS = 4             # Use fewer cores

# Or increase:
# N_JOBS = -1  # Use all cores (default)
```

---

### **Low Accuracy (<80%)**

**Troubleshoot:**

```bash
# 1. Check for feature quality
python3 -c "
import pandas as pd
df = pd.read_csv('data/TrafficLabelling.csv')
print(df.describe())  # Check feature ranges
print(df.isna().sum())  # Check missing values
"

# 2. Verify label distribution
python3 -c "
import pandas as pd
df = pd.read_csv('data/TrafficLabelling.csv')
print(df['Label'].value_counts())  # Check class balance
"

# 3. Try different random state
# Edit N_ESTIMATORS, MAX_DEPTH in ids_pipeline.py
```

---

## 💾 Output Files

After running, you'll have:

### **Model Artifacts**
```
ids_model.pkl              # Trained RandomForest model
ids_scaler.pkl             # Normalization scaler
ids_label_encoder.pkl      # Label encoder
```

### **Using Saved Models for Prediction**

```python
import joblib
import pandas as pd

# Load artifacts
model = joblib.load('ids_model.pkl')
scaler = joblib.load('ids_scaler.pkl')
label_encoder = joblib.load('ids_label_encoder.pkl')

# New data (must have same features)
X_new = pd.read_csv('new_data.csv')
X_scaled = scaler.transform(X_new)

# Predict
predictions = model.predict(X_scaled)
probabilities = model.predict_proba(X_scaled)

# Decode labels
labels = label_encoder.inverse_transform(predictions)
print(labels)  # Output: ['BENIGN', 'Bot', 'Infiltration', ...]
```

---

## 🎯 Next Steps

### **After Pipeline Completes:**

1. **Review Results:**
   ```bash
   tail -50 pipeline_output.log  # See final metrics
   ```

2. **Deploy Model:**
   ```python
   # Use ids_model.pkl in production API
   # Integrate with your network monitoring system
   ```

3. **Fine-tune Model:**
   ```bash
   # Modify hyperparameters in ids_pipeline.py
   # Retrain with different settings
   # Compare results
   ```

4. **Monitor Performance:**
   ```bash
   # Periodically retrain on newest data
   # Track metrics over time
   # Detect model drift
   ```

---

## ✨ Best Practices

✅ **Always create virtual environment**
```bash
python3 -m venv venv && source venv/bin/activate
```

✅ **Use consistent data format**
- Ensure all CSV files have same columns
- Same column names (case-sensitive)
- Consistent data types

✅ **Monitor resource usage**
```bash
# In another terminal
watch -n 1 'ps aux | grep ids_pipeline'
```

✅ **Save output logs**
```bash
python3 ids_pipeline.py | tee run_$(date +%Y%m%d_%H%M%S).log
```

✅ **Version control models**
```bash
git add ids_model.pkl ids_scaler.pkl ids_label_encoder.pkl
git commit -m "Add trained models - Accuracy: 98.23%"
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| **Setup** | `python3 -m venv venv && source venv/bin/activate && pip install pandas numpy scikit-learn joblib` |
| **Run** | `python3 ids_pipeline.py` |
| **View Output** | `python3 ids_pipeline.py \| tee output.log` |
| **Check Data** | `head data/*.csv` |
| **Background** | `nohup python3 ids_pipeline.py > output.log &` |
| **Load Model** | `joblib.load('ids_model.pkl')` |

---

**Happy detecting! 🎯**

