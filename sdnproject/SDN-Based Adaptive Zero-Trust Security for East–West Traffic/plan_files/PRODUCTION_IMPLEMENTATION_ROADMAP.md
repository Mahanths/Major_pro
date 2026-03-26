# PRODUCTION IMPLEMENTATION ROADMAP
**Complete Path from Training to Live Deployment**

---

## 🎯 ROADMAP OVERVIEW

```
PHASE 1: DATA COLLECTION        (Week 1-2)
   ↓ Deploy network monitoring
   ↓ Collect 7-14 days real traffic baseline
   ↓ Collect known attack samples
   
PHASE 2: MODEL TRAINING          (Week 3-4)
   ↓ Extract features from real PCAPs  
   ↓ Train Isolation Forest + XGBoost
   ↓ Validate accuracy >= 95%
   
PHASE 3: STAGED DEPLOYMENT       (Week 5-8)
   ↓ Deploy FastAPI brain (test environment)
   ↓ Deploy telemetry collection (1% sample)
   ↓ Deploy ONOS controller
   ↓ Test policy enforcement (1% traffic)
   ↓ Increase to 10%, then 100%
   
PHASE 4: PRODUCTION HARDENING    (Week 9+)
   ↓ Continuous monitoring
   ↓ Weekly model retraining
   ↓ Incident response automation
   ↓ Scale to full network
```

---

## PHASE 1: DATA COLLECTION (Weeks 1-2)

### Week 1: Deploy PCAP Collection

**Monday - Day 1:**
```bash
# 1. Deploy tcpdump on network edge
sudo tcpdump -i eth0 -w /data/pcaps/baseline_%Y-%m-%d_%H-%M-%S.pcap \
  -G 3600 -C 500 'tcp or udp' &

# 2. Deploy Zeek IDS as backup
sudo /opt/zeek/bin/zeekctl start

# 3. Verify collection is happening
ls -lh /data/pcaps/ | wc -l  # Should grow hourly

# 4. Set calendar reminder: Collect until next Friday
```

**Friday - Day 5:**
- Verify 5 days of continuous capture
- Check disk space (need ~150GB for week)
- Verify no collection gaps

### Week 2: Collect Attack Samples

**Monday - Day 8:**
```bash
# Option 1: Download public attacks
wget https://www.unb.ca/cic/datasets/cicids2018.html
# Extract required PCAPs

# Option 2: Request from security team
# "Provide PCAPs of any IDS/firewall blocks from last 30 days"

# Option 3: Lab testing (with permission)
# Run controlled attacks with network isolated
```

**Friday - Day 14:**
- [ ] 7-14 days baseline traffic collected
- [ ] Known attack samples acquired
- [ ] Total size: ~200-400 GB
- [ ] Ready for feature extraction

---

## PHASE 2: MODEL TRAINING (Weeks 3-4)

### Week 3: Feature Extraction

**Monday - Day 15:**
```bash
# Extract features from baseline
for f in /data/pcaps/weekday_*.pcap; do
    python training/pcap_to_csv.py \
      -i "$f" \
      -o "/data/training/features/$(basename $f .pcap)_features.csv" \
      -l 0  # Label 0 = normal
done

echo "✅ Baseline extraction complete"
```

**Wednesday - Day 17:**
```bash
# Extract features from attacks
for f in /data/pcaps/attacks/*.pcap; do
    python training/pcap_to_csv.py \
      -i "$f" \
      -o "/data/training/features/$(basename $f .pcap)_attack_features.csv" \
      -l 1  # Label 1 = malicious
done

echo "✅ Attack extraction complete"
```

**Friday - Day 19:**
```bash
# Merge all CSVs into single training set
python -c "
import pandas as pd
import glob

csv_files = glob.glob('/data/training/features/*.csv')
dfs = [pd.read_csv(f) for f in csv_files]
combined = pd.concat(dfs, ignore_index=True)
combined = combined.sample(frac=1).reset_index(drop=True)
combined.to_csv('/data/training_data/final_training_set.csv', index=False)
print(f'✅ Created training set: {len(combined)} flows')
"
```

### Week 4: Model Training & Validation

**Monday - Day 22:**
```bash
# Split data: 80% train, 20% test
python training/train_models.py \
  -d /data/training_data/final_training_set.csv \
  --epochs 50 \
  --output-dir brain/models/

# This creates:
# - isolation_forest_model.pkl
# - xgboost_model.pkl
# - feature_scaler.pkl
```

