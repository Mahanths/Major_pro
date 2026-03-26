# LIVE TELEMETRY SOURCE GUIDE
**Where to Get Real-Time Network Flows for FastAPI Inference**

---

## 🎯 GOAL
Connect your actual network to the FastAPI brain so it can analyze live flows and make real-time policy decisions.

---

## THE PROBLEM

Your FastAPI brain expects JSON telemetry like this:

```json
{
  "flow_id": "src:sport-dst:dport-proto",
  "src_ip": "10.0.1.5",
  "dst_ip": "10.0.2.100", 
  "src_port": 54321,
  "dst_port": 443,
  "protocol": "TCP",
  "timestamp": "2025-01-15T10:30:45.123Z",
  "fwd_packets": 120,
  "bwd_packets": 115,
  "flow_duration": 5.234,
  "fwd_packet_rate": 22.9,
  "bwd_packet_rate": 21.9,
  "packet_payload_bytes": 45678,
  "tcp_flags": ["SYN", "ACK", "FIN"],
  "byte_entropy": 0.45
}
```

**But where does this come from?** Your existing network doesn't magically generate this JSON.

You need a **telemetry collector** that watches network traffic and feeds the brain.

---

## OPTION 1: ZEEK IDS (Recommended - Production Quality)

### 1.1 Install Zeek

```bash
# Ubuntu/Debian
sudo apt-get install zeek zeek-aux

# Verify
which zeek
zeek --version
```

### 1.2 Configure for Your Network

**Edit Zeek config:**

```bash
sudo nano /opt/zeek/etc/node.cfg
```

**Add your interface:**

```
[zeek]
type=standalone
host=localhost
interface=eth0    # ← Your network interface
lb_method=pf_ring
lb_procs=4
```

### 1.3 Start Zeek

```bash
cd /opt/zeek
sudo ./bin/zeekctl
> install
> start
> status

# Logs appear in:
# /opt/zeek/logs/current/

# Key log files:
# - conn.log       = Flow summaries (what we need)
# - dns.log        = DNS queries
# - ssl.log        = Certificate info
# - http.log       = HTTP requests
```

### 1.4 Convert Zeek conn.log to Telemetry JSON

**Create converter script:**

