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
from documents.generator_reportlab import get_document_generator
from services.vessel_tracking import get_vessel_tracking_service
from services.multimodal_tracking import get_multimodal_tracking_service
from services.container_tracking import get_container_tracking_service

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
document_generator = None
vessel_tracking_service = None
multimodal_tracking_service = None
container_tracking_service = None


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
    global delay_predictor, document_generator, vessel_tracking_service, multimodal_tracking_service, container_tracking_service
    
    logger.info("🚀 Starting CW Analytics Engine...")
    
    try:
        # Load delay prediction model
        models_path = Path(__file__).parent.parent / "models"
        delay_predictor = DelayPredictor(model_dir=str(models_path))
        logger.info("✅ Delay prediction model loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        logger.warning("⚠️  Server starting without ML models - training may be required")
    
    try:
        # Initialize document generator
        document_generator = get_document_generator()
        logger.info("✅ Document generator initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize document generator: {e}")
    
    try:
        # Initialize vessel tracking service
        vessel_tracking_service = get_vessel_tracking_service()
        logger.info("✅ Vessel tracking service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vessel tracking: {e}")
    
    try:
        # Initialize multimodal tracking service
        multimodal_tracking_service = get_multimodal_tracking_service()
        logger.info("✅ Multimodal tracking service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize multimodal tracking: {e}")
    
    try:
        # Initialize container tracking service
        container_tracking_service = get_container_tracking_service()
        logger.info("✅ Container tracking service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize container tracking: {e}")
    
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
            "documents": ["/generate-document"],
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
# Document Generation Endpoints
# ============================================================================

class DocumentGenerationRequest(BaseModel):
    """Request model for document generation."""
    document_type: str  # "BOL", "COMMERCIAL_INVOICE", "PACKING_LIST"
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "BOL",
                "data": {
                    "shipment_id": "job-2025-001",
                    "carrier_name": "MAERSK LINE",
                    "shipper_name": "ABC Corporation",
                    "shipper_address": "123 Export St",
                    "shipper_city": "Shanghai",
                    "shipper_country": "China",
                    "consignee_name": "XYZ Inc",
                    "consignee_address": "456 Import Ave",
                    "consignee_city": "Los Angeles",
                    "consignee_country": "USA",
                    "vessel_name": "MSC GULSUN",
                    "voyage_number": "123W",
                    "port_of_loading": "Shanghai",
                    "port_of_discharge": "Los Angeles",
                    "containers": [
                        {
                            "number": "MSCU1234567",
                            "seal_number": "SEAL001",
                            "type": "40HC",
                            "package_count": 500,
                            "package_type": "CARTONS",
                            "description": "Electronic Components",
                            "weight": 15000,
                            "volume": 67.5
                        }
                    ]
                }
            }
        }


@app.post("/generate-document")
async def generate_document(request: DocumentGenerationRequest):
    """
    Generate a logistics document (BOL, Invoice, or Packing List).
    
    Args:
        request: Document generation request with type and data
    
    Returns:
        Document generation result with file path and URL
    """
    if not document_generator:
        raise HTTPException(
            status_code=503,
            detail="Document generator not initialized"
        )
    
    try:
        doc_type = request.document_type.upper()
        logger.info(f"Generating document type: {doc_type}")
        
        if doc_type == "BOL" or doc_type == "BILL_OF_LADING":
            result = document_generator.generate_bill_of_lading(request.data)
        elif doc_type == "COMMERCIAL_INVOICE" or doc_type == "INVOICE":
            result = document_generator.generate_commercial_invoice(request.data)
        elif doc_type == "PACKING_LIST" or doc_type == "PKG":
            result = document_generator.generate_packing_list(request.data)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported document type: {doc_type}. Supported types: BOL, COMMERCIAL_INVOICE, PACKING_LIST"
            )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error during document generation")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in document generation endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {str(e)}"
        )


