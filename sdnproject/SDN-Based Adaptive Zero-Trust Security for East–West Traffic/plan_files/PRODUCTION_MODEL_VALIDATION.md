# PRODUCTION MODEL VALIDATION GUIDE
**Acceptance Criteria & Testing Before Live Deployment**

---

## 🎯 GOAL
Ensure trained models meet production requirements before connecting to SDN controller and enforcing policies on real network.

---

## VALIDATION MINDSET

**DO NOT deploy until:**
- ✅ Isolation Forest detects ≥95% of actual attacks with <5% false positives
- ✅ XGBoost classifies attacks with ≥90% accuracy
- ✅ System handles false positives gracefully (VERIFY policy, not immediate BLOCK)
- ✅ Latency is acceptable (<500ms end-to-end)
- ✅ Models work on flows they haven't seen before

**Why this matters:**
- False positive (block legitimate flow) = production outage
- False negative (miss real attack) = security breach
- Need balanced trade-off, not 100% of either

---

## STEP 1: LOAD & EVALUATE MODELS ON TEST SET

**You held out 20% of data; now test on it:**

```python
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_auc_score, roc_curve, precision_recall_curve,
    f1_score, accuracy_score
)
import matplotlib.pyplot as plt

# Load models
isolation_forest = joblib.load('brain/models/isolation_forest_model.pkl')
xgboost_model = joblib.load('brain/models/xgboost_model.pkl')
scaler = joblib.load('brain/models/feature_scaler.pkl')

# Load test set
X_test = np.load('data/training_data/X_test.npy')
y_test = np.load('data/training_data/y_test.npy')

print("=" * 70)
print("ISOLATION FOREST VALIDATION (Tier 1: Anomaly Detection)")
print("=" * 70)

# Tier 1: Anomaly Detection
# -1 = anomaly, 1 = normal (sklearn convention)
y_pred_if = isolation_forest.predict(X_test)
anomaly_pred = (y_pred_if == -1).astype(int)  # Convert to 0=normal, 1=anomaly

# For binary classification: assume attacks are anomalies
# But some normal traffic IS anomalous (large files, backups)
# So we need to measure detection of TRUE attacks

true_attacks = y_test == 1
detected_attacks = anomaly_pred == 1

# Calculate metrics
true_positives = np.sum((true_attacks) & (detected_attacks))
false_positives = np.sum((~true_attacks) & (detected_attacks))
false_negatives = np.sum((true_attacks) & (~detected_attacks))
true_negatives = np.sum((~true_attacks) & (~detected_attacks))

print(f"\nConfusion Matrix:")
print(f"  True Positives (attacks detected):   {true_positives:,}")
print(f"  False Positives (normal flagged):    {false_positives:,}")
print(f"  False Negatives (attacks missed):    {false_negatives:,}")
print(f"  True Negatives (normal passed):      {true_negatives:,}")

detection_rate = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
false_positive_rate = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0
precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

print(f"\n📊 METRICS:")
print(f"  Detection Rate (Sensitivity):     {detection_rate*100:.1f}%")
print(f"    ✅ PASS if >= 95%, ❌ FAIL if < 90%")
print(f"  False Positive Rate:              {false_positive_rate*100:.1f}%")
print(f"    ✅ PASS if <= 5%, ❌ FAIL if > 10%")
print(f"  Precision (of flagged flows):     {precision*100:.1f}%")
print(f"    ✅ PASS if >= 80%, means 80% of flags are real attacks")

# Decision
print(f"\n🎯 TIER 1 DECISION:")
if detection_rate >= 0.95 and false_positive_rate <= 0.05:
    print(f"  ✅ PASS - Ready for production")
elif detection_rate >= 0.90 and false_positive_rate <= 0.10:
    print(f"  ⚠️  CONDITIONAL - Acceptable but monitor FP rate")
else:
    print(f"  ❌ FAIL - Retrain or collect more data")

print("\n" + "=" * 70)
print("XGBOOST VALIDATION (Tier 2: Attack Classification)")
print("=" * 70)

# Tier 2: Attack Classification (only runs if Tier 1 says anomaly)
# Only evaluate on flows Tier 1 flagged as anomalies
anomaly_indices = np.where(anomaly_pred == 1)[0]

if len(anomaly_indices) > 0:
    X_anomalies = X_test[anomaly_indices]
    y_anomalies_true = y_test[anomaly_indices]
    
    y_pred_xgb = xgboost_model.predict(X_anomalies)
    y_pred_xgb_proba = xgboost_model.predict_proba(X_anomalies)[:, 1]
    
    # Calculate metrics on flagged flows
    accuracy = accuracy_score(y_anomalies_true, y_pred_xgb)
    f1 = f1_score(y_anomalies_true, y_pred_xgb)
    
    # Confusion matrix for class 2
    cm_xgb = confusion_matrix(y_anomalies_true, y_pred_xgb)
    
    print(f"\nConfusion Matrix (on anomalies detected by Tier 1):")
    print(f"  True Negatives (normal):          {cm_xgb[0,0]:,}")
    print(f"  False Positives (normal→attack):  {cm_xgb[0,1]:,}")
    print(f"  False Negatives (attack→normal):  {cm_xgb[1,0]:,}")
    print(f"  True Positives (attacks):         {cm_xgb[1,1]:,}")
    
    print(f"\n📊 METRICS:")
    print(f"  Accuracy:                 {accuracy*100:.1f}%")
    print(f"    ✅ PASS if >= 90%")
    print(f"  F1-Score:                 {f1:.3f}")
    print(f"    ✅ PASS if >= 0.85")
    
    # Classification report
    print(f"\n  Detailed Report:")
    print(classification_report(y_anomalies_true, y_pred_xgb, 
                               target_names=['Normal', 'Attack'],
                               digits=3))
    
    # Decision
    print(f"\n🎯 TIER 2 DECISION:")
    if accuracy >= 0.90 and f1 >= 0.85:
        print(f"  ✅ PASS - Classification is reliable")
    elif accuracy >= 0.85:
        print(f"  ⚠️  CONDITIONAL - Check with security team")
    else:
        print(f"  ❌ FAIL - Retrain with more balanced data")
else:
    print(f"\n⚠️  No anomalies detected by Tier 1 - cannot evaluate Tier 2")

```

