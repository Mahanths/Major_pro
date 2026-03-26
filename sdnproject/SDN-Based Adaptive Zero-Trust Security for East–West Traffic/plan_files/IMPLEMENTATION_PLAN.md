# SDN-Based Adaptive Zero-Trust Security - Implementation Plan

**Single Source of Truth for Phase-Based Build | Your PC = Laptop 1 (The Brain)**

---

## 🎯 Project Overview

This is a **Two-Tier Hybrid ML Zero-Trust Security System** for East-West datacenter traffic protection.

**Architecture:**
- **Laptop 1 (Your Brain)**: Runs ONOS Controller (Java) + FastAPI ML Engine (Python)
- **Laptop 2+ (Future)**: Runs network topology (Mininet/OVS) + generates live telemetry
- **Integration**: Laptops communicate via REST API on port 8000 (Brain) and OpenFlow 6653 (ONOS)

**ML Pipeline:**
- **Tier 1**: Isolation Forest (unsupervised anomaly detection)
- **Tier 2**: XGBoost (supervised malicious classification, only runs if Tier 1 flags)
- **Trust Core**: Dynamic Trust Score formula combining ML outputs + historical behavior

---

## 📋 Phase Breakdown & Tasks

### ✅ PHASE 0: Complete - Baseline Infrastructure
- [x] Created directory structure (brain/, training/, controller/, data/)
- [x] Wrote Python brain modules (feature_handler, hybrid_engine, trust_calculator)
- [x] Built FastAPI app skeleton with health + inference endpoints
- [x] Defined 8-feature ML vector schema (locked)
- [x] Created training pipeline scaffold (pcap_to_csv, train_models)
- [x] Wrote this single-source-of-truth implementation plan

**Status: Ready for local testing**

---

### PHASE 1: Python Brain Full Integration (Current)

**Goal:** Get FastAPI running locally with mocked models, validate all endpoints

**Tasks:**
1. Install Python dependencies
   ```bash
   cd brain/
   pip install -r requirements.txt
   ```

2. Start the FastAPI Brain
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

3. Test health endpoint
   ```bash
   curl http://localhost:8000/health
   ```

4. Send test telemetry (mocked inference)
   ```bash
   curl -X POST http://localhost:8000/infer \
     -H "Content-Type: application/json" \
     -d '{
       "flow_id": "192.168.1.10:192.168.1.20:443:443",
       "src_ip": "192.168.1.10",
       "dst_ip": "192.168.1.20",
       "src_port": 443,
       "dst_port": 443,
       "src_mac": "aa:bb:cc:dd:ee:01",
       "dst_mac": "aa:bb:cc:dd:ee:02",
       "flow_duration": 5.0,
       "fwd_packets": 100,
       "bwd_packets": 98,
       "fwd_bytes": 50000,
       "bwd_bytes": 48000,
       "dst_ports": [443],
       "tcp_flags": ["SYN", "ACK", "ACK", "FIN"],
       "inter_arrival_times": [0.05, 0.05, 0.05, 0.05]
     }'
   ```

5. Verify mocked ML inference works (should return 0.0 malicious_probability for clean traffic)

6. Add `/list_endpoints` documentation route

**Deliverables:**
- ✓ FastAPI running on localhost:8000
- ✓ All endpoints responding with correct JSON schema
- ✓ Mocked Isolation Forest + XGBoost working
- ✓ End-to-end inference → trust_score → policy_decision flow validated

**Timeline:** 1-2 hours (mostly testing)

---

### PHASE 2: Training Pipeline & Model Generation

**Goal:** Generate real ML models from synthetic training data

**Prerequisites:**
- D-ITG and Scapy installed (for traffic generation)
- TShark installed (for packet capture)

**Tasks:**
1. Generate normal baseline traffic
   ```bash
   # On a victim machine:
   ITGRecv
   # On an attacker machine:
   ITGSend -a 192.168.1.100 -T TCP -t 60000
   ```

2. Capture to PCAP
   ```bash
   sudo tshark -i eth0 -w normal_traffic.pcap
   ```

3. Generate attack traffic (SYN floods, port scans)
   ```bash
   sudo hping3 -S --flood -p 80 192.168.1.100
   ```

