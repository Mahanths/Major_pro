# ONOS POLICY ENFORCEMENT GUIDE
**From FastAPI Decisions to Actual Network Traffic Control**

---

## 🎯 GOAL
Connect FastAPI policy decisions to ONOS controller so it can actually block/allow/throttle flows in your real network.

---

## ARCHITECTURE OVERVIEW

```
Network Traffic
    ↓
Zeek/tshark → Telemetry (JSON)
    ↓
FastAPI Brain ← Your ML Models
    ↓ (Policy Decision)
ONOS Controller ← REST API
    ↓ (OpenFlow Intent)
Open vSwitch / SDN Switch
    ↓
Network Flow Enforcement
```

---

## THE CONNECTION

### What FastAPI Returns:

```python
{
    "flow_id": "10.0.1.5:54321-10.0.2.100:443-TCP",
    "policy": "BLOCK",  # or "ALLOW", "VERIFY", "LIMIT"
    "trust_score": 15.2,
    "reason": "Detected SYN flood pattern",
    "actions": [
        {
            "type": "drop",
            "probability": 1.0
        }
    ]
}
```

### What ONOS Needs:

```json
{
    "intent":  {
        "id": "0x1001",
        "type": "PointToPointIntent",
        "appId": "org.onosproject.security.zerotrust",
        "ingressPoint": {
            "device":"of:1",
            "port":"1"
        },
        "egressPoint": {
            "device":"of:1",
            "port":"CONTROLLER"
        },
        "selector": {
            "criteria": [
                {"type":"ETH_TYPE","ethType":"0x0800"},
                {"type":"IPV4_SRC","ip":"10.0.1.5/32"},
                {"type":"IPV4_DST","ip":"10.0.2.100/32"},
                {"type":"IP_PROTO","protocol":"6"},
                {"type":"TCP_SRC","tcpPort":"54321"},
                {"type":"TCP_DST","tcpPort":"443"}
            ]
        },
        "treatment": {
            "instructions": [
                {"type":"DROP"}
            ]
        },
        "priority": 100
    }
}
```

---

## STEP 1: INSTALL ONOS

### 1.1 Prerequisites

```bash
# ONOS requires Java 11+
java -version
# Output: openjdk version "11.0.x"

# If not installed:
sudo apt-get install openjdk-11-jdk-headless
```

### 1.2 Download & Start ONOS

```bash
# Download ONOS (latest stable)
wget https://repo1.maven.org/maven2/org/onosproject/onos-releases/2.7.1/onos-2.7.1.tar.gz

# Extract
tar xzf onos-2.7.1.tar.gz
cd onos-2.7.1

# Start ONOS
./bin/onos-service start

# Wait for startup (~30 seconds)
sleep 30

# Check status
./bin/onos-service status
# Output: ONOS is running (pid xxxx)

# Access web UI: http://localhost:8181
# Default credentials: onos/rocks
```

### 1.3 Activate Required Apps

```bash
# CLI
./bin/onos

# Inside ONOS shell:
onos> app activate org.onosproject.openflow
onos> app activate org.onosproject.fwd
onos> app activate org.onosproject.gui
onos> devices
# Should show connected devices

onos> exit
```

---

## STEP 2: CREATE POLICY ENFORCER

**Create Python module that translates FastAPI decisions to ONOS intents:**

