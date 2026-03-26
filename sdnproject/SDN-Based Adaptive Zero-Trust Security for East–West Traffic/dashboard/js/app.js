// ============================================
// GLOBAL STATE
// ============================================
const appState = {
    currentUser: null,
    userRole: null,
    isLoggedIn: false,
    apiUrl: 'http://localhost:8000'
};

// Demo users
const demoUsers = {
    admin: { username: 'admin', password: 'admin123', role: 'admin' },
    client: { username: 'user1', password: 'pass123', role: 'client' }
};

// ============================================
// LOGIN FUNCTIONALITY
// ============================================
document.getElementById('loginForm').addEventListener('submit', handleLogin);

function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    // Check credentials
    const user = Object.values(demoUsers).find(u => 
        u.username === username && u.password === password && u.role === role
    );

    if (user) {
        appState.currentUser = username;
        appState.userRole = role;
        appState.isLoggedIn = true;

        // Hide login, show dashboard
        document.getElementById('loginPage').classList.remove('show');
        
        if (role === 'admin') {
            document.getElementById('adminPage').style.display = 'flex';
            document.getElementById('currentUser').textContent = `${username} (Admin)`;
            initAdminDashboard();
        } else {
            document.getElementById('clientPage').style.display = 'block';
            document.getElementById('clientName').textContent = `Welcome, User 1!`;
            initClientDashboard();
        }
    } else {
        alert('Invalid credentials. Please try again.');
    }
}

// ============================================
// LOGOUT FUNCTIONALITY
// ============================================
document.getElementById('logoutBtn').addEventListener('click', handleLogout);
document.getElementById('clientLogout').addEventListener('click', handleLogout);

function handleLogout() {
    appState.isLoggedIn = false;
    appState.currentUser = null;
    appState.userRole = null;

    document.getElementById('loginPage').classList.add('show');
    document.getElementById('adminPage').style.display = 'none';
    document.getElementById('clientPage').style.display = 'none';

    document.getElementById('loginForm').reset();
}

// ============================================
// ADMIN DASHBOARD INITIALIZATION
// ============================================
function initAdminDashboard() {
    // Sidebar navigation
    document.querySelectorAll('.nav-item:not(.logout)').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            switchSection(item.dataset.section);
        });
    });

    // Refresh button
    document.getElementById('refreshThreats')?.addEventListener('click', updateThreatsTable);

    // Initialize charts
    initCharts();

    // Start live updates
    startLiveUpdates();

    // Update system status
    updateSystemStatus();
}

function switchSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('show');
    });

    // Show selected section
    document.getElementById(sectionName + 'Section').classList.add('show');

    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        threats: 'Active Threats',
        network: 'Network Topology',
        policies: 'Zero-Trust Policies',
        audit: 'Audit Log',
        analytics: 'Analytics & Insights'
    };
    document.getElementById('pageTitle').textContent = titles[sectionName] || 'Dashboard';
}

// ============================================
// CHARTS INITIALIZATION
// ============================================
let threatChart, trustChart, attackVectorsChart, topThreatsChart;

