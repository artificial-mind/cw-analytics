"""
CW Analytics Engine - FastAPI Server
Centralized ML/AI and analytics service for logistics platform.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import uvicorn
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ml.delay_predictor import DelayPredictor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CW Analytics Engine",
    description="ML/AI and analytics service for logistics platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ML model instances
delay_predictor: Optional[DelayPredictor] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class DelayPredictionRequest(BaseModel):
    """Request model for delay prediction."""
    shipment_data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "shipment_data": {
                    "id": "job-2025-001",
                    "origin_port": "Shanghai",
                    "destination_port": "Long Beach",
                    "vessel_name": "MAERSK LINE",
                    "etd": "2026-01-10T00:00:00",
                    "eta": "2026-02-05T00:00:00",
                    "risk_flag": False,
                    "container_type": "40HC"
                }
            }
        }


class DelayPredictionResponse(BaseModel):
    """Response model for delay prediction."""
    success: bool
    will_delay: Optional[bool] = None
    confidence: Optional[float] = None
    delay_probability: Optional[float] = None
    risk_factors: Optional[list] = None
    recommendation: Optional[str] = None
    model_accuracy: Optional[float] = None
    error: Optional[str] = None


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    model_name: str
    model_type: str
    accuracy: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    features: list
    trained_date: Optional[str] = None


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize ML models on startup."""
    global delay_predictor
    
    logger.info("🚀 Starting CW Analytics Engine...")
    
    try:
        # Load delay prediction model
        models_path = Path(__file__).parent.parent / "models"
        delay_predictor = DelayPredictor(model_dir=str(models_path))
        logger.info("✅ Delay prediction model loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        logger.warning("⚠️  Server starting without ML models - training may be required")
    
    logger.info("✅ Analytics Engine ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("👋 Shutting down Analytics Engine...")


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "CW Analytics Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "ml": ["/predict-delay"],
            "analytics": ["/analytics/routes", "/analytics/carriers"],
            "info": ["/model-info", "/health"]
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    models_loaded = delay_predictor is not None
    
    return {
        "status": "healthy" if models_loaded else "degraded",
        "models": {
            "delay_predictor": "loaded" if delay_predictor else "not loaded"
        }
    }


@app.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the delay prediction model."""
    if not delay_predictor:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return ModelInfoResponse(
        model_name="Delay Prediction Model",
        model_type="Random Forest Classifier",
        accuracy=delay_predictor.metrics.get("accuracy", 0.0),
        precision=delay_predictor.metrics.get("precision"),
        recall=delay_predictor.metrics.get("recall"),
        features=delay_predictor.feature_names,
        trained_date=None  # TODO: Add training date to metrics
    )


# ============================================================================
# ML Prediction Endpoints
# ============================================================================

@app.post("/predict-delay", response_model=DelayPredictionResponse)
async def predict_delay(request: DelayPredictionRequest):
    """
    Predict if a shipment will be delayed.
    
    Uses Random Forest classifier trained on historical shipment data
    to predict delays 48-72 hours in advance.
    
    Returns prediction with confidence score and risk factors.
    """
    if not delay_predictor:
        raise HTTPException(
            status_code=503,
            detail="Delay prediction model not loaded. Please train the model first."
        )
    
    logger.info(f"🔮 Predicting delay for shipment: {request.shipment_data.get('id', 'unknown')}")
    
    try:
        # Make prediction
        result = delay_predictor.predict(request.shipment_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Prediction failed"))
        
        return DelayPredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics Endpoints (Future)
# ============================================================================

@app.get("/analytics/routes")
async def get_route_analytics():
    """Get analytics for shipping routes."""
    # TODO: Implement route analytics
    return {
        "status": "coming_soon",
        "message": "Route analytics endpoint under development"
    }


@app.get("/analytics/carriers")
async def get_carrier_analytics():
    """Get analytics for carriers."""
    # TODO: Implement carrier analytics
    return {
        "status": "coming_soon",
        "message": "Carrier analytics endpoint under development"
    }


@app.get("/analytics/ports")
async def get_port_analytics():
    """Get analytics for ports."""
    # TODO: Implement port analytics
    return {
        "status": "coming_soon",
        "message": "Port analytics endpoint under development"
    }


# ============================================================================
# Model Training Endpoints (Future)
# ============================================================================

@app.post("/train-model")
async def train_delay_model():
    """Trigger model retraining."""
    # TODO: Implement async model training
    return {
        "status": "coming_soon",
        "message": "Model training endpoint under development"
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
