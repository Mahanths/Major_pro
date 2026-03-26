# Project Environment & Hosting Alternatives

You cannot run this project inside my AI environment. I am a cloud-based conversational coding assistant. I do not have a Linux routing kernel, physical network adapters, or the ability to generate live network traffic on demand for you.

To achieve this project, you need environments that can handle **low-level Layer 2/Layer 3 networking (Open vSwitch, Mininet)** and **High-Performance Data Science (Python/XGBoost)**.

Here are the 4 methods you can use to host and run this project yourself, ranked from easiest to most realistic.

---

### Option 1: The "1-Laptop WSL2" Method (Highly Recommended)
You run everything on a single Windows laptop. You use Windows Subsystem for Linux (WSL2) to create a hidden Linux environment inside Windows.

*   **How it works:** ONOS Controller and the Python Brain run natively on your Windows Desktop. Mininet runs inside WSL2 (Ubuntu) to simulate the data center network. They connect via `localhost`.
*   **Pros:**
    *   **Completely Free.** No extra hardware.
    *   **Easiest Setup:** Everything is on one screen. Perfect for writing the code and debugging.
    *   **Fast:** No internet routing means instant communication between the brain and the fake network.
*   **Cons:**
    *   **Simulated:** The traffic is entirely virtual. It is not crossing real network cards.
    *   **Resource Heavy:** Running Java (ONOS), Python ML models, and a simulated Linux network simultaneously requires at least 16GB of RAM on your Windows machine.

### Option 2: The "Type-2 Hypervisor" Method (VirtualBox / VMware)
You install a hypervisor software on your main laptop to create entirely isolated Virtual Machines.

*   **How it works:** You create 2 or 3 Ubuntu VMs inside VirtualBox. VM 1 runs the Controller/Brain. VM 2 runs Mininet. VM 3 runs the Attacker. You link them together using VirtualBox "Internal Networks".
*   **Pros:**
    *   **Clean Isolation:** If you mess up the Linux OS, you just delete the VM and start over without risking your host Windows machine.
    *   **Modular Learning:** Teaches you how to link separate operating systems together using virtual bridging.
*   **Cons:**
    *   **Slower:** Running full GUI Virtual Machines is incredibly heavy on your CPU and RAM compared to WSL2.

### Option 3: The "Cloud VPS" Method (AWS / DigitalOcean)
You rent Virtual Private Servers (VPS) from a cloud provider.

*   **How it works:** You rent an Ubuntu server on AWS EC2 or DigitalOcean Droplets. You SSH into the server and install ONOS, Mininet, and Python.
*   **Pros:**
    *   **Infinite Resources:** If your laptop is weak (e.g., only 8GB RAM), you can rent a 32GB RAM cloud server for a few cents an hour to run everything smoothly.
    *   **Always On:** You can close your laptop and the network keeps running in the cloud.
*   **Cons:**
    *   **Costs Money:** You pay by the hour for cloud compute.
    *   **High Latency:** Every time you type a command or ONOS makes a decision, it has to travel over the internet, adding latency.
    *   **Complex Security:** Cloud providers heavily restrict "spoofed" network traffic (which Mininet and Scapy use to simulate attacks). You often have to disable strict source-destination checks in AWS to get it to work.

### Option 4: The Physical Laptops with "Bridged VMs" (Highly Realistic & Clean)
You use 3 physical Windows/Mac laptops, but instead of wiping their hard drives to install Linux natively, you install VirtualBox on all 3 of them. Each laptop runs 1 Ubuntu Virtual Machine. You then connect the 3 physical laptops using a **Hybrid Wi-Fi/Ethernet Topology**.

*   **How it works:** 
    *   **Laptop 1 (The AI Brain):** Runs VM 1 (Java ONOS & Python ML). Connects to your Home Wi-Fi Router.
    *   **Laptop 2 (The Target Network / Bridge):** Runs VM 2. Connects to the Home Wi-Fi Router. *Crucially*, it also has a physical Ethernet cable plugged directly into Laptop 3. This VM acts as the Open vSwitch, bridging the Wi-Fi control traffic to the Ethernet attack traffic.
    *   **Laptop 3 (The Attacker):** Runs VM 3. Wi-Fi is turned **OFF**. It is connected *only* via the physical Ethernet cable to Laptop 2.
    *   **The Secret Sauce:** In VirtualBox, you set the Network Adapters for VM 2 and VM 3 to **"Bridged Adapter"** pointing at the physical Ethernet cards. This allows the VMs to bypass Windows and directly send raw packets onto the physical copper wire.
*   **Pros:**
    *   **Perfect ML Data:** All the heavy attack traffic between Laptop 3 and Laptop 2 travels across a flawless physical copper wire. This generates perfect, microsecond-accurate `inter_arrival_time` statistics for the AI to train on, without home Wi-Fi lag spikes interfering.
    *   **Wi-Fi Protection:** By keeping the attacks isolated on the Ethernet cable between Laptops 2 and 3, you prevent the massive SYN floods from crashing your home Wi-Fi router. Laptop 1 simply monitors the results peacefully over the air.
    *   **No Reformatting:** You keep your normal Windows OS. 
*   **Cons:**
    *   **Hardware Intensive:** You need 3 separate laptops.
    *   **Dongle City:** If your laptops only have Wi-Fi (like MacBooks), you must buy USB-to-Ethernet adapters for Laptop 2 and 3. Do not run the attack traffic over Wi-Fi.
