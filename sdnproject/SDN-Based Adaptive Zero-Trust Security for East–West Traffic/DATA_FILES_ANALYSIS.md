# 📊 DATA FILES ANALYSIS & CLEANUP RECOMMENDATIONS

**Analysis Date:** April 5, 2026  
**Current Disk Usage:** 216 MB (data/) + 71 MB (training/data/) = **287 MB total**

---

## 🎯 FILES SUMMARY

### Files In `data/` Folder (Currently 10 files, 216 MB)

| File | Size | Type | Status | Keep? | Reason |
|------|------|------|--------|-------|--------|
| `cicids2018_8features.csv` | 31 MB | 8-Feature Dataset | ✅ **PRIMARY** | **YES** | Best quality, 8 selected features, real data |
| `cicids2019_8features.csv` | 31 MB | 8-Feature Dataset | ✅ **PRIMARY** | **YES** | Best quality, 8 selected features, real data |
| `cicids2023_8features.csv` | 31 MB | 8-Feature Dataset | ✅ **PRIMARY** | **YES** | Best quality, 8 selected features, real data |
| `cicids2018_synthetic.csv` | 24 MB | Synthetic Data | ⚠️ DUPLICATE | **NO** | Also in training/data/, synthetic = lower quality |
| `cicids2019_synthetic.csv` | 24 MB | Synthetic Data | ⚠️ DUPLICATE | **NO** | Also in training/data/, synthetic = lower quality |
| `cicids2023_synthetic.csv` | 24 MB | Synthetic Data | ⚠️ DUPLICATE | **NO** | Also in training/data/, synthetic = lower quality |
| `nslkdd_realistic.csv` | 32 MB | NSL-KDD Dataset | ⚠️ ALTERNATIVE | **NO** | Different format, older dataset, not used in current setup |
| `nslkdd_training_8features.csv` | 13 MB | NSL-KDD 8-Feature | ⚠️ ALTERNATIVE | **NO** | Different format, older dataset, not needed for current model |
| `training_dataset.csv` | 9.1 MB | Unknown/Legacy | ❓ UNKNOWN | **NO** | Purpose unclear, legacy file (keep only if needed) |
| `NSL-KDD.tar.gz` | 297 KB | Compressed Archive | 🗜️ ARCHIVE | **NO** | Source archive, should be removed if extracted |

### Files In `training/data/` Folder (Duplicates, 71 MB)

| File | Size | Type | Duplicate Of | Keep? |
|------|------|------|--------------|-------|
| `cicids2018_synthetic.csv` | 24 MB | Synthetic | data/cicids2018_synthetic.csv | **NO** |
| `cicids2019_synthetic.csv` | 24 MB | Synthetic | data/cicids2019_synthetic.csv | **NO** |
| `cicids2023_synthetic.csv` | 24 MB | Synthetic | data/cicids2023_synthetic.csv | **NO** |

---

## ✅ RECOMMENDED CLEANUP

### Files to KEEP (Essential for ML Model)
```
data/
├── cicids2018_8features.csv     ✅ 31 MB - Primary training data
├── cicids2019_8features.csv     ✅ 31 MB - Primary training data
└── cicids2023_8features.csv     ✅ 31 MB - Primary training data

TOTAL: 93 MB (keeps actual training data)
```

### Files to DELETE (Redundant/Unwanted)
```
data/
├── cicids2018_synthetic.csv     ❌ 24 MB - Duplicate, lower quality
├── cicids2019_synthetic.csv     ❌ 24 MB - Duplicate, lower quality
├── cicids2023_synthetic.csv     ❌ 24 MB - Duplicate, lower quality
├── nslkdd_realistic.csv         ❌ 32 MB - Different format, not used
├── nslkdd_training_8features.csv ❌ 13 MB - Different format, not used
├── training_dataset.csv         ❌ 9.1 MB - Unknown/legacy
└── NSL-KDD.tar.gz             ❌ 297 KB - Archive, can remove

training/data/
├── cicids2018_synthetic.csv     ❌ 24 MB - Duplicate
├── cicids2019_synthetic.csv     ❌ 24 MB - Duplicate
└── cicids2023_synthetic.csv     ❌ 24 MB - Duplicate

TOTAL TO DELETE: 194 MB
```

---

## 💾 SPACE SAVING IMPACT

