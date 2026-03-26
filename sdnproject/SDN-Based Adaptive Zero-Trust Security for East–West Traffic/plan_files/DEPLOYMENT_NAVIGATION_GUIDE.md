# REAL-WORLD DEPLOYMENT NAVIGATION GUIDE
**Your Complete Path from Synthetic to Production**

---

## 🎯 YOU ARE HERE

You discovered that **synthetic training data won't work for production**. 

The models trained on random packets will only achieve 50-60% accuracy on your REAL network, which is not acceptable for security.

---

## THE PIPELINE

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR NETWORK (Real Traffic)                  │
└────────────────────────────┬──────────────────────────────────┘
                             ↓
                   ┌──────────────────┐
                   │  PCAP Collection │ ← START HERE
                   │   (tcpdump/Zeek) │
                   └──────────┬───────┘
                              ↓
                ┌──────────────────────────────┐
                │  Feature Extraction from     │
                │  Real PCAPs                  │
                └──────────────┬───────────────┘
                               ↓
              ┌─────────────────────────────────────┐
              │  Model Training on REAL Baseline +  │
              │  Known Attacks                      │
              └──────────────┬──────────────────────┘
                             ↓
            ┌──────────────────────────────────────┐
            │  Production Model Validation         │
            │  (Must pass: Detection>=95%, FPR<=5%)│
            └──────────────┬───────────────────────┘
                           ↓
         ┌─────────────────────────────────────────────┐
         │  Live Telemetry Source Setup                │
         │  (Zeek/tshark feeding FastAPI)             │
         └──────────────┬────────────────────────────┘
                        ↓
      ┌──────────────────────────────────────────────────┐
      │  ONOS Policy Enforcement                         │
      │  (FastAPI → ONOS → Actual Network Control)      │
      └──────────────┬───────────────────────────────────┘
                     ↓
         ┌──────────────────────────────────────────┐
         │  Staged Deployment (1% → 10% → 100%)    │
         │  (Monitor at each stage)                 │
         └──────────────┬─────────────────────────┘
                        ↓
          ┌─────────────────────────────────────┐
          │  PRODUCTION: Live Zero-Trust System │
          │  (Detecting & Blocking Attacks)     │
          └─────────────────────────────────────┘
```

---

## GUIDE SELECTION MATRIX

Use this to know which guide to read next:

| Current Status | Next Step | Read This Guide |
|---|---|---|
| Just finished synthetic testing | Start collecting real data | **PCAP_COLLECTION_GUIDE.md** |
| Have .pcap files | Convert them to ML features | **FEATURE_EXTRACTION_GUIDE.md** |
| Trained models | Verify they work on real data | **PRODUCTION_MODEL_VALIDATION.md** |
| Models are validated ✅ | Set up live telemetry pipeline | **LIVE_TELEMETRY_SOURCE.md** |
| FastAPI receiving live flows | Connect policy decisions to network | **ONOS_POLICY_ENFORCEMENT.md** |
| Everything configured | Execute deployment plan | **PRODUCTION_IMPLEMENTATION_ROADMAP.md** |

---

## DETAILED GUIDE DESCRIPTIONS

### 1. PCAP_COLLECTION_GUIDE.md
**What:** How to capture real network traffic for training

**When:** Week 1-2 (immediately after understanding synthetic data won't work)

**Contains:**
- 5 different capture methods (tcpdump, Zeek, OVS, etc.)
- Step-by-step setup for YOUR network interface
- How to organize captures (weekday/weekend, daytime/afterhours)
- How to collect attack samples
- Timeline: 7-14 days of continuous capture
- Expected storage: 200-400 GB

**Output:** Real .pcap files representing YOUR network's normal + attack traffic

**Key Takeaway:**
```
Synthetic data: Generic patterns → 50-60% accuracy on your network
Real data: YOUR network's actual patterns → 95%+ accuracy
```

---

### 2. FEATURE_EXTRACTION_GUIDE.md
**What:** Convert .pcap files to the 8-feature ML vectors

**When:** Week 3 (after collecting PCAPs)

**Contains:**
- Explanation of all 8 features (flow_duration, packet rates, entropy, etc.)
- How to use pcap_to_csv.py on your real files
- Feature quality checks (NaN detection, outlier identification)
- How to merge all CSVs into one training set
- Edge case handling (fragmented packets, timeouts, etc.)
- How to normalize and split for training
- Expected output: 500K - 1M feature vectors

**Output:** CSV files ready for model training

**Key Functions:**
```
extract_flow_duration()      # Time from first to last packet
extract_packet_rates()       # Packets per second in each direction
extract_byte_entropy()       # Randomness of payload
extract_tcp_flags()          # Anomaly detection via flag count
extract_inter_arrival_times()# Burst characterization
```

---

### 3. PRODUCTION_MODEL_VALIDATION.md
**What:** Acceptance criteria before deployment

**When:** Week 4 (after training on real data)

**Contains:**
- How to test Isolation Forest on test set (95%+ detection required)
- How to test XGBoost classification accuracy (90%+ required)
- False positive rate calculation (<5% acceptable)
- Latency testing (<100ms required)
- Cross-validation on completely unseen data
- Policy decision simulation
- Complete deployment checklist

**Output:** Approval/rejection for production deployment

**Critical Decision:**
```
PASS: All metrics >= target
  → Proceed to production deployment

