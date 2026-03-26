# Dynamic ML Training Guide: Step-by-Step

This guide explains how to generate a real-time dataset dynamically, capture it, and train your Hybrid ML models (Isolation Forest & XGBoost) using a physically separate machine. This approach replaces static downloaded datasets (like KDDCup) with realistic, live East-West traffic.

---

## The Setup Architecture for Training

To train the models dynamically and cleanly, you will use a **3-Machine Setup** during the training phase. This allows one machine to purely handle the data science, while the other two generate the raw network interactions.

### The Machines:
1. **Machine A (The Brain/Trainer):** Your primary machine (Laptop 1) with Python, `scikit-learn`, `xgboost`, and `pandas`. This machine will run the training scripts.
2. **Machine B (The Victim):** A Linux machine (Laptop 3 or a VM) running `D-ITG` (to receive normal traffic).
3. **Machine C (The Attacker):** A Linux machine (Laptop 4 or a VM) running `Scapy`, `Nmap`, and `D-ITG` (to send both normal and attack traffic).

*Note:* If you are using the Mininet 2-Laptop setup, Machine B and C are simply two virtual hosts (e.g., `h1` and `h2`) inside Mininet on Laptop 2.

---

## Phase 1: Generating the "Normal" Baseline Dataset

Before the AI can detect attacks, it must first learn what "normal" data center traffic looks like. We use D-ITG to generate this randomized legitimate traffic.

### Step 1: Start the Receiver (Machine B)
Log into Machine B (The Victim) and start the D-ITG receiver daemon. This tells the machine to listen for incoming normal traffic.
```bash
ITGRecv
```

### Step 2: Start Packet Capture (Machine B or the Switch)
You need to record the traffic. Open a second terminal on Machine B (or on the Mininet switch/OVS bridge connecting them) and start `tshark` (command-line Wireshark) to capture the raw packets into a `.pcap` file.
```bash
sudo tshark -i eth0 -w normal_traffic_raw.pcap
```
*(Replace `eth0` with the correct interface name).*

### Step 3: Generate Normal Traffic (Machine C)
Log into Machine C (The Attacker/Client) and use D-ITG to send randomized flows (HTTP, VoIP, DNS simulations) to Machine B's IP address (e.g., `192.168.1.100`).
```bash
# Example: Send TCP traffic for 60 seconds at a random rate
ITGSend -a 192.168.1.100 -T TCP -t 60000
```
*Run various `ITGSend` commands with different protocols and packet sizes to create a diverse normal baseline.*

### Step 4: Stop Capture
Stop the `tshark` capture on Machine B (Ctrl+C). You now have `normal_traffic_raw.pcap`.

---

## Phase 2: Generating the "Attack" Dataset

Now we generate the malicious lateral movement traffic so the XGBoost model can learn the signatures of specific attacks.

### Step 1: Start Packet Capture
Start a new `tshark` capture for the attack data.
```bash
sudo tshark -i eth0 -w attack_traffic_raw.pcap
```

### Step 2: Launch Attacks (Machine C)
From Machine C, run various standardized attacks against Machine B.

**Attack 1: Port Scanning (Nmap)**
```bash
nmap -p 1-65535 -T4 -A -v 192.168.1.100
```

**Attack 2: SYN Flood / DoS (Scapy/Hping3)**
```bash
sudo hping3 -S --flood -V -p 80 192.168.1.100
```

**Attack 3: Data Exfiltration (Custom Scapy Script)**
Write a Python script on Machine C using Scapy to send packets with highly entropic (randomized/encrypted-looking) payloads to simulate data theft.

### Step 3: Stop Capture
Stop the `tshark` capture. You now have `attack_traffic_raw.pcap`.

---

## Phase 3: Feature Extraction (Preparing the Data)

Machine Learning models cannot read raw `.pcap` files directly. We must convert the packets into the 8 mathematical features required by our system (e.g., Packet Rate, Byte Entropy, Inter-Arrival Time).