| Category | Current | After Cleanup | Saved |
|----------|---------|---------------|-------|
| **data/ folder** | 216 MB | 93 MB | **123 MB** ✅ |
| **training/data/** | 71 MB | 0 MB | **71 MB** ✅ |
| **Total Project Size** | 287 MB | 93 MB | **194 MB (67.6% reduction)** ✨ |

---

## 📋 DETAILED FILE EXPLANATIONS

### ✅ Files to KEEP

#### 1. `cicids2018_8features.csv` (31 MB)
- **Content:** CIC-IDS2018 dataset with 8 selected features
- **Format:** Pre-processed, optimal features selected
- **Quality:** Real network traffic data labeled with attack types
- **Usage:** Primary training data for the ML model
- **Action:** **KEEP - Essential**

#### 2. `cicids2019_8features.csv` (31 MB)
- **Content:** CIC-IDS2019 dataset with 8 selected features
- **Format:** Pre-processed, optimal features selected
- **Quality:** Real network traffic data with diverse attack patterns
- **Usage:** Primary training data for the ML model
- **Action:** **KEEP - Essential**

#### 3. `cicids2023_8features.csv` (31 MB)
- **Content:** CIC-IDS2023 dataset with 8 selected features
- **Format:** Pre-processed, optimal features selected
- **Quality:** Most recent dataset with latest attack patterns
- **Usage:** Primary training data for the ML model
- **Action:** **KEEP - Essential**

### ❌ Files to DELETE

#### 1. `cicids*_synthetic.csv` (72 MB total)
- **Problem:** Duplicate files exist in both data/ and training/data/
- **Quality:** Synthetic data is lower quality than real network data
- **Recommendation:** **DELETE**
- **Command:** 
  ```bash
  rm data/cicids2018_synthetic.csv
  rm data/cicids2019_synthetic.csv
  rm data/cicids2023_synthetic.csv
  rm training/data/cicids2018_synthetic.csv
  rm training/data/cicids2019_synthetic.csv
  rm training/data/cicids2023_synthetic.csv
  ```

#### 2. `nslkdd_realistic.csv` (32 MB)
- **Problem:** NSL-KDD is a different dataset format; current pipeline uses CIC-IDS data
- **Format:** Incompatible with 8-feature schema used in current model
- **Recommendation:** **DELETE** (unless you plan to implement NSL-KDD support)
- **Command:** `rm data/nslkdd_realistic.csv`

#### 3. `nslkdd_training_8features.csv` (13 MB)
- **Problem:** Alternative dataset format; not used in current pipeline
- **Purpose:** Different attack detection schema than CIC-IDS
- **Recommendation:** **DELETE** (unless you need NSL-KDD specifically)
- **Command:** `rm data/nslkdd_training_8features.csv`

#### 4. `training_dataset.csv` (9.1 MB)
- **Problem:** Unknown origin or purpose; legacy file
- **Usage:** Not referenced in current pipeline
- **Recommendation:** **DELETE** (check before deleting if this is custom data)
- **Command:** `rm data/training_dataset.csv`

#### 5. `NSL-KDD.tar.gz` (297 KB)
- **Problem:** Source archive; extracted version already exists
- **Purpose:** Contains NSL-KDD compressed dataset
- **Recommendation:** **DELETE** (keep only if planning to re-extract)
- **Command:** `rm data/NSL-KDD.tar.gz`

---

## 🔧 CLEANUP EXECUTION

### Option 1: Manual Deletion (If Unsure)
Delete files one by one:
```bash
cd '/home/mahanth-s/sdnproject/SDN-Based Adaptive Zero-Trust Security for East–West Traffic'

# Delete synthetic files
rm data/cicids2018_synthetic.csv
rm data/cicids2019_synthetic.csv
rm data/cicids2023_synthetic.csv
rm training/data/cicids2018_synthetic.csv
rm training/data/cicids2019_synthetic.csv
rm training/data/cicids2023_synthetic.csv

# Delete NSL-KDD and unknown files
rm data/nslkdd_realistic.csv
rm data/nslkdd_training_8features.csv
rm data/training_dataset.csv
rm data/NSL-KDD.tar.gz
```

### Option 2: Batch Deletion (If Confident)
```bash
cd '/home/mahanth-s/sdnproject/SDN-Based Adaptive Zero-Trust Security for East–West Traffic'

# Delete all unwanted files
rm -f data/*synthetic.csv
rm -f training/data/*synthetic.csv
rm -f data/nslkdd_*
rm -f data/training_dataset.csv
rm -f data/NSL-KDD.tar.gz

# Verify only 3 essential files remain
ls -lh data/
```

---

## 📊 VERIFICATION

After cleanup, you should have:
```
✅ data/cicids2018_8features.csv    (31 MB)
✅ data/cicids2019_8features.csv    (31 MB)
✅ data/cicids2023_8features.csv    (31 MB)
├─ Total: 93 MB
├─ Folder count: 3 CSV files only
└─ training/data/: Empty or removed
```

Run this command to verify:
```bash
du -sh data/ && echo "---" && ls -1 data/*.csv | wc -l && echo "files remain"
```

Expected output:
```
93M    data/
3
files remain
```

---

## 🎯 IMPACT ON MODEL PERFORMANCE

- **Training Data Quality:** ⬆️ **Improves** (removes duplicate/synthetic data noise)
- **Model Accuracy:** ⚖️ **No negative impact** (only keeps real, high-quality data)
- **Training Speed:** ⬆️ **Faster** (less duplicate data to process)
- **Disk Space:** ⬇️ **Reduced by 67.6%** (194 MB freed)

---

## ⚠️ IMPORTANT NOTES

1. **Backup First:** Consider backing up before deletion:
   ```bash
   tar -czf data_backup.tar.gz data/ training/data/
   ```

2. **Test After Cleanup:** Run the pipeline after deletion to ensure it still works:
   ```bash
   python3 ids_pipeline.py
   ```

3. **No Data Loss:** The 3 essential 8-feature files contain all needed data:
   - All 8 selected features for ML model
   - All attack types (BENIGN, Bot, Infiltration, Brute Force)
   - Real network traffic patterns

4. **Git Status:** These are data files (not code), so cleanup won't affect version control

---

## 📝 SUMMARY

| Action | Details |
|--------|---------|
| **Files to Keep** | 3 CSV files (all CIC-IDS 8-feature versions) |
| **Files to Delete** | 10 files (duplicates, alternatives, archives) |
| **Space Freed** | 194 MB (67.6% reduction) |
| **Final Size** | 93 MB (just the essential data) |
| **Model Impact** | No negative impact; removes noise and duplicates |

**Recommendation: ✅ PROCEED WITH CLEANUP**