**Wednesday - Day 24:**
```bash
# Validate model accuracy
python plan_files/validate_models.py \
  --model-dir brain/models/ \
  --test-set /data/training_data/test_set.csv

# Expected output:
# Isolation Forest Detection Rate: 96.2%
# False Positive Rate: 3.1%
# XGBoost Accuracy: 93.5%
```

**Friday - Day 26:**
```bash
# Decision: Ready for deployment?
# ✅ IF: Detection >= 95%, FPR <= 5%, XGB >= 90%
#        Proceed to Phase 3
# ⚠️ IF: 90-94% detection or > 5% FPR
#        Proceed with VERIFY policy, plan retraining
# ❌ IF: < 90% detection or > 10% FPR
#        Collect more data, loop back to Week 3
```

---

## PHASE 3: STAGED DEPLOYMENT (Weeks 5-8)

### Week 5: Test Environment Setup

**Monday - Day 29:**
```bash
# 1. Deploy FastAPI brain
cd /home/mahanth-s/sdnproject/SDN-Based\ Adaptive\ Zero-Trust\ Security\ for\ East–West\ Traffic
python -m uvicorn brain.app:app --host 0.0.0.0 --port 8000 --workers 4

# 2. Verify it's running
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 3. Deploy Zeek telemetry collection
sudo /opt/zeek/bin/zeekctl start

# 4. Test end-to-end single flow
curl -X POST http://localhost:8000/infer \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "10.0.1.100:54321-10.0.2.50:443-TCP",
    "src_ip": "10.0.1.100",
    "dst_ip": "10.0.2.50",
    "fwd_packets": 50,
    "bwd_packets": 45,
    "flow_duration": 5.2,
    "packet_payload_bytes": 12000,
    "tcp_flags": ["SYN", "ACK", "FIN"]
  }'
```

**Wednesday - Day 31:**
```bash
# Deploy ONOS controller
cd onos-2.7.1
./bin/onos-service start

# Activate required apps
./bin/onos onos_ip
onos> app activate org.onosproject.openflow

# Verify device connected
onos> devices
# Expected: device:1 connected

# Connect to OVS (if using)
ovs-vsctl show
sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6653
```

**Friday - Day 33:**
- [ ] FastAPI responding to telemetry
- [ ] Models loaded and inferring
- [ ] ONOS connected to switch
- [ ] OpenFlow app activated
- [ ] Can create test intents

### Week 6: 1% Traffic Test

**Monday - Day 36:**
```bash
# Configure telemetry to sample 1% of traffic
# In Zeek config or tshark filter:
# sampling_ratio=0.01

# Start collecting telemetry
python brain/telemetry_consumer.py \
  --zeek-log /opt/zeek/logs/current/conn.log \
  --destination http://localhost:8000/infer \
  --batch-size 100 \
  --interval 1s

# This sends ~10-100 flows per second (depending on network)
```

**Wednesday - Day 38:**
```bash
# Monitor initial decisions
tail -f brain/logs/decisions.log | head -100

# Should see output like:
# 2025-01-22 10:30:45 | ALLOW | trust=92.5 | 10.0.1.5:443 → 10.0.2.100:443
# 2025-01-22 10:30:46 | ALLOW | trust=88.2 | 10.0.1.10:80 → 10.0.2.50:8080
```

**Friday - Day 40:**
- [ ] 1% of traffic processed (0 errors)
- [ ] Policies mostly ALLOW (normal)
- [ ] <1 false positive per hour
- [ ] Decision latency <100ms
- [ ] Ready to increase to 10%

### Week 7: 10% Traffic Test

**Monday - Day 43:**
```bash
# Increase sampling to 10%
# In telemetry config:
# sampling_ratio=0.10

# Deploy policy enforcement to ONOS
# Edit brain/app.py to activate ONOS enforcer
# When policy != ALLOW, create ONOS intent
```

**Wednesday - Day 45:**
```bash
# Monitor for false positives
grep "BLOCK" brain/logs/decisions.log | wc -l
# Expected: 0-5 blocks per hour (on 10% traffic)

# Check for user complaints
# (No support tickets about "connection rejected"?)
```

**Friday - Day 47:**
- [ ] 10% of traffic processed
- [ ] <1 false positive per 100 flows
- [ ] ONOS enforcement working
- [ ] Network performance normal
- [ ] Ready for 100%