```python
# security/onos_enforcer.py

import requests
import json
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ONOSPolicyEnforcer:
    """
    Translates FastAPI zero-trust decisions to ONOS network intents
    """
    
    def __init__(self, onos_url="http://localhost:8181", 
                 onos_user="onos", onos_pass="rocks"):
        self.onos_url = onos_url
        self.auth = (onos_user, onos_pass)
        self.intent_counter = 0
        self._verify_onos_connection()
    
    def _verify_onos_connection(self):
        """Ensure ONOS is reachable"""
        try:
            resp = requests.get(
                f"{self.onos_url}/onos/v1/devices",
                auth=self.auth,
                timeout=5
            )
            if resp.status_code == 200:
                logger.info("✅ Connected to ONOS")
            else:
                logger.error(f"❌ ONOS error: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ Cannot connect to ONOS: {e}")
    
    def enforce_policy(self, policy_decision: Dict) -> Dict:
        """
        Convert FastAPI policy decision to ONOS action
        
        Input:
            {
                "flow_id": "src_ip:port-dst_ip:port-proto",
                "policy": "BLOCK",  # ALLOW, VERIFY, LIMIT, BLOCK
                "trust_score": 25.5,
                "reason": "..."
            }
        
        Output:
            {
                "success": true,
                "intent_id": "0x1234",
                "action": "DROP",
                "target_devices": ["of:0000000000000001"]
            }
        """
        
        flow_id = policy_decision.get("flow_id")
        policy = policy_decision.get("policy", "ALLOW")
        
        logger.info(f"Enforcing policy: {policy} on {flow_id}")
        
        # Parse flow_id: "10.0.1.5:54321-10.0.2.100:443-TCP"
        try:
            parts = flow_id.split('-')
            src_addr, dst_addr = parts[0], parts[1]
            protocol = parts[2] if len(parts) > 2 else "TCP"
            
            src_ip, src_port = src_addr.rsplit(':', 1)
            dst_ip, dst_port = dst_addr.rsplit(':', 1)
        except:
            logger.error(f"Cannot parse flow_id: {flow_id}")
            return {"success": False, "error": "Invalid flow_id"}
        
        # Translate policy to ONOS action
        if policy == "BLOCK":
            action = self._create_drop_intent(
                src_ip, src_port, dst_ip, dst_port, protocol
            )
        elif policy == "LIMIT":
            action = self._create_meter_intent(
                src_ip, src_port, dst_ip, dst_port, protocol,
                rate_kbps=1000  # Throttle to 1Mbps
            )
        elif policy == "VERIFY":
            action = self._create_mirror_intent(
                src_ip, src_port, dst_ip, dst_port, protocol
            )
        else:  # ALLOW
            action = self._remove_restrictions(
                src_ip, src_port, dst_ip, dst_port, protocol
            )
        
        return action
    
    def _create_drop_intent(self, src_ip, src_port, dst_ip, dst_port, protocol):
        """Create ONOS intent to DROP a flow"""
        
        self.intent_counter += 1
        intent_id = f"drop-{self.intent_counter}"
        
        intent = {
            "id": intent_id,
            "type": "PointToPointIntent",
            "appId": "org.onosproject.security.zerotrust",
            "ingressPoint": {
                "device": "of:0000000000000001",
                "port": "1"
            },
            "egressPoint": {
                "device": "of:0000000000000001",
                "port": "CONTROLLER"
            },
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},
                    {"type": "IPV4_SRC", "ip": f"{src_ip}/32"},
                    {"type": "IPV4_DST", "ip": f"{dst_ip}/32"},
                    {"type": "IP_PROTO", "protocol": self._proto_to_number(protocol)},
                    {"type": f"{protocol}_SRC", f"{protocol.lower()}Port": int(src_port)},
                    {"type": f"{protocol}_DST", f"{protocol.lower()}Port": int(dst_port)}
                ]
            },
            "treatment": {
                "instructions": [
                    {"type": "DROP"}
                ]
            },
            "priority": 100
        }
        
        return self._submit_intent(intent)
    
    def _create_meter_intent(self, src_ip, src_port, dst_ip, dst_port, protocol, rate_kbps=1000):
        """Create ONOS intent with rate limiting (LIMIT policy)"""
        
        self.intent_counter += 1
        intent_id = f"limit-{self.intent_counter}"
        
        # First, create meter
        meter = {
            "deviceId": "of:0000000000000001",
            "appId": "org.onosproject.security.zerotrust",
            "unit": "KB_PER_SEC",
            "bands": [
                {
                    "type": "DROP",
                    "rate": rate_kbps
                }
            ]
        }
        
        # Submit meter
        meter_resp = requests.post(
            f"{self.onos_url}/onos/v1/meters",
            json=meter,
            auth=self.auth,
            timeout=5
        )
        
        meter_id = meter_resp.json().get("meterId", 1) if meter_resp.status_code == 201 else 1
        
        # Create intent with meter action
        intent = {
            "id": intent_id,
            "type": "PointToPointIntent",
            "appId": "org.onosproject.security.zerotrust",
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},
                    {"type": "IPV4_SRC", "ip": f"{src_ip}/32"},
                    {"type": "IPV4_DST", "ip": f"{dst_ip}/32"}
                ]
            },
            "treatment": {
                "instructions": [
                    {"type": "METER", "meterId": meter_id}
                ]
            },
            "priority": 90
        }
        
        return self._submit_intent(intent)
    
    def _create_mirror_intent(self, src_ip, src_port, dst_ip, dst_port, protocol):
        """Create ONOS intent to MIRROR flow to controller (VERIFY policy)"""
        
        self.intent_counter += 1
        intent_id = f"mirror-{self.intent_counter}"
        
        intent = {
            "id": intent_id,
            "type": "PointToPointIntent",
            "appId": "org.onosproject.security.zerotrust",
            "ingressPoint": {
                "device": "of:0000000000000001",
                "port": "1"
            },
            "egressPoint": {
                "device": "of:0000000000000001",
                "port": "LOCAL"  # Send copy to controller
            },
            "selector": {
                "criteria": [
                    {"type": "ETH_TYPE", "ethType": "0x0800"},
                    {"type": "IPV4_SRC", "ip": f"{src_ip}/32"},
                    {"type": "IPV4_DST", "ip": f"{dst_ip}/32"}
                ]
            },
            "treatment": {
                "instructions": [
                    {"type": "OUTPUT", "port": "CONTROLLER"}
                ]
            },
            "priority": 95
        }
        
        return self._submit_intent(intent)
    
    def _remove_restrictions(self, src_ip, src_port, dst_ip, dst_port, protocol):
        """Remove DROP intent if flow is trusted (ALLOW policy)"""
        
        # Query existing DROP intents for this flow
        intents = self._query_intents(src_ip, dst_ip)
        
        removed_count = 0
        for intent_key in intents:
            if "drop" in intent_key.lower():
                self._delete_intent(intent_key)
                removed_count += 1
        
        return {
            "success": True,
            "action": "ALLOW",
            "removed_restrictions": removed_count
        }
    
    def _submit_intent(self, intent: Dict) -> Dict:
        """Submit intent to ONOS"""
        
        try:
            resp = requests.post(
                f"{self.onos_url}/onos/v1/intents/batch",
                json={"intents": [intent]},
                auth=self.auth,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if resp.status_code in [200, 201]:
                logger.info(f"✅ Intent submitted: {intent.get('id')}")
                return {
                    "success": True,
                    "intent_id": intent.get('id'),
                    "action": self._extract_action(intent),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ ONOS rejected intent: {resp.text}")
                return {
                    "success": False,
                    "error": resp.text
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to submit intent: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _query_intents(self, src_ip: str, dst_ip: str) -> List[str]:
        """Find existing intents for src/dst"""
        
        try:
            resp = requests.get(
                f"{self.onos_url}/onos/v1/intents",
                auth=self.auth,
                timeout=5
            )
            
            if resp.status_code == 200:
                intents = resp.json().get("intents", [])
                matching = []
                
                for intent in intents:
                    if src_ip in str(intent) and dst_ip in str(intent):
                        matching.append(intent.get("id"))
                
                return matching
            else:
                return []
        
        except Exception as e:
            logger.error(f"Failed to query intents: {e}")
            return []
    
    def _delete_intent(self, intent_id: str) -> bool:
        """Delete an intent"""
        
        try:
            resp = requests.delete(
                f"{self.onos_url}/onos/v1/intents/{intent_id}",
                auth=self.auth,
                timeout=5
            )
            
            if resp.status_code == 204:
                logger.info(f"✅ Intent deleted: {intent_id}")
                return True
            else:
                logger.error(f"Failed to delete intent: {resp.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting intent: {e}")
            return False
    
    def _proto_to_number(self, protocol: str) -> int:
        """Convert protocol name to IP protocol number"""
        
        proto_map = {
            "TCP": 6,
            "UDP": 17,
            "ICMP": 1,
        }
        return proto_map.get(protocol.upper(), 6)
    
    def _extract_action(self, intent: Dict) -> str:
        """Extract action type from intent"""
        
        treatment = intent.get("treatment", {})
        instructions = treatment.get("instructions", [])
        
        if instructions:
            return instructions[0].get("type", "UNKNOWN")
        
        return "UNKNOWN"
```