4. Convert PCAP → CSV using feature extractor
   ```bash
   python training/pcap_to_csv.py -i normal_traffic.pcap -o training_data/normal_features.csv -l 0
   python training/pcap_to_csv.py -i attack_traffic.pcap -o training_data/attack_features.csv -l 1
   ```

5. Merge datasets and train models
   ```bash
   # Merge normal + attack CSVs into one
   cat training_data/normal_features.csv training_data/attack_features.csv > training_data/training_dataset_final.csv
   
   # Train models
   python training/train_models.py -d training_data/training_dataset_final.csv
   ```

6. Export models to brain/models/*.pkl

**Deliverables:**
- brain/models/isolation_forest_model.pkl
- brain/models/xgboost_model.pkl
- Trained models integrated into running FastAPI

**Timeline:** 2-4 hours (depends on traffic generation time)

---

### PHASE 3: Telemetry & Dynamic Data Loop

**Goal:** Create live data pipeline from network → FastAPI

**Tasks:**
1. Write live feature extractor from network stats
   - Query ONOS FlowStats API
   - Transform to 8-feature vector
   - POST to FastAPI every 1 second

2. Create Mininet topology script (optional, for local testing)
   - 2-3 virtual hosts
   - Connect to ONOS on remote Laptop 1

3. Write traffic generators
   - Normal: D-ITG background flows
   - Attack: Scapy SYN floods, port scans

4. Wire telemetry → Brain → Trust → Policy decision loop

**Deliverables:**
- Live telemetry flowing to FastAPI
- Trust scores updating in real-time
- Policy decisions ready for ONOS

**Timeline:** 4-6 hours

---

### PHASE 4: ONOS Controller Integration (Java)

**Goal:** Close the feedback loop - ONOS → Python Brain → ONOS

**Tasks:**
1. Write controller/ZTProvider.java
   - Register as ONOS app
   - Listen for Packet-In events
   - Forward flow metadata to FastAPI

2. Write controller/FlowCollector.java
   - Pull OpenFlow flow statistics
   - Async HTTP POST to Brain

3. Write controller/PolicyEnforcer.java
   - Receive policy decision from Brain
   - Convert to ONOS Intent (Allow, Verify, Limit, Block)
   - Push Intent back to switches

4. Deploy to ONOS
   ```bash
   onos-app localhost install target/controller.oar
   ```

**Deliverables:**
- ONOS apps deployed and running
- Closed-loop: traffic → telemetry → ML → policy → enforcement

**Timeline:** 6-10 hours (Java + ONOS learning curve)

---

### PHASE 5: E2E Validation & KPIs

**Goal:** Validate system meets performance requirements

**KPIs to measure:**
- **Detection Latency** (Target: < 500ms from packet to policy enforcement)
- **False Positive Rate** (Target: < 5%)
- **Mitigation Precision** (Target: > 95% of attacks blocked)
- **Throughput** (Target: no degradation for normal traffic)

**Tasks:**
1. Design test scenarios
   - Normal traffic baseline
   - SYN flood attacks
   - Port scan attacks
   - Data exfiltration

2. Automate metrics collection
   - Capture timestamps at each stage
   - Calculate median/p95 latencies
   - Count false positives vs true positives

3. Run test suite and measure KPIs

4. Iterate model tuning if needed

**Deliverables:**
- Test runbook with reproducible scenarios
- KPI report with graphs
- Tuning recommendations

**Timeline:** 4-6 hours

---

### PHASE 6: Production Hardening (Optional)

**Tasks:**
- Add authentication/authorization to API
- Implement persistent trust state database (PostgreSQL)
- Add monitoring/observability (Prometheus metrics)
- Containerize with Docker
- Write deployment guides

**Timeline:** 8-12 hours

---

## 🛠️ Technology Stack

| Component | Technology | Location |
| --- | --- | --- |
| **ML/AI** | Scikit-Learn (Isolation Forest) + XGBoost | brain/ |
| **REST API** | FastAPI + Uvicorn | brain/app.py |
| **Feature Engineering** | Custom Python | brain/feature_handler.py |
| **Trust Logic** | Custom Math | brain/trust_calculator.py |
| **Model Training** | Joblib (serialization) | training/ |
| **SDN Controller** | ONOS (Java) | controller/ |
| **Network Topo** | Mininet (optional) | External |
| **Traffic Gen** | D-ITG, Scapy | External |

---

## 📂 Current Project Structure

```
SDN-Based Adaptive Zero-Trust Security for East-West Traffic/
├── 4-Laptop-Physical-Setup-Option.md          # Archived: hardware topology
├── dynamic-training-guide.md                  # Archived: training walkthrough
├── hosting-alternatives.md                    # Archived: deployment options
├── plan file                                  # Archived: old planning doc
├── project-structure-and-execution.md         # Archived: original arch
├── requirements.txt                           # Archived: dependencies
├── vm-implementation-guide.md                 # Archived: VM setup
├── IMPLEMENTATION_PLAN.md                     # ← THIS FILE (Master Plan)
├── brain/
│   ├── app.py                                 # FastAPI main app
│   ├── feature_handler.py                     # 8-feature extraction
│   ├── hybrid_engine.py                       # Tier 1+2 ML inference
│   ├── trust_calculator.py                    # Trust score formula
│   ├── requirements.txt                       # Python deps
│   └── models/
│       ├── isolation_forest_model.pkl         # (Generated by Phase 2)
│       └── xgboost_model.pkl                  # (Generated by Phase 2)
├── training/
│   ├── pcap_to_csv.py                         # PCAP → CSV converter
│   └── train_models.py                        # Train both models
├── controller/                                # (Empty, for Phase 4)
│   ├── ZTProvider.java
│   ├── FlowCollector.java
│   └── PolicyEnforcer.java
├── data/                                      # Placeholder for datasets
│   ├── normal_traffic.pcap
│   └── attack_traffic.pcap
└── [NETWORK TOPOLOGIES - Future Laptop 2+]
    ├── multi_zone_topo.py                     # Mininet topology
    ├── traffic_generators/                    # D-ITG, Scapy scripts
    └── live_feature_extractor.py              # Telemetry pusher
```

---

## 🚀 How to Start RIGHT NOW

### Immediate (Next 5 minutes):

1. **Install dependencies:**
   ```bash
   cd brain/
   pip install -r requirements.txt
   ```

2. **Start the Brain:**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

3. **Test it:**
   ```bash
   curl http://localhost:8000/health
   ```

### Next Phase (Following 1-2 hours):

- Generate training data (synthetic or from Mininet)
- Train Isolation Forest + XGBoost
- Verify real models load into FastAPI
- Send malicious test flows and confirm they're flagged

### Integration (Next 4-8 hours):

- Set up Mininet topology on Laptop 2 (or remote machine)
- Wire telemetry → Brain → Policy decision
- Deploy ONOS apps and close the loop

---

## 📊 Success Criteria (Done When...)

- [x] FastAPI app runs without errors
- [ ] Mocked inference works for clean and attack traffic
- [ ] Real ML models train and export successfully
- [ ] Live telemetry pipeline flows to API
- [ ] ONOS responds to policy decisions
- [ ] E2E attack is detected and blocked within 500ms
- [ ] False positive rate < 5%
- [ ] Runbook created for reproducible testing

---

## 🎓 Key Concepts Locked In (DO NOT DEVIATE)

1. **8-Feature Schema** (same everywhere):
   - flow_duration, fwd_packet_rate, bwd_packet_rate, byte_entropy, unique_dst_ports, tcp_flags_count, inter_arrival_time_min, inter_arrival_time_max

2. **Trust Formula** (non-negotiable):
   - T_new = 0.90 * T_old - 40 * P_mal - 25 * S_anom + R_bonus
   - Thresholds: BLOCK < 40, LIMIT 40-59, VERIFY 60-79, ALLOW ≥ 80

3. **API Contract** (all clients must follow):
   - POST /infer with TelemetryRequest
   - Response: InferenceResponse (tier1 + tier2 scores)
   - Trust endpoint chains off inference results

4. **Latency Target**: < 500ms end-to-end

---

## 🔗 Cross-References

- Architecture Detail: See `project-structure-and-execution.md` (sections II-V)
- Training Detail: See `dynamic-training-guide.md` (Phase 1-4)
- Hardware Setup: See `4-Laptop-Physical-Setup-Option.md`

---

**Last Updated:** March 25, 2026
**Status:** Phase 0 ✓, Phase 1 In Progress
**Maintained By:** Zero-Trust SDN Project Team