---

## STEP 2: EVALUATE END-TO-END LATENCY

**Measure actual inference time on real flows:**

```python
import time
import numpy as np
from brain.feature_handler import FeatureHandler
from brain.hybrid_engine import HybridEngine
from brain.trust_calculator import TrustCalculator

# Initialize
feature_handler = FeatureHandler()
ml_engine = HybridEngine()
trust_calc = TrustCalculator()

# Load test telemetry (from actual network)
test_flows = [
    {
        "flow_id": f"flow_{i}",
        "fwd_packets": 50, "bwd_packets": 45,
        "flow_duration": 5.2,
        "packet_payload_bytes": 12000,
        "tcp_flags": ["SYN", "ACK", "FIN"],
        "src_port": 54321, "dst_port": 443,
    }
    for i in range(100)
]

latencies = []

print("=" * 70)
print("LATENCY TESTING (100 flows)")
print("=" * 70)

for flow in test_flows:
    start = time.time()
    
    # Step 1: Extract features (~5ms)
    features = feature_handler.extract_features(flow)
    
    # Step 2: ML inference (~15ms)
    tier1_anomaly, tier2_triggered, tier2_prob = ml_engine.infer(
        features, 
        {"src": flow.get('src_ip'), "dst": flow.get('dst_ip')}
    )
    
    # Step 3: Trust calculation (~5ms)
    trust = trust_calc.calculate_trust(
        flow['flow_id'],
        tier2_prob,
        tier1_anomaly,
        is_clean_traffic=(tier2_prob < 0.5)
    )
    
    end = time.time()
    latency_ms = (end - start) * 1000
    latencies.append(latency_ms)

latencies = np.array(latencies)

print(f"\nLatency Statistics:")
print(f"  Min:       {latencies.min():.1f} ms")
print(f"  Max:       {latencies.max():.1f} ms")
print(f"  Mean:      {latencies.mean():.1f} ms")
print(f"  Median:    {np.median(latencies):.1f} ms")
print(f"  P99:       {np.percentile(latencies, 99):.1f} ms")

print(f"\n🎯 LATENCY DECISION:")
if latencies.mean() < 100:  # < 100ms is excellent for ~15ms processing
    print(f"  ✅ PASS - Mean {latencies.mean():.1f}ms is acceptable")
elif latencies.mean() < 500:
    print(f"  ⚠️  CONDITIONAL - {latencies.mean():.1f}ms is marginal")
else:
    print(f"  ❌ FAIL - {latencies.mean():.1f}ms is too slow")
    print(f"     Action: Optimize feature extraction or use model caching")

```

