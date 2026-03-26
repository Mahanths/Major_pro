# 🎯 Zero-Trust SDN Security Dashboard

## Overview

A comprehensive web-based dashboard for managing and monitoring the Zero-Trust SDN adaptive security system. The dashboard provides role-based interfaces for **Admins** and **Clients** with real-time threat monitoring, policy management, and trust score tracking.

---

## 📊 Dashboard Features

### **ADMIN DASHBOARD** (Full Control)

#### 1. **Dashboard (Home)**
- **KPI Cards**: Real-time metrics
  - Active Threats Count
  - Average Trust Score
  - Connected Hosts
  - Blocked Flows
- **Charts**:
  - Threat Distribution (24h)
  - Trust Score Trend
- **Traffic Analysis**: Live network statistics
  - Total Flows
  - Throughput
  - Packets/sec
  - Anomalies Detected

#### 2. **Threats**
- Real-time threat table with details:
  - Timestamp
  - Source & Destination IP
  - Threat Type (DDoS, Port Scan, Brute Force, etc.)
  - Severity (CRITICAL, HIGH, MEDIUM)
  - Trust Score of attachment
- **Action Buttons**:
  - **Block**: Immediately block the source
  - **Limit**: Rate limit the traffic
  - **Verify**: Request additional verification

#### 3. **Network**
- Network topology overview
  - Active switches: 8
  - Active links: 24
  - Network Health: 98%
- Connected devices list
  - Switches status (Online/Offline)
  - Hosts status (Online/Offline)

#### 4. **Policies**
- Zero-Trust policy management
- View all active policies
- Columns:
  - Policy Name
  - Type (Security/Access)
  - Priority (1-10)
  - Status (Active/Inactive)
  - Flows Matched
- **Actions**:
  - Edit policies
  - Delete policies
  - Create new policies

#### 5. **Audit Log**
- Complete audit trail of all system actions
- Columns:
  - Timestamp
  - Event (Threat Blocked, Policy Applied, etc.)
  - User
  - Source
  - Status (Success/Failed)
  - Details
- Filterable by date

#### 6. **Analytics**
- Advanced analytics and insights
- **Charts**:
  - Attack Vectors breakdown
  - Top Threats by occurrence count
- Trend analysis and reports

---

### **CLIENT DASHBOARD** (Limited Access)

#### 1. **My Connections**
- **Personal Status Cards**:
  - My Trust Score (%)
  - Connection Status (Connected/Offline)
  - Network Access Level (Full/Limited/Restricted)
- **Active Flows Table**:
  - Destination IP:Port
  - Protocol (UDP, TCP, DoH, Encrypted, etc.)
  - Status (Allowed/Blocked/Verified)
  - Duration of connection
  - Data transferred

#### 2. **Trust Reports**
- **Weekly Trust Summary** Chart
  - Trust score trend over time
  - Average trust score
  - Best day analysis
  - Risky actions count
  - Policy violations count
- **Connection Quality Metrics**:
  - Average Latency (ms)
  - Packet Loss (%)
  - Jitter (ms)

#### 3. **History**
- Connection history table
- Columns:
  - Date & Time
  - Action (Connection Request, DNS Query, VPN)
  - Destination
  - Result (Allowed/Blocked/Verified)
  - Trust Score at time

---

## 🚀 How to Use

### **Setup & Running**

#### **Option 1: Using Python Server**
```bash
cd dashboard
python3 server.py
# Access at http://localhost:5000
```

#### **Option 2: Using Any Web Server**
```bash
# Using Python (Built-in)
cd dashboard
python3 -m http.server 5000

# Using Node.js http-server
npm install -g http-server
cd dashboard
http-server -p 5000

# Using PHP
cd dashboard
php -S localhost:5000
```

### **Demo Login Credentials**

**Admin Access:**
- Username: `admin`
- Password: `admin123`
- Role: Admin

**Client Access:**
- Username: `user1`
- Password: `pass123`
- Role: Client

---

## 📋 Admin Guide

### **Monitoring Threats**
1. Go to **Threats** tab
2. View real-time threat list
3. Use color-coded severity:
   - 🔴 **CRITICAL** (Red): Immediate action needed
   - 🟠 **HIGH** (Orange): Investigate soon
   - 🟡 **MEDIUM** (Yellow): Monitor closely
4. Take action:
   - Click **Block** to prevent traffic
   - Click **Limit** for rate limiting
   - Click **Verify** to challenge the source

### **Understanding KPIs**
- **Active Threats**: Current threats detected by ML models
- **Trust Score**: Overall network health (0-100%)
- **Connected Hosts**: Live devices on network
- **Blocked Flows**: Flows blocked by policies

### **Analyzing Trends**
1. Go to **Analytics** tab
2. View attack vectors and top threats
3. Identify patterns:
   - Most common attack type
   - Time-based trends
   - Source patterns

