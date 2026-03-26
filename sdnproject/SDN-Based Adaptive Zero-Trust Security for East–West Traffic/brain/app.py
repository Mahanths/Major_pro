"""
FastAPI Main Application - Zero-Trust ML Brain
Listens on port 8000 for live telemetry from ONOS controller.
Provides inference endpoints for trust scoring and policy decisions.
"""

import logging
import sys
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np

# Import brain modules
from brain.feature_handler import FeatureHandler
from brain.hybrid_engine import HybridEngine
from brain.trust_calculator import TrustCalculator

# === Logging Configuration ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("brain.log"),
    ],
)
logger = logging.getLogger(__name__)

# === FastAPI App Initialization ===
app = FastAPI(
    title="Zero-Trust SDN Brain",
    description="ML-driven zero-trust security policy engine",
    version="0.1.0",
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify: ["http://localhost:8080", "http://localhost:5000"])
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)

# === Global Components ===
feature_handler = FeatureHandler()
ml_engine = HybridEngine()
trust_calculator = TrustCalculator()

request_counter = {"total": 0}


# === Pydantic Request/Response Models ===
class TelemetryRequest(BaseModel):
    """Incoming network telemetry from ONOS controller."""

    flow_id: str = Field(
        ..., description="Unique flow identifier (src_ip:dst_ip:sport:dport)"
    )
    src_ip: str = Field(..., description="Source IP address")
    dst_ip: str = Field(..., description="Destination IP address")
    src_port: int = Field(..., description="Source port")
    dst_port: int = Field(..., description="Destination port")
    src_mac: str = Field(..., description="Source MAC address")
    dst_mac: str = Field(..., description="Destination MAC address")

    # Flow statistics
    flow_duration: float = Field(..., description="Flow duration in seconds")
    fwd_packets: int = Field(..., description="Forward packets count")
    bwd_packets: int = Field(..., description="Backward packets count")
    fwd_bytes: int = Field(..., description="Forward bytes count")
    bwd_bytes: int = Field(..., description="Backward bytes count")

    # Advanced telemetry
    dst_ports: list = Field(default_factory=list, description="List of target ports")
    tcp_flags: list = Field(default_factory=list, description="TCP flags list")
    inter_arrival_times: list = Field(
        default_factory=list, description="Inter-arrival times in ms"
    )

    switch_id: Optional[str] = Field(default=None, description="OpenFlow switch ID")


class InferenceResponse(BaseModel):
    """ML inference result."""

    flow_id: str
    timestamp: str
    features: list = Field(..., description="8-feature ML vector")
    tier1_anomaly_score: float
    tier1_is_anomaly: bool
    tier2_triggered: bool
    tier2_malicious_probability: float
    final_malicious_probability: float
    inference_latency_ms: float
    models_ready: bool


class TrustScoreResponse(BaseModel):
    """Trust score calculation result."""

    flow_id: str
    timestamp: str
    trust_score: float
    old_trust: float
    policy: str
    penalty_malicious: float
    penalty_anomaly: float
    total_penalty: float
    threshold_block: float
    threshold_limit: float
    threshold_verify: float
    threshold_allow: float


class PolicyDecisionResponse(BaseModel):
    """Final policy decision for ONOS controller."""

    flow_id: str
    timestamp: str
    src_ip: str
    dst_ip: str
    src_mac: str
    dst_mac: str
    action: str = Field(..., description="ALLOW | VERIFY | LIMIT | BLOCK")
    trust_score: float
    confidence: float
    malicious_probability: float
    anomaly_detected: bool
    switch_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    uptime_seconds: float
    total_requests: int
    ml_models_ready: bool
    isolation_forest_loaded: bool
    xgboost_loaded: bool
    using_mock_models: bool


# === Helper Functions ===
def build_flow_key(src_ip: str, dst_ip: str, src_port: int, dst_port: int) -> str:
    """Build unique flow identifier."""
    return f"{src_ip}:{dst_ip}:{src_port}:{dst_port}"