---

## STEP 3: TEST ON COMPLETELY UNSEEN NETWORK (Cross-Validation)

**Ensure model generalizes, not just memorizes:**

```python
# If you have data from a DIFFERENT time period or network segment
X_holdout = np.load('data/training_data/X_holdout_new_segment.npy')
y_holdout = np.load('data/training_data/y_holdout_new_segment.npy')

print("=" * 70)
print("CROSS-VALIDATION ON UNSEEN DATA")
print("=" * 70)

# Tier 1 on holdout
y_pred_if_holdout = isolation_forest.predict(X_holdout)
anomaly_pred_holdout = (y_pred_if_holdout == -1).astype(int)

detection_rate_holdout = np.sum((y_holdout == 1) & (anomaly_pred_holdout == 1)) / np.sum(y_holdout == 1)
fpr_holdout = np.sum((y_holdout == 0) & (anomaly_pred_holdout == 1)) / np.sum(y_holdout == 0)

print(f"\nTier 1 on NEW data:")
print(f"  Detection Rate: {detection_rate_holdout*100:.1f}%")
print(f"  False Positive Rate: {fpr_holdout*100:.1f}%")

if detection_rate_holdout >= 0.90 and fpr_holdout <= 0.10:
    print(f"  ✅ Model generalizes well!")
else:
    print(f"  ⚠️  Performance degraded on new data - may need retraining")

# Tier 2 on holdout
anomaly_indices_holdout = np.where(anomaly_pred_holdout == 1)[0]
if len(anomaly_indices_holdout) > 0:
    X_anom_holdout = X_holdout[anomaly_indices_holdout]
    y_anom_holdout = y_holdout[anomaly_indices_holdout]
    
    y_pred_xgb_holdout = xgboost_model.predict(X_anom_holdout)
    acc_holdout = accuracy_score(y_anom_holdout, y_pred_xgb_holdout)
    
    print(f"\nTier 2 on NEW data:")
    print(f"  Accuracy: {acc_holdout*100:.1f}%")
    
    if acc_holdout >= 0.85:
        print(f"  ✅ Classification generalizes!")
    else:
        print(f"  ⚠️  Classification needs improvement on new patterns")

```

---

## STEP 4: SIMULATE PRODUCTION DEPLOYMENT

**Test how system behaves with real policy decisions:**

```python
import json
from datetime import datetime

print("=" * 70)
print("PRODUCTION SIMULATION")
print("=" * 70)

# Simulate 50 network flows (mix of normal + attack)
test_scenarios = [
    # Scenarios: (description, features, is_attack)
    ("Normal HTTPS", [5.0, 45, 40, 0.15, 1, 0, 0.01, 50], False),
    ("Normal DNS", [0.1, 10, 8, 0.05, 1, 0, 0.001, 100], False),
    ("SYN Flood", [0.002, 5000, 0, 0.01, 1, 50, 0.0001, 0.0005], True),
    ("Port Scan", [0.05, 100, 5, 0.1, 500, 20, 0.001, 50], True),
    ("Data Exfil", [120, 10, 500, 0.8, 1, 2, 1, 50], True),
    ("Large Download", [30, 100, 500, 0.2, 1, 0, 0.1, 50], False),
]

policy_decisions = []

for scenario, features, is_attack in test_scenarios:
    # Tier 1: Anomaly detection
    features_array = np.array(features).reshape(1, -1)
    tier1_pred = isolation_forest.predict(features_array)[0]
    tier1_anomaly = 1 if tier1_pred == -1 else 0
    
    if tier1_anomaly:
        # Tier 2: Classification
        tier2_prob = xgboost_model.predict_proba(features_array)[0, 1]
    else:
        tier2_prob = 0.0
    
    # Trust score
    trust = trust_calc.calculate_trust(
        flow_id=scenario,
        ml_malicious_probability=tier2_prob,
        ml_anomaly_score=tier1_anomaly,
        is_clean_traffic=(tier2_prob < 0.4)
    )
    
    # Policy decision
    trust_score = trust['trust_score']
    if trust_score >= 80:
        policy = "ALLOW"
    elif trust_score >= 60:
        policy = "VERIFY"
    elif trust_score >= 40:
        policy = "LIMIT"
    else:
        policy = "BLOCK"
    
    decision = {
        "scenario": scenario,
        "is_attack": is_attack,
        "tier1_anomaly": tier1_anomaly,
        "tier2_prob": f"{tier2_prob:.2f}",
        "trust_score": f"{trust_score:.1f}",
        "policy": policy,
        "correct": (policy == "BLOCK" if is_attack else policy in ["ALLOW", "VERIFY"])
    }
    
    policy_decisions.append(decision)

# Print results
print(f"\n{'Scenario':<20} {'Attack?':<8} {'T1':<3} {'T2':<6} {'Trust':<8} {'Policy':<8} {'Correct?':<8}")
print("-" * 80)

correct_decisions = 0
for d in policy_decisions:
    correct = "✅" if d['correct'] else "❌"
    print(f"{d['scenario']:<20} {str(d['is_attack']):<8} {d['tier1_anomaly']:<3} {d['tier2_prob']:<6} {d['trust_score']:<8} {d['policy']:<8} {correct:<8}")
    if d['correct']:
        correct_decisions += 1

accuracy = correct_decisions / len(policy_decisions)
print("-" * 80)
print(f"\n🎯 POLICY DECISION ACCURACY: {accuracy*100:.0f}% ({correct_decisions}/{len(policy_decisions)})")

if accuracy >= 0.95:
    print(f"  ✅ PASS - System making correct decisions")
elif accuracy >= 0.85:
    print(f"  ⚠️  CONDITIONAL - Review policy thresholds")
else:
    print(f"  ❌ FAIL - System not ready for production")

```

