# Project Architecture: Models, Structure, and Execution

This document provides a highly detailed breakdown of the exact Machine Learning models required, the specific folder structure you should build on your computer, and the step-by-step Execution Workflow.

---

## 🧠 1. The Required Machine Learning Models

To achieve "Adaptive Zero-Trust" with high accuracy and low false positives, you must build **exactly two** Machine Learning models working together in a "Two-Tier Hybrid Pipeline."

### Model 1: The "Tier 1" Anomaly Detector (Isolation Forest)
*   **What it is:** An Unsupervised Machine Learning algorithm (`sklearn.ensemble.IsolationForest`).
*   **Its Job:** To learn what "Normal" traffic looks like and act as a highly efficient, CPU-lightweight gatekeeper.
*   **How it works:** You train it *only* on normal traffic datasets. When live traffic flows in, it asks: *"Does this look strange?"*
*   **Why we need it:** If a hacker invents a brand new "Zero-Day" attack tomorrow, Model 2 (XGBoost) won't catch it because it's never seen it. But Model 1 will catch it because it knows the alien traffic *doesn't look normal*.
*   **Speed:** Evaluates packets in `< 2 milliseconds`.

### Model 2: The "Tier 2" Classifier (XGBoost)
*   **What it is:** A Supervised Gradient Boosting algorithm (`xgboost.XGBClassifier`).
*   **Its Job:** To act as the Heavy-Duty Specialist. It only wakes up if Model 1 says "This looks strange."
*   **How it works:** You train it on a massive dataset of labeled attacks (DDoS, Syn Floods, Port Scans). It looks at the strange traffic and says: *"I am 98.4% confident this is a Scapy SYN Flood."*
*   **Why we need it:** It provides the mathematical `Malicious Probability Score` that your Trust Engine needs to actually lower the Trust Score of an IP address.
*   **Speed:** Evaluates packets in `~10 milliseconds`.

---

## 📂 2. Distributed Folder Structure (What goes where?)

Because we are using the **3-Laptop Hybrid VM Setup**, you do not put all the code on one machine. You must split your project folders across the 3 physical machines. Create these exact folder structures on the respective laptops:

### On Laptop 1 (The AI Brain & Controller)
This machine holds the heavy logic. It only needs the `brain/` and `controller/` code.

```text
SDN_Project_Laptop1/
│
├── brain/                              # The Python ML Intelligence Layer
│   ├── app.py                          # The FastAPI server (Listens on port 8000)
│   ├── hybrid_engine.py                # Script that runs the data through Model 1 and Model 2
│   ├── trust_calculator.py             # Script containing the Math formula for Trust Scores
│   ├── requirements.txt                # pip dependencies (fastapi, scikit-learn, etc.)
│   └── models/                         # Where you save your trained AI
│       ├── isolation_forest_model.pkl  # Extracted from training
│       └── xgboost_model.pkl           # Extracted from training
│
└── controller/                         # The Java ONOS Controller Apps
    ├── ZTProvider.java                 # Intercepts 'Packet-In' events from Laptop 2
    ├── FlowCollector.java              # Sends network JSON stats to the python brain
    └── PolicyEnforcer.java             # Receives the AI Score and drops/allows the traffic
```

### On Laptop 2 (The Bridge & Telemetry Collector)
This Ubuntu VM acts as the inline physical switch. It doesn't run ONOS or the ML models. It just runs traffic capture scripts.

```text
SDN_Project_Laptop2/
│
├── capture_tools/                      # Tools to extract features from the physical wire
│   ├── live_feature_extractor.py       # (Optional if not using FlowCollector.java) Reads TShark live and sends JSON to Laptop 1
│   └── pcap_to_csv.py                  # Script used ONLY during training to convert raw pcaps
│
└── normal_traffic_gen/                 
    └── start_ditg_receiver.sh          # Bash script to start the D-ITG background daemon to receive normal traffic
```

### On Laptop 3 (The Attacker)
This Ubuntu VM is purely for generating network traffic. It does no AI processing and does no network routing.

```text
SDN_Project_Laptop3/
│
├── attack_scripts/                     # Python Scapy scripts to launch attacks
│   ├── launch_syn_flood.py             # Generates a randomized TCP SYN flood
│   ├── launch_port_scan.sh             # An automated Nmap bash script
│   └── launch_data_exfiltration.py     # Sends highly entropic packet sizes
│
└── normal_traffic_gen/                 
    └── generate_normal_baseline.sh     # Bash script using D-ITG to send clean HTTP/DNS traffic to Laptop 2
```

---

## 🚀 3. Detailed Execution Steps (End-to-End)

Once your code is written and your folders are structured like above, here are the detailed, step-by-step instructions to turn the whole system on and protect the network.

### Phase 1: Pre-Flight (Starting the Core Systems)
1.  **Start the ONOS Controller:** On Laptop 1, open a terminal and launch ONOS.
    *   *Command:* `bazel run onos-local -- clean debug` (or whatever specific ONOS start command your version uses).
    *   *Verify:* Ensure ONOS is listening on port `6653`.
2.  **Start the AI Brain:** On Laptop 1, open a second terminal, navigate to `/brain`, and launch the FastAPI server.
    *   *Command:* `uvicorn app:app --host 0.0.0.0 --port 8000`
    *   *Verify:* The terminal should say `Application startup complete`. The AI models (`.pkl`) are now loaded into physical RAM.

### Phase 2: Connecting the Network
3.  **Start the Switches:** Over on Laptop 2 (The Linux Bridge/Mininet), start the network.
    *   *If using Physical Bridged VMs:* `sudo ovs-vsctl set-controller br0 tcp:<Laptop_1_IP>:6653`
    *   *If using Mininet:* `sudo python3 multi_zone_topo.py`
4.  **Verify Handshake:** Look at the ONOS terminal on Laptop 1. You should see a log message saying `Device Connected: of:00000000001`. The network is now successfully controlled by ONOS.

### Phase 3: The Automated Loop (Live Traffic)
Once Phase 1 and 2 are running, the entire security pipeline is fully automated. You do not manually type anything. Here is what happens under the hood when traffic occurs:

1.  **The Trigger:** Laptop 3 (Attacker) tries to ping or scan Laptop 2 (Victim).
2.  **The Intercept:** The Open vSwitch on Laptop 2 realizes there is no security rule for this traffic. It pauses the packet and fires a `Packet-In` message over Wi-Fi to Laptop 1 (ONOS).
3.  **The Telemetry:** ONOS's `FlowCollector.java` pulls the speed, size, and TCP flags of that packet. It wraps it in a JSON HTTP POST request and shoots it to the FastAPI Brain running on port 8000.
4.  **The AI Calculation:** `hybrid_engine.py` receives the JSON.
    *   It asks the *Isolation Forest*: "Is this normal?" (Result: -1 for Anomaly).
    *   It wakes up *XGBoost*: "Classify this." (Result: 95% Port Scan).
5.  **The Trust Update:** `trust_calculator.py` takes the 95% malicious score and drops the Attacker's Trust Score from 100 down to 20.
6.  **The Enforcement:** FastAPI returns a JSON response to ONOS: `{"action": "BLOCK", "trust_score": 20}`.
7.  **The Drop:** `PolicyEnforcer.java` in ONOS compiles a hard OpenFlow `DROP` rule and pushes it back over Wi-Fi to Laptop 2.
8.  **The Result:** Laptop 2's physical switch locks down. Laptop 3's terminal freezes. The attack is terminated dynamically.