```python
#!/usr/bin/env python3
"""
Convert Zeek conn.log to FastAPI telemetry JSON

Zeek conn.log format (tab-separated):
  id.orig_h  id.orig_p  id.resp_h  id.resp_p  proto  duration  
  orig_pkts  resp_pkts  orig_bytes  resp_bytes  conn_state  ...
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import socket

def parse_zeek_conn_log(conn_log_file):
    """Read Zeek conn.log and yield telemetry JSON objects"""
    
    with open(conn_log_file, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            fields = line.strip().split('\t')
            
            # Zeek conn.log header (approximate):
            # 0:timestamp 1:uid 2:src_ip 3:src_port 4:dst_ip 5:dst_port 
            # 6:proto 7:duration 8:orig_pkts 9:resp_pkts 10:orig_bytes 11:resp_bytes ...
            
            try:
                timestamp = float(fields[0])
                src_ip = fields[2]
                src_port = int(fields[3])
                dst_ip = fields[4]
                dst_port = int(fields[5])
                proto = fields[6].upper()
                duration = float(fields[7])
                fwd_packets = int(fields[8])
                bwd_packets = int(fields[9])
                fwd_bytes = int(fields[10])
                bwd_bytes = int(fields[11])
                conn_state = fields[12] if len(fields) > 12 else "UNKNOWN"
                
                # Calculate rates
                fwd_pps = fwd_packets / duration if duration > 0 else 0
                bwd_pps = bwd_packets / duration if duration > 0 else 0
                
                # Estimate byte entropy (simplified - normally from payload inspection)
                # Higher entropy = more random/compressed/encrypted
                payload_size = fwd_bytes + bwd_bytes
                entropy = min(payload_size / 100000, 1.0)  # Rough estimate
                
                # TCP flags from conn_state
                # Zeek states: S0, S1, SF, REJ, RSTO, RSTOS0, RSTR, RSTRH, SH, SHR, OTH
                tcp_flags = parse_zeek_state(conn_state)
                
                # TCP flags count (anomaly detection)
                tcp_flags_count = len(tcp_flags)
                
                # Build telemetry
                telemetry = {
                    "flow_id": f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{proto}",
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": proto,
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat() + "Z",
                    "fwd_packets": fwd_packets,
                    "bwd_packets": bwd_packets,
                    "flow_duration": duration,
                    "fwd_packet_rate": min(fwd_pps, 1000),  # Cap at 1000 pps
                    "bwd_packet_rate": min(bwd_pps, 1000),
                    "packet_payload_bytes": fwd_bytes + bwd_bytes,
                    "tcp_flags": tcp_flags,
                    "byte_entropy": entropy,
                    "conn_state": conn_state,
                    "src_is_local": is_private_ip(src_ip),
                    "dst_is_local": is_private_ip(dst_ip),
                }
                
                yield telemetry
                
            except (ValueError, IndexError) as e:
                print(f"Skip malformed line: {e}", file=sys.stderr)
                continue

def parse_zeek_state(state):
    """Convert Zeek connection state to TCP flags"""
    state_map = {
        'S0': ['SYN'],              # Connection attempt seen
        'S1': ['SYN', 'ACK'],       # Reply to connection attempt
        'SF': ['SYN', 'ACK', 'FIN'],  # Established and terminated
        'REJ': ['RST'],             # Reset
        'RSTR': ['RST'],            # Reset from responder
        'RSTOS0': ['RST'],          # Reset occurred, state 0
        'SH': ['SYN', 'FIN'],       # Incomplete shutdown
        'OTH': ['FIN', 'ACK'],      # Other
    }
    return state_map.get(state, [])

def is_private_ip(ip):
    """Check if IP is private (RFC 1918)"""
    try:
        parsed = socket.inet_aton(ip)
        octet1 = ord(parsed[0:1])
        return (octet1 == 10 or 
                octet1 == 172 or 
                octet1 == 192)
    except:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: zeek_to_telemetry.py <conn.log> [output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Parse and output
    out = sys.stdout if not output_file else open(output_file, 'w')
    
    for telemetry in parse_zeek_conn_log(input_file):
        print(json.dumps(telemetry), file=out)
    
    if output_file:
        out.close()
        print(f"✅ Generated {output_file}", file=sys.stderr)
```

### 1.5 Run Zeek to FastAPI Pipeline

```bash
#!/bin/bash
# zeek_to_fastapi_pipeline.sh

ZEEK_LOG="/opt/zeek/logs/current/conn.log"
BRAIN_ENDPOINT="http://localhost:8000/infer"
TELEMETRY_FILE="/tmp/zeek_telemetry.jsonl"

while true; do
    # Convert latest Zeek conn.log to telemetry
    python3 zeek_to_telemetry.py "$ZEEK_LOG" "$TELEMETRY_FILE"
    
    # Send to FastAPI brain (batch or real-time)
    tail -n 100 "$TELEMETRY_FILE" | while read -r line; do
        curl -X POST "$BRAIN_ENDPOINT" \
          -H "Content-Type: application/json" \
          -d "$line"
    done
    
    sleep 5  # Poll every 5 seconds
done
```

---

## OPTION 2: tshark (Lightweight, Real-Time)

### 2.1 Install tshark

```bash
sudo apt-get install tshark

# Allow non-root capture
sudo usermod -a -G wireshark $USER
newgrp wireshark
```

### 2.2 Live Capture & Conversion