# === API Endpoints ===
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Returns model and API status."""
    model_status = ml_engine.get_model_status()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        uptime_seconds=0.0,
        total_requests=request_counter["total"],
        ml_models_ready=model_status["engine_ready"],
        isolation_forest_loaded=model_status["isolation_forest_loaded"],
        xgboost_loaded=model_status["xgboost_loaded"],
        using_mock_models=model_status["using_mock_models"],
    )


@app.post("/infer", response_model=InferenceResponse)
async def inference_endpoint(telemetry: TelemetryRequest):
    """
    Primary inference endpoint.
    Extracts features from telemetry and runs Tier 1 + Tier 2 ML inference.
    """
    request_counter["total"] += 1

    try:
        # Validate telemetry
        if not feature_handler.validate_telemetry(telemetry.dict()):
            raise HTTPException(
                status_code=400,
                detail="Missing required telemetry fields",
            )

        # Extract 8 features
        features = feature_handler.extract_features(telemetry.dict())

        # ML Inference (Tier 1 + Tier 2)
        ml_result = ml_engine.infer(
            np.array(features),
            flow_metadata=telemetry.dict(),
        )

        return InferenceResponse(
            flow_id=telemetry.flow_id,
            timestamp=datetime.utcnow().isoformat(),
            features=features,
            tier1_anomaly_score=ml_result["tier1_anomaly_score"],
            tier1_is_anomaly=ml_result["tier1_is_anomaly"],
            tier2_triggered=ml_result["tier2_triggered"],
            tier2_malicious_probability=ml_result["tier2_malicious_probability"],
            final_malicious_probability=ml_result["final_malicious_probability"],
            inference_latency_ms=ml_result["inference_latency_ms"],
            models_ready=ml_result["models_ready"],
        )

    except Exception as e:
        logger.error(f"Inference error for flow {telemetry.flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/trust_score", response_model=TrustScoreResponse)
async def trust_score_endpoint(inference_result: InferenceResponse):
    """
    Calculate trust score based on ML inference results.
    Uses Trust Score Formula: T_new = λ*T_old - (α*P_mal) - (β*S_anom) + R_bonus
    """
    try:
        trust_result = trust_calculator.calculate_trust(
            flow_id=inference_result.flow_id,
            ml_malicious_probability=inference_result.final_malicious_probability,
            ml_anomaly_score=float(
                inference_result.tier1_anomaly_score
            ),  # Convert [-1,1] to [0,1]
            is_clean_traffic=False,
        )

        return TrustScoreResponse(
            flow_id=inference_result.flow_id,
            timestamp=datetime.utcnow().isoformat(),
            trust_score=trust_result["trust_score"],
            old_trust=trust_result["old_trust"],
            policy=trust_result["policy"],
            penalty_malicious=trust_result["penalty_malicious"],
            penalty_anomaly=trust_result["penalty_anomaly"],
            total_penalty=trust_result["total_penalty"],
            threshold_block=trust_result["threshold_block"],
            threshold_limit=trust_result["threshold_limit"],
            threshold_verify=trust_result["threshold_verify"],
            threshold_allow=trust_result["threshold_allow"],
        )

    except Exception as e:
        logger.error(f"Trust score error for {inference_result.flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Trust calculation failed: {str(e)}")


@app.post("/policy_decision", response_model=PolicyDecisionResponse)
async def policy_decision_endpoint(
    telemetry: TelemetryRequest, inference_and_trust: Dict
):
    """
    Make final policy decision to send back to ONOS controller.
    Maps trust score to action: ALLOW | VERIFY | LIMIT | BLOCK
    """
    try:
        trust_score = inference_and_trust.get("trust_score", 100.0)
        policy = inference_and_trust.get("policy", "ALLOW")
        malicious_prob = inference_and_trust.get("final_malicious_probability", 0.0)

        # Map policy to action
        action = policy  # Already in correct format

        return PolicyDecisionResponse(
            flow_id=telemetry.flow_id,
            timestamp=datetime.utcnow().isoformat(),
            src_ip=telemetry.src_ip,
            dst_ip=telemetry.dst_ip,
            src_mac=telemetry.src_mac,
            dst_mac=telemetry.dst_mac,
            action=action,
            trust_score=trust_score,
            confidence=1.0 - malicious_prob,
            malicious_probability=malicious_prob,
            anomaly_detected=inference_and_trust.get("tier1_is_anomaly", False),
            switch_id=telemetry.switch_id,
        )

    except Exception as e:
        logger.error(f"Policy decision error for {telemetry.flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Policy decision failed: {str(e)}")


@app.get("/status")
async def status():
    """Get detailed system status."""
    return {
        "service": "Zero-Trust SDN Brain",
        "version": "0.1.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "requests_processed": request_counter["total"],
        "ml_engine": ml_engine.get_model_status(),
        "trust_calculator": {
            "lambda_decay": TrustCalculator.LAMBDA_DECAY,
            "alpha_malicious": TrustCalculator.ALPHA_MALICIOUS,
            "beta_anomaly": TrustCalculator.BETA_ANOMALY,
        },
    }


# === Startup/Shutdown Events ===
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 80)
    logger.info("🧠 Zero-Trust SDN Brain Starting Up")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"ML Engine Status: {ml_engine.get_model_status()}")
    logger.info("Listening on 0.0.0.0:8000")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info(
        f"Brain shutting down. Processed {request_counter['total']} requests."
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