CONDITIONAL: 90-94% detection or 5-10% FPR
  → Use VERIFY policy, plan retraining

FAIL: <90% detection or >10% FPR
  → Collect more data, retrain
```

---

### 4. LIVE_TELEMETRY_SOURCE.md
**What:** Where to get real-time network flows for the brain

**When:** Week 5 (after validating models)

**Contains:**
- 5 different telemetry sources (Zeek, tshark, OVS, Kafka, FastAPI)
- How to convert Zeek conn.log to JSON telemetry
- How to use tshark for real-time capture
- How to query OVS statistics
- Kafka streaming for high-volume networks
- FastAPI telemetry batch endpoint
- Expected telemetry volume/storage requirements
- Sizing recommendations (workers needed for your flow volume)

**Output:** Live JSON telemetry feeding into FastAPI brain

**Key Architecture:**
```
Zeek IDS → conn.log → Parser → JSON → POST /infer → FastAPI ML → Policy
```

---

### 5. ONOS_POLICY_ENFORCEMENT.md
**What:** Connect FastAPI policy decisions to actual network control

**When:** Week 5-6 (during deployment testing)

**Contains:**
- How to install & configure ONOS
- How to create ONOS intents programmatically
- Python ONOSPolicyEnforcer class (complete, copy-paste ready)
- How to integrate with FastAPI (code example)
- Policy translation (ALLOW → delete intent, BLOCK → DROP intent, LIMIT → meter, VERIFY → mirror)
- End-to-end testing
- Deployment options (single switch → distributed)
- Troubleshooting common issues

**Output:** Actual network enforcement of security policies

**Key Policies:**
```
ALLOW   → Remove any restrictions
VERIFY  → Mirror to controller for human review
LIMIT   → Rate limit to 1Mbps
BLOCK   → DROP all packets
```

---

### 6. PRODUCTION_IMPLEMENTATION_ROADMAP.md
**What:** Complete 8-week deployment schedule

**When:** Week 1 (start immediately)

**Contains:**
- 4-phase timeline (Data Collection → Training → Staged Deployment → Hardening)
- Week-by-week milestones with exact commands
- Decision points (go/no-go gates each week)
- Sample deployment from 1% → 10% → 100% traffic
- Success metrics (detection rate, FPR, latency, uptime)
- Resource requirements (compute, network, storage)
- Rollback procedures
- Post-deployment operations (daily, weekly, monthly tasks)

**Output:** Executable schedule to production

**Critical Path:**
```
Week 1-2: Collect data
Week 3-4: Train & validate
Week 5-6: Test (1% traffic)
Week 7: Increase (10% traffic)
Week 8: Production (100% traffic)
Week 9+: Operations & maintenance
```

---

## YOUR NEXT ACTIONS (In Order)

### Immediately (Today)

**Option A: You have network access**
```bash
# Start PCAP collection NOW (even while reading)
sudo tcpdump -i eth0 -w /data/pcaps/baseline_%Y-%m-%d_%H-%M-%S.pcap \
  -G 3600 -C 500 'tcp or udp' &

# Read through Week 1 section of PRODUCTION_IMPLEMENTATION_ROADMAP.md
# Set calendar reminder for "Check PCAP collection" every Friday
```

**Option B: You DON'T have network access yet**
```bash
# Download public attack dataset
wget https://www.unb.ca/cic/datasets/cicids2018.html