```bash
#!/bin/bash
# tshark_to_fastapi.sh

INTERFACE="eth0"
BRAIN_ENDPOINT="http://localhost:8000/infer"

# tshark fields (flow-level aggregation)
tshark -i "$INTERFACE" \
  -f "tcp or udp" \
  -T fields \
  -e ip.src \
  -e ip.dst \
  -e tcp.srcport \
  -e udp.srcport \
  -e tcp.dstport \
  -e udp.dstport \
  -e ip.proto \
  -e tcp.len \
  -e tcp.flags \
  -e frame.time \
  | python3 - << 'EOF'
import sys
import json
from datetime import datetime
from collections import defaultdict

flows = defaultdict(lambda: {
    'packets': 0, 
    'bytes': 0,
    'first_time': None,
    'last_time': None,
    'flags': set()
})

for line in sys.stdin:
    fields = line.strip().split('\t')
    
    # Parse fields
    src_ip, dst_ip, tcp_src, udp_src, tcp_dst, udp_dst, proto, tcp_len, flags, timestamp = fields
    
    src_port = tcp_src if tcp_src else udp_src
    dst_port = tcp_dst if tcp_dst else udp_dst
    
    # Flow key
    flow_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
    
    # Aggregate
    flows[flow_key]['packets'] += 1
    flows[flow_key]['bytes'] += int(tcp_len or 0)
    flows[flow_key]['flags'].update(flags.split(',') if flags else [])
    
    if not flows[flow_key]['first_time']:
        flows[flow_key]['first_time'] = datetime.fromisoformat(timestamp)
    flows[flow_key]['last_time'] = datetime.fromisoformat(timestamp)
    
    # Output aggregated telemetry
    duration = (flows[flow_key]['last_time'] - flows[flow_key]['first_time']).total_seconds()
    pps = flows[flow_key]['packets'] / duration if duration > 0 else 0
    
    telemetry = {
        "flow_id": flow_key,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": int(src_port),
        "dst_port": int(dst_port),
        "protocol": "TCP" if tcp_src else "UDP",
        "timestamp": datetime.now().isoformat() + "Z",
        "fwd_packets": flows[flow_key]['packets'],
        "flow_duration": duration,
        "fwd_packet_rate": min(pps, 1000),
        "packet_payload_bytes": flows[flow_key]['bytes'],
        "tcp_flags": list(flows[flow_key]['flags']),
    }
    
    print(json.dumps(telemetry))
    
    # Flush old flows
    for key in list(flows.keys()):
        age = (datetime.now() - flows[key]['last_time']).total_seconds()
        if age > 300:  # Forget about flows older than 5 minutes
            del flows[key]
EOF
```

---

## OPTION 3: OVS (Open vSwitch) Monitoring

### 3.1 Enable OVS Flow Stats

```bash
# If using OVS for your network topology

# Enable statistics collection
ovs-vsctl set Bridge br0 fail_mode=secure

# Query flows
ovs-ofctl dump-flows br0

# Output format:
# in_port=1,actions=normal,n_packets=1000,n_bytes=45000
```

### 3.2 Convert OVS Stats to Telemetry

```python
#!/usr/bin/env python3
"""
Poll OVS and convert flow stats to telemetry JSON
"""

import subprocess
import json
import time
from datetime import datetime

def poll_ovs_flows():
    """Query OVS and parse flow statistics"""
    
    try:
        result = subprocess.run(
            ['ovs-ofctl', 'dump-flows', 'br0'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        flows = []
        for line in result.stdout.split('\n'):
            if not line.strip() or line.startswith('NXST'):
                continue
            
            # Parse OVS flow stats
            # Example: in_port=1,tcp,nw_src=10.0.0.1,nw_dst=10.0.0.2,...
            flow_parts = line.split(',')
            
            telemetry = {
                "timestamp": datetime.now().isoformat() + "Z",
                "source": "ovs",
            }
            
            for part in flow_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key == 'nw_src':
                        telemetry['src_ip'] = value
                    elif key == 'nw_dst':
                        telemetry['dst_ip'] = value
                    elif key == 'tp_src':
                        telemetry['src_port'] = int(value)
                    elif key == 'tp_dst':
                        telemetry['dst_port'] = int(value)
                    elif key == 'n_packets':
                        telemetry['fwd_packets'] = int(value)
                    elif key == 'n_bytes':
                        telemetry['packet_payload_bytes'] = int(value)
            
            if 'src_ip' in telemetry:  # Only flows with complete info
                flows.append(telemetry)
        
        return flows
    
    except Exception as e:
        print(f"Error polling OVS: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/infer"
    
    while True:
        flows = poll_ovs_flows()
        
        for flow in flows:
            # Send to FastAPI brain
            import requests
            try:
                requests.post(endpoint, json=flow, timeout=1)
            except Exception as e:
                print(f"Failed to send telemetry: {e}")
        
        time.sleep(10)
```