### Step 1: Transfer Files to The Brain (Machine A)
Move both `normal_traffic_raw.pcap` and `attack_traffic_raw.pcap` to Machine A.

### Step 2: Run the Extractor Script
You will need a Python script (e.g., `pcap_to_csv.py`) on Machine A that reads the `.pcap` files, calculates the 8 features per flow, and outputs a clean dataset.

*   Run it on the normal data: Label all these flows as `0` (Normal).
*   Run it on the attack data: Label all these flows as `1` (Malicious).

Combine the results into a single file: `training_dataset_final.csv`.

---

## Phase 4: Clean Model Training (Machine A)

Now you will actually train the mathematical models on Machine A using the newly generated, dynamic CSV dataset.

### Step 1: Train the Unsupervised Model (Isolation Forest)
The Isolation Forest is Tier 1. It only needs to know what normal traffic looks like.
1. In your training script (`train.py`), load `training_dataset_final.csv`.
2. Filter the dataset so it **only** contains the rows labeled `0` (Normal).
3. Train the `scikit-learn` Isolation Forest on this normal-only subset.
   * *Why?* Because its job is to detect things that *aren't* normal. If you train it on attack data, it will think attacks are normal.
4. Export the model: `joblib.dump(iso_forest, 'isolation_forest_model.pkl')`

### Step 2: Train the Supervised Model (XGBoost)
XGBoost is Tier 2. It needs to know the difference between Normal and Malicious.
1. In `train.py`, use the **entire** `training_dataset_final.csv` (both `0` and `1` labels).
2. Split the data (e.g., 80% for training, 20% for testing to see how accurate it is).
3. Train the XGBoost Classifier to predict the `0` or `1` label based on the 8 features.
4. Export the model: `joblib.dump(xgboost_model, 'xgboost_model.pkl')`

### Step 3: Load into the Live Engine
1. Move `isolation_forest_model.pkl` and `xgboost_model.pkl` into the `brain/` directory.
2. When your FastAPI Python program starts, it will load these files into memory and use them to instantly score the real-time telemetry coming from ONOS.

---

## Appendix: How to Connect the 3 Machines (Wired & Wireless Options)

To run this training successfully, **Machine A (Trainer), Machine B (Victim), and Machine C (Attacker)** need to communicate. Here are all the possible ways to link them, ranked from best to easiest:

### 1. The "Hybrid Wi-Fi/Ethernet" Setup (🏆 Recommended for 3 Laptops)
*   **How:** Machine A (Trainer) connects to the Home Wi-Fi Router. Machine B (Victim) connects to the Home Wi-Fi Router, but ALSO has a physical Ethernet cable plugged directly into Machine C (Attacker). Machine C's Wi-Fi is turned OFF.
*   **IP Addressing:** Machine A and B get standard `192.168.x.x` Wi-Fi IPs via DHCP. The physical Ethernet connection between B and C must be given a static subnet (e.g., `10.0.0.1` and `10.0.0.2`).
*   **Why it's Best:** This is the ultimate compromise. You get the flawless, hardware-level timing of a physical Ethernet wire for your Attacker/Victim traffic (giving your ML model perfect precision), but Machine A is free to move around wirelessly. It also prevents the massive attack traffic from crashing your Home Wi-Fi Router.

### 2. The "All-Wired" Switch Setup (Maximum Realism)
*   **How:** Buy a cheap 5-port gigabit unmanaged switch ($15). Plug Machine A, B, and C into the switch using standard Ethernet cables. Turn off all Wi-Fi.
*   **IP Addressing:** Set static IPs on the same subnet (e.g., A = `10.0.0.10`, B = `10.0.0.11`, C = `10.0.0.12`).
*   **Why:** This guarantees zero packet loss and wire-speed communication between all 3 nodes.
*   **How:** If Machine B and C have Ethernet ports, plug a single Ethernet cable **directly** from Machine B into Machine C. Then, connect Machine A and Machine B to your home Wi-Fi.
*   **IP Addressing:** Machine B and C need static IPs on the Ethernet adapters that *differ* from the Wi-Fi. Example: Set Ethernet adapters to `10.0.0.1` and `10.0.0.2`.
*   **Why:** This creates a super-fast, private "attack tube" between B and C for training, while Machine A still collects data from B over the home Wi-Fi.