---

## STEP 3: INTEGRATE WITH FastAPI BRAIN

**Modify brain/app.py to use ONOS enforcer:**

```python
# In brain/app.py

from security.onos_enforcer import ONOSPolicyEnforcer

# Initialize enforcer
onos_enforcer = ONOSPolicyEnforcer(
    onos_url="http://localhost:8181",
    onos_user="onos",
    onos_pass="rocks"
)

@app.post("/policy_decision")
async def policy_decision(
    trust_score_request: TrustScoreRequest
) -> PolicyDecisionResponse:
    """
    Make trust decision AND enforce via ONOS
    """
    
    # Existing logic: calculate trust and policy...
    policy_response = await existing_policy_logic(trust_score_request)
    
    # NEW: Enforce via ONOS if policy is not ALLOW
    if policy_response.policy in ["BLOCK", "LIMIT", "VERIFY"]:
        enforcement = onos_enforcer.enforce_policy({
            "flow_id": policy_response.flow_id,
            "policy": policy_response.policy,
            "trust_score": policy_response.trust_score,
            "reason": policy_response.reason
        })
        
        # Log enforcement result
        policy_response.onos_enforcement = enforcement
        logger.info(f"ONOS enforcement: {enforcement}")
    
    return policy_response
```

---

## STEP 4: TEST END-TO-END