---

## STEP 5: FINAL ACCEPTANCE CHECKLIST

```
ISOLATION FOREST (TIER 1)
□ Detection Rate >= 95%
□ False Positive Rate <= 5%  
□ Precision >= 80%
□ Generalizes to unseen data

XGBOOST (TIER 2)
□ Accuracy >= 90%
□ F1-Score >= 0.85
□ Balanced performance on both classes
□ Generalizes to unseen data

LATENCY
□ Mean latency < 100ms
□ P99 latency < 500ms
□ No timeout errors

POLICY DECISIONS
□ Attacks correctly blocked (True Positive Rate >= 95%)
□ Normal traffic allowed (True Negative Rate >= 95%)
□ Edge cases handled gracefully
□ VERIFY policy catches uncertain flows

PRODUCTION READINESS
□ Models saved in brain/models/
□ API endpoints tested
□ Error handling verified
□ Logging configured
□ Monitoring dashboards ready
□ Rollback plan documented
```

---

## STEP 6: CONDITIONAL PASS CRITERIA

**If you don't meet strict criteria, conditional pass requires:**

1. **Detection Rate 90-94%?**
   - Increase monitoring/alerting sensitivity
   - Plan for weekly retraining with new data

2. **False Positive Rate 5-10%?**
   - Use VERIFY policy (not immediate BLOCK)
   - Let security team review VERIFY flags
   - Gradually increase threshold as confidence grows

3. **Tier 2 Accuracy 85-89%?**
   - Collect more labeled attack data
   - Increase feature engineering sophistication
   - Consider ensemble methods

4. **Latency 100-500ms?**
   - Still acceptable for policy enforcement
   - Monitor if it affects network throughput
   - Plan model optimization

---

## 🚀 DEPLOYMENT READINESS MATRIX

| Component | Requirement | Your Result | Status |
|-----------|-------------|-------------|--------|
| Tier 1 Detection | ≥95% | __% | __ |
| Tier 1 FPR | ≤5% | __% | __ |
| Tier 2 Accuracy | ≥90% | __% | __ |
| Latency | <100ms | __ms | __ |
| Generalization | >90% on holdout | __% | __ |
| Policy Correctness | >95% | __% | __ |

**Overall Status:** 
- ✅ **READY** - 6/6 requirements met
- ⚠️ **CONDITIONAL** - 5/6 requirements, proceed with caution
- ❌ **NOT READY** - <5/6 requirements, retrain required

---

## ⏭️ NEXT STEPS

**If READY or CONDITIONAL:**
1. Deploy models to FastAPI brain
2. Configure ONOS controller integration
3. Enable gradual traffic steering (1% → 5% → 100%)
4. Monitor false positive rate in production
5. Schedule weekly retraining on new data

**If NOT READY:**
1. Analyze where metrics are weak
2. Collect more/better training data
3. Retrain models
4. Repeat validation process
5. Do NOT deploy yet