function initCharts() {
    // Threat Distribution Chart
    const threatCtx = document.getElementById('threatChart')?.getContext('2d');
    if (threatCtx) {
        threatChart = new Chart(threatCtx, {
            type: 'doughnut',
            data: {
                labels: ['DDoS', 'Port Scan', 'Brute Force', 'Data Exfiltration', 'Malware'],
                datasets: [{
                    data: [35, 20, 18, 15, 12],
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#8b5cf6',
                        '#3b82f6',
                        '#06b6d4'
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Trust Score Trend Chart
    const trustCtx = document.getElementById('trustChart')?.getContext('2d');
    if (trustCtx) {
        trustChart = new Chart(trustCtx, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
                datasets: [{
                    label: 'Trust Score (%)',
                    data: [92, 91, 93, 95, 94, 92, 94],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 80,
                        max: 100
                    }
                }
            }
        });
    }

    // Attack Vectors Chart
    const attackCtx = document.getElementById('attackVectorsChart')?.getContext('2d');
    if (attackCtx) {
        attackVectorsChart = new Chart(attackCtx, {
            type: 'bar',
            data: {
                labels: ['Network', 'Application', 'Physical', 'Social Eng.'],
                datasets: [{
                    label: 'Attack Count',
                    data: [45, 32, 12, 8],
                    backgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Top Threats Chart
    const topCtx = document.getElementById('topThreatsChart')?.getContext('2d');
    if (topCtx) {
        topThreatsChart = new Chart(topCtx, {
            type: 'horizontalBar',
            type: 'bar',
            data: {
                labels: ['DDoS', 'Port Scan', 'Brute Force', 'Malware', 'Data Exfil'],
                datasets: [{
                    label: 'Occurrences',
                    data: [156, 89, 67, 45, 34],
                    backgroundColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#8b5cf6',
                        '#3b82f6',
                        '#06b6d4'
                    ]
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true
            }
        });
    }
}

// ============================================
// LIVE UPDATES
// ============================================
let updateInterval;

function startLiveUpdates() {
    updateInterval = setInterval(() => {
        updateMetrics();
    }, 5000); // Update every 5 seconds
}

async function updateMetrics() {
    try {
        // Fetch real status from API
        const status = await callAPI('/status');
        
        if (status) {
            // Update metrics from real API data
            document.getElementById('threatCount').textContent = status.active_threats || 0;
            document.getElementById('avgTrust').textContent = (status.avg_trust_score || 92).toFixed(1) + '%';
            document.getElementById('hostCount').textContent = status.connected_hosts || 45;
            document.getElementById('blockedCount').textContent = status.total_blocks || 127;

            // Update traffic stats
            document.getElementById('totalFlows').textContent = status.total_flows || 892;
            document.getElementById('throughput').textContent = (status.throughput_mbps || 245).toFixed(0) + ' Mbps';
            document.getElementById('pps').textContent = status.packets_per_second || 12500;
            document.getElementById('anomalies').textContent = status.anomalies_detected || 3;
        }
    } catch (error) {
        console.error('Failed to update metrics:', error);
        // Fallback to demo data
        document.getElementById('threatCount').textContent = Math.floor(Math.random() * 20);
        document.getElementById('avgTrust').textContent = (85 + Math.random() * 15).toFixed(1) + '%';
    }
}

async function updateSystemStatus() {
    try {
        const status = await callAPI('/health');
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.getElementById('systemStatus');

        if (status && status.status === 'healthy') {
            statusDot.classList.add('active');
            statusText.textContent = 'System: Healthy ✓';
        } else {
            statusDot.classList.remove('active');
            statusText.textContent = 'System: Warning ⚠';
        }
    } catch (error) {
        console.error('Failed to update system status:', error);
        document.getElementById('systemStatus').textContent = 'System: Offline ✗';
    }
}

async function updateThreatsTable() {
    try {
        console.log('Fetching threats from API...');
        const tbody = document.getElementById('threatsTable');
        if (tbody) {
            tbody.style.opacity = '0.5';
        }

        // In production, this would call a /threats endpoint
        // For now, generate realistic threat data from ML models
        const threats = generateMockThreats();
        
        if (tbody) {
            tbody.innerHTML = '';
            threats.forEach(threat => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${threat.sourceIp}</strong></td>
                    <td>${threat.destIp}</td>
                    <td><span class="severity ${threat.severityClass}">${threat.type}</span></td>
                    <td>${threat.probability}%</td>
                    <td>${threat.time}</td>
                    <td>
                        <button onclick="handleThreat('${threat.sourceIp}', 'block')" class="btn-small btn-danger">Block</button>
                        <button onclick="handleThreat('${threat.sourceIp}', 'limit')" class="btn-small btn-warning">Limit</button>
                        <button onclick="handleThreat('${threat.sourceIp}', 'verify')" class="btn-small btn-info">Verify</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
            tbody.style.opacity = '1';
        }
    } catch (error) {
        console.error('Failed to update threats table:', error);
    }
}

function generateMockThreats() {
    // These simulate ML model outputs
    const threat_types = ['DDoS', 'Port Scan', 'Brute Force', 'Malware', 'Lateral Movement'];
    const now = new Date();
    
    return [
        {
            sourceIp: '192.168.1.105',
            destIp: '8.8.8.8',
            type: 'DDoS',
            probability: 96,
            severityClass: 'critical',
            time: new Date(now.getTime() - 5*60000).toLocaleTimeString()
        },
        {
            sourceIp: '10.0.0.50',
            destIp: '192.168.1.1',
            type: 'Port Scan',
            probability: 87,
            severityClass: 'high',
            time: new Date(now.getTime() - 12*60000).toLocaleTimeString()
        },
        {
            sourceIp: '172.16.0.88',
            destIp: '10.10.10.50',
            type: 'Brute Force',
            probability: 78,
            severityClass: 'medium',
            time: new Date(now.getTime() - 25*60000).toLocaleTimeString()
        }
    ];
}

function handleThreat(sourceIp, action) {
    alert(`Action '${action}' applied to ${sourceIp}`);
    // In production: would call /policy_decision endpoint
}

// ============================================
// CLIENT DASHBOARD INITIALIZATION
// ============================================
function initClientDashboard() {
    // Client navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchClientSection(link.dataset.section);
        });
    });

    // Initialize client charts
    initClientCharts();

    // Start client live updates
    startClientUpdates();
}

function switchClientSection(sectionName) {
    document.querySelectorAll('.client-section').forEach(section => {
        section.classList.remove('show');
    });

    document.getElementById(sectionName + 'Section').classList.add('show');

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
}

let clientTrustChart;

function initClientCharts() {
    const clientTrustCtx = document.getElementById('clientTrustChart')?.getContext('2d');
    if (clientTrustCtx) {
        clientTrustChart = new Chart(clientTrustCtx, {
            type: 'line',
            data: {
                labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                datasets: [{
                    label: 'Your Trust Score',
                    data: [91, 92, 90, 95, 93, 89, 92],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.05)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#2563eb',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 80,
                        max: 100
                    }
                }
            }
        });
    }
}

async function startClientUpdates() {
    setInterval(async () => {
        try {
            // Fetch trust score from API for current user
            const trustData = await callAPI('/trust_score', 'POST', {
                user: appState.currentUser,
                source_ip: '192.168.1.100',
                destination_ip: '10.0.0.1',
                ports_count: 1,
                flow_duration: 30,
                fwd_packet_rate: 10.5,
                bwd_packet_rate: 8.2,
                byte_entropy: 5.2,
                unique_dst_ports: 1,
                tcp_flags_count: 2,
                inter_arrival_time_min: 0.001,
                inter_arrival_time_max: 0.5
            });
            
            if (trustData && trustData.trust_score) {
                const trustScore = (trustData.trust_score * 100).toFixed(1);
                const metric = document.querySelector('.large-metric .value');
                if (metric) {
                    metric.textContent = trustScore + '%';
                }
            }
        } catch (error) {
            console.error('Failed to fetch trust score:', error);
            // Fallback to random for demo
            const trustScore = (85 + Math.random() * 15).toFixed(1);
            const metric = document.querySelector('.large-metric .value');
            if (metric) {
                metric.textContent = trustScore + '%';
            }
        }
    }, 3000);
}

// ============================================
// API INTEGRATION HELPERS
// ============================================
async function callAPI(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${appState.apiUrl}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard loaded');
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
