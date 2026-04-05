# Project Structure Analysis & Cleanup Guide

**Generated:** April 5, 2026  
**Current Project Size:** ~1.2 GB  
**After Cleanup:** ~300 MB (recommended)

---

## 📊 Current Project Breakdown

| Directory | Size | Files | Purpose | Status |
|-----------|------|-------|---------|--------|
| **venv** | 811 MB | Many | Python virtual environment | 🟡 Keep locally, exclude from git |
| **data** | 216 MB | 10 | Training datasets (CSV files) | ✅ Keep |
| **training** | 71 MB | 7-8 | Model training scripts | ✅ Keep |
| **brain** | 4.2 MB | 5 | Main API application | ✅ Keep |
| **dashboard** | 96 KB | 3-4 | Web dashboard | ✅ Keep |
| **plan_files** | 348 KB | 25+ | Planning & documentation | ✅ Keep |

| File Type | Size | Count | Purpose | Status |
|-----------|------|-------|---------|--------|
| **ids_*.pkl** | 70 MB | 3 | Trained ML model | ✅ Keep (important!) |
| **ids_pipeline.py** | 32 KB | 1 | IDS training pipeline | ✅ Keep |
| **test_*.py** | 36 KB | 2 | Testing scripts | ✅ Keep |
| **.md files** | 92 KB | 7 | Documentation | ✅ Keep |
| **requirements.txt** | 4 KB | 1 | Dependencies | ✅ Keep |
| **controller/** | 4 KB | 0 | Empty (can remove) | 🟡 Remove |
| **brain.log** | 8 KB | 1 | Log file | 🟡 Can clean |

---

## 📁 Recommended Clean Project Structure

```
my_sdn_project/
│
├── 📂 src/                          # Source code
│   ├── ids_pipeline.py              # ⭐ IDS model training
│   ├── test_runner.py               # Testing suite  
│   ├── test_system.py               # System tests
│   └── requirements.txt             # Dependencies
│
├── 📂 models/                       # Trained models  
│   ├── ids_model.pkl                # ⭐ Trained RandomForest
│   ├── ids_scaler.pkl               # Feature scaler
│   └── ids_label_encoder.pkl        # Label encoder
│
├── 📂 data/                         # Training data
│   ├── cicids2018_8features.csv
│   ├── cicids2019_8features.csv
│   ├── cicids2023_8features.csv
│   ├── nslkdd_training_8features.csv
│   ├── cicids2018_synthetic.csv
│   ├── cicids2019_synthetic.csv
│   ├── cicids2023_synthetic.csv
│   └── nslkdd_realistic.csv
│
├── 📂 brain/                        # ML/Brain system
│   ├── app.py                       # FastAPI server
│   ├── feature_handler.py           # Feature extraction
│   ├── hybrid_engine.py             # ML engine
│   ├── trust_calculator.py          # Trust scoring
│   ├── requirements.txt
│   └── models/                      # Serialized models
│
├── 📂 training/                     # Training utilities
│   ├── train_models.py              # Main trainer
│   ├── pcap_to_csv.py               # PCAP converter
│   ├── synthetic_data_generator.py  # Data gen
│   ├── cicids_downloader.py         # Download utility
│   ├── nslkdd_generator.py
│   ├── cicids_converter.py
│   ├── nslkdd_converter.py
│   ├── improved_trainer.py
│   └── data/                        # Temp processing
│
├── 📂 dashboard/                    # Web UI
│   ├── index.html                   # Frontend
│   ├── server.py                    # Backend
│   ├── js/                          # JavaScript
│   └── css/                         # Styling
│
├── 📂 docs/                         # Documentation
│   ├── IDS_PIPELINE_GUIDE.md
│   ├── IDS_PIPELINE_SUMMARY.md
│   ├── PIPELINE_QUICK_FIX_REFERENCE.md
│   ├── PIPELINE_FIXES_AND_TROUBLESHOOTING.md
│   ├── SESSION_SUMMARY.md
│   ├── EXECUTIVE_SUMMARY.txt
│   └── QUICK_REFERENCE_CARD.md
│
├── 📂 planning/                     # Planning docs (optional)
│   ├── 00_START_HERE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── DEPLOYMENT_NAVIGATION_GUIDE.md
│   ├── TWO_LAPTOP_TESTING_GUIDE.md
│   ├── TESTING_QUICK_REFERENCE.md
│   └── ...other guides...
│
├── 📄 .gitignore                    # Git ignore file
├── 📄 .git/                         # Version control
├── 📄 README.md                     # Project overview
├── 📄 requirements.txt              # Top-level dependencies
└── 📄 RUN_TESTS.sh                  # Test runner script

```

---

## ✅ REQUIRED FILES (MUST KEEP)

### Core ML Model (Critical!)
```
✅ ids_model.pkl           (70 MB) - Your trained RandomForest model
✅ ids_scaler.pkl          (4 KB)  - Feature normalizer
✅ ids_label_encoder.pkl   (4 KB)  - Label encoder
```

**Why:** Without these, you lose your trained model!

### Source Code (Essential)
```
✅ ids_pipeline.py         (32 KB) - IDS training pipeline
✅ test_runner.py          (16 KB) - Testing suite
✅ test_system.py          (20 KB) - System tests
```

### Brain/API System
```
✅ brain/app.py            - FastAPI server
✅ brain/feature_handler.py
✅ brain/hybrid_engine.py
✅ brain/trust_calculator.py
✅ brain/requirements.txt
```

### Training Tools
```
✅ training/train_models.py
✅ training/pcap_to_csv.py
✅ training/synthetic_data_generator.py
```

### Data
```
✅ data/*.csv              (10 files) - Training datasets
```

### Configuration
```
✅ requirements.txt        - Python dependencies
✅ RUN_TESTS.sh           - Test runner
```

---

## 📋 DOCUMENTATION (KEEP ALL)

**Purpose:** Understanding how to use and deploy the system

```
✅ EXECUTIVE_SUMMARY.txt                    - Project overview
✅ IDS_PIPELINE_GUIDE.md                    - How to use pipeline
✅ IDS_PIPELINE_SUMMARY.md                  - Quick reference
✅ PIPELINE_QUICK_FIX_REFERENCE.md          - Troubleshooting
✅ PIPELINE_FIXES_AND_TROUBLESHOOTING.md    - Detailed fixes
✅ SESSION_SUMMARY.md                       - Session notes
✅ QUICK_REFERENCE_CARD.md                  - Quick commands
✅ plan_files/*.md                          - Planning documents
```

---

## 🗑️ SAFE TO REMOVE/CLEAN

### Virtual Environment (Git ignored, not committed)
```
🗑️  venv/                  (811 MB) - Recreate with: python3 -m venv venv
```

**How to remove safely:**
```bash
rm -rf venv/
python3 -m venv venv            # Recreate when needed
source venv/bin/activate        # Activate when working
```

### Empty Directories
```
🗑️  controller/             (empty) - Contains nothing
```

### Log Files (Can regenerate)
```
🗑️  brain.log               (8 KB) - Can be deleted
```

### Pycache (Recreated when running)
```
🗑️  brain/__pycache__/      - Recreated when needed
🗑️  training/__pycache__/   - Recreated when needed
```

---

## 🔧 Cleanup Commands

### 1. Remove Virtual Environment (saves 811 MB!)
```bash
rm -rf venv/
```

### 2. Remove Empty Directory
```bash
rm -rf controller/
```

### 3. Clean Log Files
```bash
rm -f brain.log
rm -f *.log
```

### 4. Remove Python Cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### 5. Full Cleanup (all safe-to-remove items)
```bash
rm -rf venv/
rm -rf controller/
rm -f brain.log
rm -f *.log
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

**Result:** Saves ~820 MB!

---

## 📦 .gitignore Configuration

Create/update `.gitignore` to exclude large/system files:

```
# Virtual Environment
venv/
env/
.venv/

# Python Cache
__pycache__/
*.pyc
*.pyo
*.egg-info/
.pytest_cache/

# IDE
.vscode/
.idea/
.DS_Store

# Logs
*.log
brain.log

# OS files
Thumbs.db
.DS_Store
*~

# Optional: Exclude raw data if too large
# data/NSL-KDD.tar.gz

# Keep model files! (comment out if public repo)
# ids_*.pkl
```

---

## 📊 Size Comparison

### Current State
```
Total Size: ~1.2 GB

venv/                    811 MB  ← Can remove locally
data/                    216 MB  ← KEEP
training/                 71 MB  ← KEEP
brain/                     4 MB  ← KEEP
ids_model.pkl             70 MB  ← KEEP (trained model!)
dashboard/                96 KB  ← KEEP
plan_files/              348 KB  ← KEEP
docs/                     92 KB  ← KEEP
source code               80 KB  ← KEEP
```

### After Cleanup
```
Total Size: ~362 MB

Without venv:            ~362 MB  (can be recreated)
GitHub Size:             ~358 MB  (venv removed)
Portable Size:           ~358 MB  (easy to distribute)
```

---

## 🎯 Step-by-Step Cleanup

### Step 1: Review Current Size
```bash
du -sh ~
du -sh data/ brain/ ids_model.pkl training/
```

### Step 2: Remove venv (Biggest!)
```bash
rm -rf venv/
echo "Saved 811 MB!"
```

### Step 3: Clean Cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
```

### Step 4: Remove Empty Dirs
```bash
rm -rf controller/
rmdir empty_dirs 2>/dev/null
```

### Step 5: Update .gitignore
```bash
# Add exclusions (see template above)
git add .gitignore
git commit -m "Update .gitignore"
```

### Step 6: Push to GitHub
```bash
git push origin master
```

### Step 7: Recreate venv When Needed
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📋 Directory Organization Checklist

- [ ] Keep `ids_*.pkl` files (your trained model!)
- [ ] Keep `ids_pipeline.py` (training script)
- [ ] Keep `data/` folder with CSV files
- [ ] Keep `brain/` application code
- [ ] Keep `training/` scripts
- [ ] Keep all `.md` documentation files
- [ ] Keep `requirements.txt`
- [ ] Remove `venv/` (recreate when needed)
- [ ] Remove `controller/` (empty)
- [ ] Remove `*.log` files
- [ ] Update `.gitignore`
- [ ] Clean `__pycache__/` directories

---

## 🚀 Quick Git Setup

### Initialize if not done
```bash
cd /home/mahanth-s/sdnproject/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic
git init
git add .
git commit -m "Initial project setup"
```

### Add .gitignore
```bash
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
*.log
.vscode/
.DS_Store
controller/
EOF

git add .gitignore
git commit -m "Add .gitignore to exclude venv and cache files"
```

### Push to GitHub
```bash
git branch -M master
git remote add origin https://github.com/Mahanths/Major_pro.git
git push -u origin master
```

---

## 📌 Important Notes

### ⭐ Your Trained Model
- `ids_model.pkl` (70 MB) = Your trained RandomForest classifier
- **CRITICAL**: Don't delete!
- Can regenerate by running: `python3 ids_pipeline.py`

### 🔄 Virtual Environment
- Can safely delete locally
- Must recreate to run code
- Recreate with: `python3 -m venv venv`

### 📊 Data Files
- All 10 CSV files are needed for training
- Consider compressing if space limited
- Size: 216 MB (large but necessary)

### 📚 Documentation
- Keep all `.md` files
- Helps future developers understand system
- No storage penalty (small files)

---

## ✅ Final Project Structure After Cleanup

```
SDN-Based Adaptive Zero-Trust Security for East–West Traffic/
├── src/
│   ├── ids_pipeline.py              # Main training script
│   ├── test_runner.py               # Testing
│   ├── test_system.py
│   └── requirements.txt             # Dependencies
│
├── models/
│   ├── ids_model.pkl                # ⭐ Trained model
│   ├── ids_scaler.pkl
│   └── ids_label_encoder.pkl
│
├── data/                            # 10 CSV training files
│   └── *.csv
│
├── brain/                           # API and ML engine
│   ├── app.py
│   ├── *.py
│   └── requirements.txt
│
├── training/                        # Training utilities
│   ├── train_models.py
│   ├── pcap_to_csv.py
│   └── *.py
│
├── dashboard/                       # Web interface
│
├── docs/                            # Documentation
│   ├── IDS_PIPELINE_GUIDE.md
│   ├── *.md
│   └── plan_files/
│
├── .git/                            # Version control
├── .gitignore                       # Git ignore rules
├── README.md                        # Project overview
└── RUN_TESTS.sh                     # Test runner
```

**Size:** ~362 MB (without venv from ~1.2 GB)

---

## 🎓 Best Practices

✅ **DO:**
- Keep all `.pkl` model files
- Keep all `.csv` data files
- Keep all documentation (`.md`)
- Keep source code files (`.py`)
- Use `.gitignore` to exclude venv
- Commit regularly to GitHub
- Tag releases with version numbers

❌ **DON'T:**
- Delete `ids_model.pkl` (your trained model!)
- Push `venv/` to GitHub (huge!)
- Commit log files or cache
- Remove data files
- Delete documentation
- Keep empty directories

---

## 📞 Quick Reference

| Action | Command |
|--------|---------|
| Check disk usage | `du -sh *` |
| Remove venv | `rm -rf venv/` |
| Clean cache | `find . -name __pycache__ -type d -exec rm -rf {} +` |
| Recreate venv | `python3 -m venv venv` |
| Activate venv | `source venv/bin/activate` |
| Install deps | `pip install -r requirements.txt` |
| Run pipeline | `python3 ids_pipeline.py` |
| Commit changes | `git add . && git commit -m "message"` |
| Push to GitHub | `git push origin master` |

---

**Status:** Ready for cleanup and reorganization ✅