### 4. The "All-Wireless" Wi-Fi Setup (Easiest, but Risky)
*   **How:** Connect Machine A, B, and C to the same Home Wi-Fi network (or a Windows Mobile Hotspot created by Machine A).
*   **IP Addressing:** Automatic DHCP.
*   **Why Risky?** Launching a DoS/SYN Flood from C to B over Wi-Fi will likely overwhelm the router's wireless radio. It could drop the connection, ruin the dataset capture, or knock other devices (like smart TVs) offline temporarily.

### 5. The "Virtual LAN" Setup (Tailscale/ZeroTier) (Over the Internet)
*   **What it is:** A software-defined mesh VPN that creates a secure, encrypted virtual network over the public internet. It tricks the laptops into thinking they are plugged into the same physical switch, even if Machine A is in New York, Machine B is in London, and Machine C is an AWS Cloud VM.
*   **The Tool:** [Tailscale](https://tailscale.com/) (Free for up to 100 devices).

**Step-by-Step Setup:**
1.  **Create an Account:** Go to Tailscale.com and sign in with a Google, Microsoft, or GitHub account.
2.  **Install the Client:** Download and install the Tailscale app on Machine A (Windows/Linux), Machine B (Linux), and Machine C (Linux).
    *   *Linux Install Command:* `curl -fsSL https://tailscale.com/install.sh | sh`
3.  **Authenticate & Connect:** Run the app on each machine and log in using the exact same account you created in Step 1.
    *   *Linux Authenticate Command:* `sudo tailscale up`
4.  **Get the IP Addresses:** Once signed in, Tailscale assigns a permanent, static `100.x.y.z` IP address to each machine.
    *   *Command:* `tailscale ip -4`
5.  **Test Connectivity:** From Machine C (The Attacker), try to ping Machine B's new `100.x.y.z` address.
    *   *Command:* `ping 100.x.y.z`
6.  **Run the Training:** Configure `D-ITG` on Machine C to send traffic to Machine B's Tailscale IP. Run `tshark` on Machine B to listen explicitly on the `tailscale0` virtual network interface instead of `eth0` (e.g., `sudo tshark -i tailscale0 -w attack_traffic.pcap`).

**Pros:**
*   **Geographic Freedom:** The laptops do not need to be in the same room, building, or country. You can simulate East-West datacenter traffic using a mix of your laptop and cheap cloud VMs.
*   **Static IPs:** Unlike home Wi-Fi DHCP which changes IP addresses constantly, Tailscale gives permanent IPs, meaning you don't have to keep rewriting your Python scripts every time a machine reboots.
*   **Safe from Router Crashes:** It encapsulates the attack traffic in encrypted UDP packets. While a SYN flood might still use bandwidth, it is much less likely to crash your home Wi-Fi router's NAT table since the router just sees standard encrypted Tailscale traffic.
*   **Zero Hardware Cost:** No need to buy physical Ethernet switches or USB adapters.

**Cons:**
*   **Performance Overhead:** Because all traffic is encrypted (WireGuard protocol) and routed over the internet, maximum throughput is usually capped around ~200-500 Mbps depending on CPU power. It cannot match the 1,000 Mbps wire-speed of a physical gigabit switch.
*   **Latency:** There will be 20ms - 80ms of latency (ping time) between the machines, which is unrealistic for actual *internal* East-West data center traffic (which usually has < 1ms latency). This could slightly skew the `inter_arrival_time` features in your ML training compared to a real physical network.
*   **Requires Internet:** If your Wi-Fi drops or your ISP goes down, the machines lose connection to each other, even if they are sitting on the same desk.