### Week 8: Full Production Deployment

**Monday - Day 50:**
```bash
# Increase to 100% (remove sampling)
# In telemetry config:
# sampling_ratio=1.0

# Scale FastAPI workers if needed
python -m uvicorn brain.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker

# Expected load: If 5,000 flows/sec
# Need: 5,000 / 500 = 10 workers
```

**Wednesday - Day 52:**
```bash
# Monitor all metrics
# - Decision latency (target <100ms)
# - False positive rate (target <1%)
# - Model accuracy (should stay >90%)
# - CPU/memory usage
# - Network impact

python plan_files/monitor_production.py \
  --interval 60 \
  --alert-threshold-latency 200 \
  --alert-threshold-fpr 0.05
```

**Friday - Day 54:**
- [ ] 100% traffic processed
- [ ] All SLAs met (latency, accuracy, FPR)
- [ ] No known false positives
- [ ] ONOS policies enforcing correctly
- [ ] Incidents: 0
- [ ] **Production deployment COMPLETE** ✅

---

## PHASE 4: PRODUCTION HARDENING (Week 9+)

### Ongoing Tasks

**Daily (Automated):**
```bash
# Monitor dashboards
# Check: latency, accuracy, false positive rate
# If any metric degrades: Alert ops team
```

**Weekly (Manual):**
```bash
# Retrain models on last 7 days of data
# Verify accuracy hasn't degraded
# Update models in production (canary 1%, then 100%)
```

**Monthly (Scheduled):**
```bash
# Analyze new attack patterns
# Collect new malicious traffic samples
# Retrain with fresh data
# Validate on test environment before production push
```

---

## DEPLOYMENT VERIFICATION CHECKLIST

### Before Phase 3 (Test Environment)

**Data Collection:**
- [ ] 7+ days baseline traffic collected
- [ ] Attack samples acquired (10K+ malicious flows)
- [ ] Features extracted from 100K+ flows
- [ ] No NaN or invalid values in training set

**Model Quality:**
- [ ] Isolation Forest: Detection >= 95%, FPR <= 5%
- [ ] XGBoost: Accuracy >= 90%, F1-Score >= 0.85
- [ ] Tested on completely unseen data (>90% accuracy)

**Code Quality:**
- [ ] brain/app.py compiles without errors
- [ ] All endpoints tested and responding
- [ ] Error handling for edge cases
- [ ] Logging configured
- [ ] Docker image built (optional but recommended)

### Before Phase 5 (Production 100%)

**System Performance:**
- [ ] Latency <100ms per request (99th percentile)
- [ ] Throughput >500 requests/sec (single process)
- [ ] Memory usage <2GB for normal load
- [ ] CPU usage <80% at peak load

**Integration Testing:**
- [ ] FastAPI receives telemetry from Zeek
- [ ] Policy decisions sent to ONOS successfully
- [ ] ONOS creates intents without errors
- [ ] Switch enforces DROP/LIMIT policies
- [ ] Normal traffic not blocked
- [ ] Attack traffic is blocked

**Operational Readiness:**
- [ ] Monitoring dashboard deployed
- [ ] Alerting configured (latency, accuracy, FPR)
- [ ] Log aggregation centralized (ELK/Splunk)
- [ ] Incident response runbook created
- [ ] Rollback procedure documented
- [ ] Team trained on operation

---

## CRITICAL DECISION POINTS

### Decision 1: Week 4 - Model Quality
```
IF Detection >= 95% AND FPR <= 5% AND Accuracy >= 90%
  → Proceed to Phase 3 (Test)
  
ELSE IF Detection >= 90% AND FPR <= 10%
  → Proceed but with VERIFY policy
  → Plan retraining for Week 8
  
ELSE
  → Collect more data (2 more weeks)
  → Loop back to Week 3
```

### Decision 2: Week 6 - System Stability
```
IF No crashes AND <1 false positive/hour AND latency <100ms
  → Proceed to 10%
  
ELSE IF latency >500ms
  → Optimize code or add workers
  
ELSE IF false positive rate >5%
  → Adjust policy thresholds
  → Collect more training data
```

### Decision 3: Week 8 - Production Ready
```
IF FPR <1% AND latency <100ms AND accuracy >90%
  → Full production deployment approved
  
ELSE
  → Extend to Week 10 with monitoring
  → Plan corrective actions
```