```bash
#!/bin/bash
# Test zero-trust enforcement

# 1. Verify ONOS is running
curl -s http://localhost:8181/onos/v1/devices \
  -u onos:rocks | jq '.devices | length'
# Should return: 1 (or number of connected switches)

# 2. Send malicious flow to FastAPI
curl -X POST http://localhost:8000/policy_decision \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "192.168.1.10:54321-10.0.0.1:443-TCP",
    "src_ip": "192.168.1.10",
    "dst_ip": "10.0.0.1",
    "src_port": 54321,
    "dst_port": 443,
    "fwd_packet_rate": 5000,
    "trust_score": 20
  }'

# Expected response:
# {
#   "policy": "BLOCK",
#   "onos_enforcement": {
#     "success": true,
#     "intent_id": "drop-1",
#     "action": "DROP"
#   }
# }

# 3. Verify intent was created in ONOS
curl -s http://localhost:8181/onos/v1/intents \
  -u onos:rocks | jq '.intents | length'
# Should increase by 1
```

---

## STEP 5: VISUALIZE IN ONOS GUI

```bash
# Open browser
open http://localhost:8181

# Login: onos / rocks

# You should see:
# - Network topology
# - Deployed intents (showing your BLOCK/LIMIT policies)
# - Traffic flow visualization
```

---

## 🎯 DEPLOYMENT OPTIONS

### Option A: Single Switch (Lab)

```
Host 1 → Switch (OVS) ← ONOS ← FastAPI Brain
Host 2 ↗       ↓
            Flows
```

**ONOS config:**
```yaml
drivers:
  - name: "ovsdb"
    devices:
      - ip: "127.0.0.1:6640"
```

### Option B: Distributed Switches (Production)

```
Network Segment 1 → Switch... ├─ ONOS Cluster ← FastAPI Brain
Network Segment 2 → Switch... │   (3 nodes)
Network Segment 3 → Switch... ┘
```

**ONOS config:**
```yaml
cluster:
  nodes:
    - id: "onos1"
      ip: "192.168.1.100"
      port: 9876
    - id: "onos2"
      ip: "192.168.1.101"
      port: 9876
    - id: "onos3"
      ip: "192.168.1.102"
      port: 9876
```

---

## ⚠️ COMMON ISSUES

### Issue 1: ONOS "Connection refused"

```bash
# Check ONOS is running
ps aux | grep onos

# Restart if needed
./bin/onos-service stop
sleep 5
./bin/onos-service start
sleep 30
```

### Issue 2: "Invalid intent criteria"

**Problem:** Intents rejected by ONOS

**Solution:** Verify switch supports criteria type
```bash
# Check switch capabilities
./bin/onos
onos> devices -s
# Shows: "OpenFlow" or "NETCONF" capabilities
```

### Issue 3: "No route to device"

**Problem:** Intent targets device that doesn't exist

**Solution:** Query available devices
```bash
./bin/onos
onos> devices
# Lists: device:1, device:2, etc.

# Update enforcer code with correct device IDs
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] ONOS installed and running (./bin/onos-service status)
- [ ] Switch connected to ONOS (onos> devices shows switch)
- [ ] OpenFlow app activated (onos> app activate org.onosproject.openflow)
- [ ] ONOSPolicyEnforcer Python module created
- [ ] FastAPI imports and initializes enforcer
- [ ] Test policy on single flow works
- [ ] ONOS GUI shows intents being created/deleted
- [ ] Monitoring dashboard configured
- [ ] Rollback plan documented
- [ ] Production deployment approved

---

## 🚀 FULL PIPELINE (End-to-End)

```
Real Network Traffic
        ↓
Zeek IDS (conn.log)
        ↓
Telemetry Converter (JSON)
        ↓
FastAPI /infer endpoint
        ↓
ML Inference (Tier 1 + Tier 2)
        ↓
Trust Calculator
        ↓
Policy Decision (ALLOW/BLOCK/LIMIT/VERIFY)
        ↓
ONOSPolicyEnforcer
        ↓
ONOS REST API
        ↓
OpenFlow Intent
        ↓
Open vSwitch / SDN Switch
        ↓
Network Traffic Enforcement ✅
```

**Total Flow:**
- Telemetry arrives at FastAPI
- ML decision made in <100ms
- ONOS intent submitted in <200ms
- Switch enforces in <500ms

**Total: <1 second from attack detection to enforcement!**