# Use that as your training data (faster, but less tuned to your network)
# Still need real baseline from your network eventually
```

### This Week

- [ ] Read all 6 guides in this folder (2-3 hours)
- [ ] Choose data collection method (tcpdump/Zeek/OVS)
- [ ] Deploy collection to your network
- [ ] Create directory for storing data (/data/pcaps, /data/training_data, etc.)

### Next Week

- [ ] Verify 7 days of baseline collection
- [ ] Collect attack samples (download CICIDS2018 or request from security team)
- [ ] Start feature extraction
- [ ] Begin model training

### Week 3

- [ ] Validate models on real data
- [ ] Make go/no-go decision for deployment
- [ ] If GO: Install ONOS, set up test environment
- [ ] If NO-GO: Collect more data, retrain

---

## KEY DIFFERENCES: Synthetic vs Real

### Synthetic (What You Had)

```python
flows = generate_synthetic_flows()
# Results in:
# - 95%+ accuracy on test set
# - But 50-60% on real network
# - Because patterns don't match YOUR network
# - Generic "average" doesn't apply to your specific infrastructure
```

### Real (What You Need)

```python
flows = collect_real_flows_from_your_network()
# Results in:
# - 95%+ accuracy on test set
# - ALSO 95%+ on production network
# - Because patterns match YOUR network exactly
# - Your ML models know YOUR specific normal behavior
```

---

## SUCCESS CRITERIA

You'll know deployment is successful when:

✅ **Week 4 (Model Validation)**
- Isolation Forest detects 95%+ of attacks
- False positive rate <= 5%
- XGBoost accuracy >= 90%

✅ **Week 6 (Test Deployment)**
- FastAPI processing 1% of traffic with 0 errors
- <1 false positive per hour
- Latency <100ms

✅ **Week 8 (Production)**
- 100% of traffic being analyzed
- Policy decisions being enforced in ONOS
- Network working normally (no complaints)
- Attacks being blocked in real-time

✅ **Week 12 (Stable Operations)**
- Continuous 24/7 operation
- Weekly retraining working smoothly
- New attack patterns being learned
- Zero false positives or escalation

---

## TROUBLESHOOTING QUICK LINKS

**"My PCAP collection failed"**
→ PCAP_COLLECTION_GUIDE.md → Troubleshooting section

**"Feature extraction is too slow"**
→ FEATURE_EXTRACTION_GUIDE.md → Batch method

**"Model accuracy is too low"**
→ Go back to PCAP_COLLECTION_GUIDE.md (collect more data) or adjust feature extraction

**"ONOS intents not being created"**
→ ONOS_POLICY_ENFORCEMENT.md → Common issues section

**"FastAPI crashed in production"**
→ PRODUCTION_IMPLEMENTATION_ROADMAP.md → Rollback procedure

---

## RESOURCE REQUIREMENTS SUMMARY

| Resource | Phase 1-2 | Phase 3-4 | Phase 5+ |
|----------|-----------|-----------|----------|
| **Disk** | 500GB+ | 1TB | 2TB+ |
| **CPU** | 1 core | 2-4 cores | 8+ cores |
| **RAM** | 8GB | 16GB | 32GB |
| **Network** | 1Gbps | 1Gbps | 10Gbps |
| **Time** | 14 days | 14 days | Ongoing |
| **Cost** | Minimal | Moderate | Depends on scale |

---

## FINAL CHECKLIST BEFORE STARTING

- [ ] I understand synthetic data won't work for production
- [ ] I have access to my network's traffic (or will request it)
- [ ] I understand the 8-week timeline
- [ ] I have >= 2TB disk space
- [ ] I have permission from security/network team to capture traffic
- [ ] I have read all 6 guides (or plan to read them systematically)
- [ ] I'm ready to start Phase 1 now

---

## 🚀 LET'S GO!

**Start with:** PCAP_COLLECTION_GUIDE.md

**Next hour goal:** Deploy tcpdump/Zeek on your network and verify it's capturing

**This week goal:** Have 7 days of collection running

**This month goal:** Have trained, validated models ready for deployment

**2 months goal:** Live production system blocking real attacks

You've got this! The guides are designed to be step-by-step executable. No ambiguity - just follow the commands.

---

## GUIDE FILE LOCATIONS

All guides are in the `plan_files/` folder:

```
plan_files/
├── REAL_WORLD_DEPLOYMENT_STRATEGY.md           (Overview - start here)
├── PCAP_COLLECTION_GUIDE.md                    (Week 1-2)
├── FEATURE_EXTRACTION_GUIDE.md                 (Week 3)
├── PRODUCTION_MODEL_VALIDATION.md              (Week 4)
├── LIVE_TELEMETRY_SOURCE.md                    (Week 5)
├── ONOS_POLICY_ENFORCEMENT.md                  (Week 5-6)
├── PRODUCTION_IMPLEMENTATION_ROADMAP.md        (Week 1-12+)
└── DEPLOYMENT_NAVIGATION_GUIDE.md              (This file - your map)
```

**Recommended reading order:**
1. This file (you are here)
2. REAL_WORLD_DEPLOYMENT_STRATEGY.md (overview)
3. PRODUCTION_IMPLEMENTATION_ROADMAP.md (timeline)
4. PCAP_COLLECTION_GUIDE.md (start today)
5. Follow weeks 1-12 schedule, reading other guides as needed

Good luck! 🎉
