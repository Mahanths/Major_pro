#!/bin/bash

# ============================================================================
# ZERO-TRUST SYSTEM - QUICK START TEST RUNBOOK
# Run this script to test the entire system end-to-end TODAY
# ============================================================================

set -e  # Exit on error

PROJECT_ROOT="/home/mahanth-s/sdnproject/SDN-Based Adaptive Zero-Trust Security for East–West Traffic"
cd "$PROJECT_ROOT"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🧪 ZERO-TRUST SDN SYSTEM - QUICK START TEST"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# ============================================================================
# PREPARATION: Install dependencies (one-time)
# ============================================================================

echo "📦 STEP 1: Installing Python dependencies..."
echo "────────────────────────────────────────────────────────────────────────────────"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r brain/requirements.txt
echo "✓ Dependencies installed"

# ============================================================================
# TEST 1: Unit Tests (5 minutes)
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST 1️⃣  - UNIT TESTS (Feature Extraction, ML, Trust Calc)"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

python test_system.py --test unit

# ============================================================================
# TEST 2: Integration Tests (5 minutes)
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST 2️⃣  - INTEGRATION TESTS (End-to-End Pipeline)"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

python test_system.py --test integration

# ============================================================================
# TEST 3: Attack Simulation Tests (10 minutes)
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "TEST 3️⃣  - ATTACK SIMULATION (SYN Flood, Port Scan, Data Exfil)"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

python test_system.py --test attacks

# ============================================================================
# PHASE 2: Generate Training Data & Train Models (10 minutes)
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "PHASE 2️⃣  - GENERATE TRAINING DATA"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

mkdir -p training_data
echo "Generating synthetic dataset (1000 normal + 1000 attack flows)..."
python training/synthetic_data_generator.py \
    --output training_data/training_dataset.csv \
    --normal 1000 \
    --attacks 1000

# ============================================================================
# PHASE 3: Train ML Models (5-10 minutes)
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "PHASE 3️⃣  - TRAIN ML MODELS"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

echo "Training Isolation Forest + XGBoost..."
python training/train_models.py \
    --dataset training_data/training_dataset.csv \
    --model-dir brain/models

# ============================================================================
# VERIFY: Check if models loaded
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ VERIFICATION: Models Trained"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

if [ -f "brain/models/isolation_forest_model.pkl" ]; then
    echo "✓ Isolation Forest model trained: $(du -h brain/models/isolation_forest_model.pkl | cut -f1)"
else
    echo "✗ Isolation Forest model NOT found"
    exit 1
fi

if [ -f "brain/models/xgboost_model.pkl" ]; then
    echo "✓ XGBoost model trained: $(du -h brain/models/xgboost_model.pkl | cut -f1)"
else
    echo "✗ XGBoost model NOT found"
    exit 1
fi

# ============================================================================
# NEXT STEPS
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🎉 SUCCESS! Zero-Trust System is Ready"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  START THE FASTAPI BRAIN (Terminal 1):"
echo "   cd '$PROJECT_ROOT'"
echo "   source venv/bin/activate"
echo "   uvicorn brain/app:app --host 0.0.0.0 --port 8000"
echo ""
echo "2️⃣  TEST ENDPOINTS (Terminal 2):"
echo "   # Check health"
echo "   curl http://localhost:8000/health"
echo ""
echo "   # Send normal traffic"
echo "   curl -X POST http://localhost:8000/infer \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"flow_id\": \"192.168.1.10:192.168.1.20:50000:443\", ...}'"
echo ""
echo "3️⃣  SEND ATTACK TELEMETRY:"
echo "   # Attack telemetry with high packet rate"
echo "   curl -X POST http://localhost:8000/infer \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"flow_id\": \"10.0.0.100:192.168.1.50:50000:443\",\"flow_duration\": 5.0,\"fwd_packets\": 50000, ...}'"
echo ""
echo "✅ YOU NOW HAVE:"
echo "   • Real trained ML models (not mocks)"
echo "   • FastAPI brain ready to receive telemetry"
echo "   • 9 unit + integration + attack tests passing"
echo "   • Ready for ONOS integration (Phase 4)"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