---

## KEY SUCCESS METRICS

| Metric | Target | Week 4 | Week 6 | Week 8 | Week 12 |
|--------|--------|--------|--------|--------|----------|
| Detection Rate | >= 95% | __% | __% | __% | __% |
| False Positive Rate | <= 1% | __% | __% | __% | __% |
| Inference Latency | <100ms | __ms | __ms | __ms | __ms |
| Throughput | >500/sec | __/s | __/s | __/s | __/s |
| Uptime | >= 99.9% | - | - | __% | __% |
| Attack Detection | Real-time | <1s | <500ms | <500ms | <500ms |

---

## RESOURCE REQUIREMENTS

### Compute Resources

```
Development Phase (Weeks 1-4):
  - 1 CPU core
  - 8 GB RAM
  - 500 GB disk (for PCAPs)
  - Network access to capture interface

Test Phase (Weeks 5-7):
  - 2-4 CPU cores
  - 16 GB RAM
  - 200 GB disk
  - Network access to monitoring

Production Phase (Week 8+):
  - 8+ CPU cores (scale based on flow volume)
  - 32+ GB RAM
  - 1 TB disk (for logs, models, backups)
  - High-bandwidth network connection
  - GPU optional (10x speedup)
```

### Network Resources

```
PCAP Collection:
  - ~20GB per 24 hours
  - ~600GB per month
  - Recommend: 2TB storage minimum for 3 months

ONOS Controller:
  - 1 Gigabit connection to switches
  - <5ms latency to switch management interface
  - Redundant connectivity for HA

FastAPI Brain:
  - 1 Gigabit connection to telemetry sources
  - <10ms latency to Zeek/tshark
  - Redundant for high availability
```

---

## ROLLBACK PROCEDURE

If something breaks in production:

```bash
# Immediate (< 5 minutes)
# 1. Stop FastAPI (allows normal forwarding)
systemctl stop fastapi-brain

# 2. Clear ONOS intents (remove all policies)
./onos
onos> intents -p
onos> intents -p | grep "drop"  # Get drop intent IDs
onos> remove-intent org.onosproject.security.zerotrust drop-1
onos> remove-intent org.onosproject.security.zerotrust drop-2
# Repeat for all intents

# 3. Verify network is flowing normally
ping 10.0.0.1  # Should work now
curl http://example.com  # Should work

# 4. Investigation phase (hours)
tail -f brain/logs/errors.log
ps aux | grep onos
systemctl status fastapi-brain
```

---

## POST-DEPLOYMENT (Week 9+)

### Daily
- [ ] Check dashboards for anomalies
- [ ] Review false positive alerts
- [ ] Verify detection latency <500ms
- [ ] Check CPU/memory usage normal

### Weekly
- [ ] Retrain models on new data
- [ ] Deploy updated models to canary (1%)
- [ ] Validate accuracy unchanged
- [ ] Deploy to production (100%)

### Monthly
- [ ] Full audit of blocked flows
- [ ] Review attack detection accuracy
- [ ] Update threat intelligence
- [ ] Plan next quarter improvements

### Quarterly
- [ ] Performance optimization review
- [ ] Security posture assessment
- [ ] Team training update
- [ ] Incident retrospectives

---

## 📞 SUPPORT CONTACTS

If something goes wrong:

```
FastAPI Issues:
  - Check: /home/.../brain/logs/app.log
  - Restart: systemctl restart fastapi-brain
  - Contact: ML/Backend team

ONOS Issues:
  - Check: onos-2.7.1/karaf.log
  - Restart: ./bin/onos-service restart
  - Contact: Network/SDN team

Network Issues:
  - Check: tcpdump/tshark logs
  - Restart: systemctl restart telemetry-collector
  - Contact: Network ops team

Escalation:
  - Critical: Page on-call engineer
  - High: Create ticket, 1 hour response
  - Medium: Email, 4 hour response
  - Low: Backlog, next sprint
```

---

## 🚀 YOU'RE READY!

This roadmap takes you from:
- **Week 1:** Raw network traffic
- **Week 4:** Trained ML models
- **Week 8:** Production deployment
- **Week 12:** Fully operational zero-trust system

Total time: ~3 months to production-ready system that detects and blocks attacks on East-West traffic in real-time.

**Next step:** Start Phase 1 on Monday!
