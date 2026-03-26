# ⚡ Quick Testing Reference Card

**Print this and keep it handy!**

---

## 🚀 5-MINUTE QUICK START

### **Terminal 1 - Laptop A (Brain Server)**
```bash
cd /home/mahanth-s/sdnproject/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic
source venv/bin/activate
uvicorn brain.app:app --host 0.0.0.0 --port 8000 --reload
# Keep this running! Don't close it!
```

### **Terminal 2 - Laptop A (Get IP)**
```bash
hostname -I
# Copy this IP for Laptop B (example: 192.168.1.100)
```

### **Terminal 1 - Laptop B (Clone & Test)**
```bash
git clone https://github.com/Mahanths/Major_pro.git
cd Major_pro/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn pandas numpy scikit-learn xgboost requests
python3 test_runner.py
# Answer prompts: Laptop A IP, dataset path, sample count
```

---

## ✅ SETUP CHECKLIST

- [ ] Laptop A: Python 3.12 + venv
- [ ] Laptop B: Python 3.12 installed
- [ ] Both on same WiFi
- [ ] Laptop A API running on :8000
- [ ] Laptop B can ping Laptop A
- [ ] Test dataset available

---

## 📊 EXPECTED RESULTS

| Metric | Expected | Status |
|--------|----------|--------|
| **Accuracy** | > 95% | ✅ |
| **Precision** | > 95% | ✅ |
| **Recall** | > 95% | ✅ |
| **False Positive Rate** | < 1% | ✅ |
| **Avg Latency** | < 100ms | ✅ |

---

## ❌ COMMON FIXES

| Problem | Fix |
|---------|-----|
| "Connection refused" | Verify Laptop A IP, check if API running |
| "Accuracy too low" | Verify dataset has 8 features, check models loaded |
| "Timeout" | Use wired connection, check network |
| "File not found" | Verify dataset path, run from project root |

---

## 📋 TEST REPORT INTERPRETATION

```
✅ > 98%  accuracy  → Perfect, deploy immediately
✅ 95-98% accuracy  → Good, acceptable for production
⚠️  85-95% accuracy → OK, but investigate issues
❌ < 85%  accuracy  → Error, debug required
```

---

## 🔧 QUICK DEBUGGING

**Check if API is running:**
```bash
curl http://192.168.1.100:8000/health
```

**Check if models loaded:**
```bash
curl http://192.168.1.100:8000/status
```

**Test single prediction:**
```bash
python3 -c "
import requests
payload = {'features': [0.1]*8}
r = requests.post('http://192.168.1.100:8000/infer', json=payload)
print(r.json())
"
```

---

## 📂 FILE LOCATIONS

```
Brain API:          brain/app.py
Models:             brain/models/*.pkl
Test Script:        test_runner.py
Test Reports:       test_report_*.json
Documentation:      TWO_LAPTOP_TESTING_GUIDE.md
```

---

## 🎯 TEST PHASES

```
Phase 1: Health Check    (1 min)
Phase 2: Load Dataset    (2 min)
Phase 3: Run Tests       (15-45 min, depending on samples)
Phase 4: Calculate Metrics (1 min)
Phase 5: Save Report     (< 1 min)
```

---

## 💡 PRO TIPS

1. **Use wired connection** for stable testing
2. **Start with 1000 samples** for quick validation
3. **Keep API running** in separate terminal
4. **Save reports** for history tracking
5. **Test off-peak** hours for better WiFi

---

## 📞 NEED HELP?

1. Check **TWO_LAPTOP_TESTING_GUIDE.md** for detailed info
2. Review **Troubleshooting** section in guide
3. Check terminal output for error messages
4. Verify all tools installed: `pip list | grep -E "pandas|scikit|xgboost"`

---

**You got this! 🚀**