### **Managing Policies**
1. Go to **Policies** tab
2. View all active policies with match count
3. Edit/Delete as needed
4. Add new policy (Button at top)

---

## 👤 Client Guide

### **Checking Your Trust Score**
1. Login with client credentials
2. "My Connections" tab shows score
3. Color-coded:
   - 🟢 Excellent (90-100%)
   - 🟡 Good (70-89%)
   - 🔴 Low (<70%)

### **Monitoring Your Connections**
1. Check "Active Network Flows" table
2. See:
   - What destinations you're connecting to
   - Whether they're **Allowed**, **Blocked**, or **Verified**
   - How long the connection has been active
   - Data transferred

### **Reading Trust Reports**
1. Go to "Trust Reports" tab
2. View weekly trend chart
3. Check connection quality metrics
4. Understand if your behavior is trustworthy

### **Reviewing History**
1. Go to "History" tab
2. See past 30 days of connections
3. Understand trust score changes
4. Identify patterns

---

## 🔄 Integration with AI Brain API

### **API Endpoints Called**
The dashboard can integrate with the FastAPI Brain:
- `GET http://localhost:8000/health` - System health check
- `POST http://localhost:8000/infer` - Raw ML inference
- `POST http://localhost:8000/trust_score` - Calculate trust
- `POST http://localhost:8000/policy_decision` - Get action

### **Data Flow**
```
Network Traffic
    ↓
ONOS Controller (port 8181)
    ↓ sends telemetry
AI Brain FastAPI (port 8000)
    ↓ calculates scores
Dashboard (port 5000)
    ↓ displays results
Admin / Client views
```

---

## 🎨 Dashboard Components Explained

### **Color Coding**
- 🔵 **Blue**: Primary, Normal/Good
- 🟢 **Green**: Success, Allowed, Good
- 🟡 **Yellow**: Warning, Medium Risk
- 🟠 **Orange**: High Risk/Threat
- 🔴 **Red**: Critical/Blocked

### **Status Indicators**
- Pulsing green dot: System healthy & online
- Pulsing red dot: System warning/issue
- Offline devices: Grayed out status

### **Charts**
- **Doughnut Chart**: Distribution (e.g., threat types)
- **Line Chart**: Trends over time (e.g., trust score)
- **Bar Chart**: Comparisons (e.g., attack count)

---

## ⚙️ Configuration

### **Change Dashboard Port**
```bash
python3 dashboard/server.py 8080  # Use port 8080 instead
```

### **Connect to Real API**
Edit `js/app.js`:
```javascript
const appState = {
    apiUrl: 'http://your-api-server:8000'  // Change this
};
```

### **Add More Users**
Edit `js/app.js`:
```javascript
const demoUsers = {
    admin: { username: 'admin', password: 'admin123', role: 'admin' },
    client: { username: 'user1', password: 'pass123', role: 'client' },
    // Add more users here
};
```

---

## 🔐 Real-World Deployment

### **For Production**

#### **1. Admin Dashboard**
- Multi-admin support with LDAP/AD auth
- Real-time threat feeds
- Policy templates
- Compliance reporting
- Dashboard customization

#### **2. Client Portal**
- Self-service account management
- Ticket system for access requests
- Device management
- Usage analytics

#### **3. Security Enhancements**
- HTTPS/SSL certificate
- Multi-factor authentication
- Session timeout
- Audit logging of admin actions
- Role-based access control (RBAC)

#### **4. Integration**
- Connect to actual ONOS controller (8181)
- Connect to actual AI Brain API (8000)
- Integrate with SIEM (Splunk, ELK)
- Connect to identity provider (OAuth, SAML)

---

## 📱 Responsive Design

Dashboard is fully responsive:
- ✅ Desktop (1920px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (below 768px)

---

## 🐛 Troubleshooting

### **Dashboard won't load**
```bash
# Check if server is running
curl http://localhost:5000

# Check firewall
sudo ufw allow 5000
```

### **Can't reach API**
```bash
# Check if AI Brain is running
curl http://localhost:8000/health

# CORS issue? Add to FastAPI:
# from fastapi.middleware.cors import CORSMiddleware
```

### **Charts not showing**
- Check browser console for errors
- Verify Chart.js is loaded
- Check data format

---

## 📞 Support

For issues or suggestions:
1. Check browser console (F12)
2. Check server logs
3. Review admin guide above

---

## 📝 File Structure

```
dashboard/
├── index.html           # Main HTML file
├── css/
│   └── style.css       # Styling (1000+ lines)
├── js/
│   └── app.js          # JavaScript logic
├── server.py           # Local server
└── README.md           # This file
```

---

## 🚀 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Custom dashboard layouts
- [ ] Export reports (PDF, CSV)
- [ ] Mobile app
- [ ] Email alerts
- [ ] Slack integration
- [ ] Machine learning insights
- [ ] Predictive threat detection

---

**Version:** 1.0  
**Last Updated:** March 26, 2026  
**Status:** Ready for Production