# ============================================================================
# Vessel Tracking Endpoints (Day 6 - Tool 12)
# ============================================================================

class VesselTrackRequest(BaseModel):
    """Request model for vessel tracking"""
    vessel_name: Optional[str] = None
    imo_number: Optional[str] = None
    mmsi: Optional[str] = None

@app.post("/api/vessel/track")
async def track_vessel(request: VesselTrackRequest):
    """
    Track a vessel in real-time using AIS data
    
    Args:
        request: Vessel identification (name, IMO, or MMSI)
    
    Returns:
        Real-time vessel position, speed, heading, and status
    """
    if not vessel_tracking_service:
        raise HTTPException(
            status_code=503,
            detail="Vessel tracking service not initialized"
        )
    
    if not any([request.vessel_name, request.imo_number, request.mmsi]):
        raise HTTPException(
            status_code=400,
            detail="At least one identifier required: vessel_name, imo_number, or mmsi"
        )
    
    try:
        result = vessel_tracking_service.track_vessel(
            vessel_name=request.vessel_name,
            imo_number=request.imo_number,
            mmsi=request.mmsi
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in vessel tracking endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Vessel tracking failed: {str(e)}"
        )

@app.get("/api/vessel/list")
async def list_vessels():
    """Get list of all trackable vessels"""
    if not vessel_tracking_service:
        raise HTTPException(
            status_code=503,
            detail="Vessel tracking service not initialized"
        )
    
    try:
        vessels = vessel_tracking_service.get_all_tracked_vessels()
        return {
            "success": True,
            "vessels": vessels,
            "count": len(vessels)
        }
    except Exception as e:
        logger.error(f"Error listing vessels: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list vessels: {str(e)}"
        )


@app.get("/api/shipment/{shipment_id}/multimodal-tracking")
async def track_multimodal_shipment(shipment_id: str):
    """
    Track a shipment across multiple transport modes (ocean, rail, truck).
    
    Args:
        shipment_id: Shipment/job number (e.g., job-2025-001)
    
    Returns:
        Detailed tracking information including:
        - Overall progress percentage
        - Current transport leg and mode
        - All transport legs (completed, in-progress, planned)
        - Handoff points and status
        - Current location and next destination
    """
    if not multimodal_tracking_service:
        raise HTTPException(
            status_code=503,
            detail="Multimodal tracking service not initialized"
        )
    
    try:
        logger.info(f"Tracking multimodal shipment: {shipment_id}")
        
        result = multimodal_tracking_service.track_multimodal_shipment(shipment_id=shipment_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multimodal tracking endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal tracking failed: {str(e)}"
        )


@app.get("/api/container/{container_number}/live-tracking")
async def track_container_live(container_number: str):
    """
    Track container with live IoT sensor data.
    
    Args:
        container_number: Container number (e.g., MAEU1234567)
    
    Returns:
        Live tracking data including:
        - GPS location (lat/lon)
        - Temperature monitoring (for reefer containers)
        - Humidity monitoring
        - Shock/impact events
        - Door open/close events
        - Battery level
        - Active alerts
    """
    if not container_tracking_service:
        raise HTTPException(
            status_code=503,
            detail="Container tracking service not initialized"
        )
    
    try:
        logger.info(f"Tracking container with live sensors: {container_number}")
        
        result = container_tracking_service.track_container_live(container_number)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in container tracking endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Container tracking failed: {str(e)}"
        )


@app.get("/api/container/list")
async def list_containers():
    """Get list of all containers with IoT sensors"""
    if not container_tracking_service:
        raise HTTPException(
            status_code=503,
            detail="Container tracking service not initialized"
        )
    
    try:
        containers = container_tracking_service.get_all_tracked_containers()
        return {
            "success": True,
            "containers": containers,
            "count": len(containers)
        }
    except Exception as e:
        logger.error(f"Error listing containers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list containers: {str(e)}"
        )


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