---

## OPTION 4: Kafka Streaming (High-Volume)

For production deployments with tons of flows per second:

```python
#!/usr/bin/env python3
"""
Consume network telemetry from Kafka and feed to FastAPI brain
"""

from kafka import KafkaConsumer
import json
import requests

KAFKA_BROKERS = ['localhost:9092']
KAFKA_TOPIC = 'network-telemetry'
BRAIN_ENDPOINT = 'http://localhost:8000/infer'

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    group_id='brain-telemetry-consumer'
)

for message in consumer:
    telemetry = message.value
    
    # Send to FastAPI
    try:
        response = requests.post(BRAIN_ENDPOINT, json=telemetry, timeout=0.5)
        if response.status_code != 200:
            print(f"Brain error: {response.text}")
    except Exception as e:
        print(f"Failed to send telemetry: {e}")
```

---

## OPTION 5: FastAPI Telemetry Receiver

Make your brain directly receive telemetry from SDN controller:

```python
# In brain/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TelemetryBatch(BaseModel):
    flows: list[dict]  # List of telemetry objects

@app.post("/telemetry/batch")
async def receive_telemetry_batch(batch: TelemetryBatch):
    """
    Receive batch of flows from network collector
    
    POST /telemetry/batch
    {
        "flows": [
            {
                "flow_id": "...",
                "src_ip": "...",
                ...
            },
            ...
        ]
    }
    """
    results = []
    
    for flow in batch.flows:
        try:
            # Process each flow through inference pipeline
            policy_response = await infer(flow)
            results.append(policy_response)
        except Exception as e:
            results.append({"error": str(e), "flow_id": flow.get("flow_id")})
    
    return {
        "processed": len(batch.flows),
        "results": results
    }
```

---

## 🎯 DEPLOYMENT RECOMMENDATION

| Scenario | Recommendation |
|----------|-----------------|
| Development/Lab | **tshark** (easy, lightweight) |
| Production <10K flows/sec | **Zeek** (best analysis, ~50MB/hr logs) |
| Production >10K flows/sec | **Kafka + custom collector** (streaming) |
| OVS-based network | **Option 3** (native integration) |
| Multi-sensor | **Kafka broker** (centralize all sources) |

---

## 📊 EXPECTED TELEMETRY VOLUME

```
Typical Enterprise Network:
  ~1,000 - 10,000 flows per second
  ~100MB - 1GB logs per hour
  
Small Office (< 50 users):
  ~100 - 500 flows/second
  
ISP/Cloud:
  >100,000 flows/second
```

**Your FastAPI brain can handle:**
- ~100 decisions/second (single process)
- ~500 decisions/second (with 5 worker processes)
- >5,000 decisions/second (with load balancer + 10 workers)

**Sizing example:**
```
If 5,000 flows/sec, need:
  - 5,000 / 500 = 10 FastAPI worker processes
  - 1 load balancer (nginx) to distribute
  - Model inference GPU (optional, 10x speedup)
```

---

## ✅ CHECKLIST

- [ ] Chose telemetry source (Zeek, tshark, OVS, Kafka)
- [ ] Installed and configured tool
- [ ] Running on network interface
- [ ] Producing valid JSON telemetry
- [ ] Tested connection to FastAPI endpoint
- [ ] Monitoring telemetry arrival rate
- [ ] Confirmed FastAPI receiving flows
- [ ] FastAPI returning policy decisions
- [ ] Decisions fed to ONOS controller
- [ ] ONOS enforcing policies on switches

---

## 🚀 NEXT: Connect to ONOS

Once telemetry is flowing and policies are being decided, pipe the decisions to ONOS to actually block/allow flows in your real network!

See: `ONOS_POLICY_ENFORCEMENT.md`
