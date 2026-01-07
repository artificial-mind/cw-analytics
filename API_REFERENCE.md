# CW Analytics Engine - API Reference

**Version:** 1.2.0  
**Base URL:** `http://localhost:8002`  
**Protocol:** REST API (FastAPI)

## Overview

The CW Analytics Engine provides centralized ML/AI and analytics services for the logistics platform, including:
- Predictive delay detection using machine learning
- Document generation (BOL, Commercial Invoice, Packing List)
- Analytics and reporting endpoints
- Customer communication and notifications
- Public tracking link generation
- Proactive delay warnings
- Real-time exception monitoring

---

## Endpoints

### Core Endpoints

#### `GET /`
**Description:** Root endpoint with service information  
**Response:** `200 OK`
```json
{
  "service": "CW Analytics Engine",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "model_info": "/model-info",
    "predict_delay": "/predict-delay",
    "generate_document": "/generate-document",
    "train_model": "/train-model"
  }
}
```

#### `GET /health`
**Description:** Health check endpoint  
**Response:** `200 OK`
```json
{
  "status": "healthy",
  "ml_model_loaded": true,
  "document_generator_loaded": true
}
```

---

### Machine Learning Endpoints

#### `GET /model-info`
**Description:** Get information about the deployed ML model  
**Response:** `200 OK` - `ModelInfoResponse`

```json
{
  "model_name": "DelayPredictor",
  "model_type": "RandomForestClassifier",
  "accuracy": 0.85,
  "precision": 0.82,
  "recall": 0.88,
  "features": [
    "origin_port_encoded",
    "destination_port_encoded",
    "vessel_encoded",
    "transit_days",
    "risk_flag"
  ],
  "trained_date": "2026-01-05"
}
```

#### `POST /predict-delay`
**Description:** Predict if a shipment will be delayed using ML model  
**Request Body:** `DelayPredictionRequest`

```json
{
  "shipment_data": {
    "id": "job-2025-001",
    "origin_port": "Shanghai",
    "destination_port": "Long Beach",
    "vessel_name": "MAERSK LINE",
    "etd": "2026-01-10T00:00:00",
    "eta": "2026-02-05T00:00:00",
    "risk_flag": false,
    "container_type": "40HC"
  }
}
```

**Response:** `200 OK` - `DelayPredictionResponse`

```json
{
  "success": true,
  "will_delay": false,
  "confidence": 0.78,
  "delay_probability": 0.22,
  "risk_factors": [
    "high_volume_route",
    "peak_season"
  ],
  "recommendation": "Monitor closely - moderate risk",
  "model_accuracy": 0.85
}
```

**Error Response:** `500 Internal Server Error`
```json
{
  "success": false,
  "error": "Model prediction failed: <error_message>"
}
```

#### `POST /train-model`
**Description:** Train or retrain the ML model with provided training data  
**Request Body:**

```json
{
  "training_data": [
    {
      "id": "job-001",
      "origin_port": "Shanghai",
      "destination_port": "Los Angeles",
      "vessel_name": "MAERSK",
      "transit_days": 25,
      "risk_flag": false,
      "was_delayed": false
    },
    // ... more training examples
  ],
  "labels": [0, 1, 0, 1, ...]  // Binary labels: 0 = no delay, 1 = delayed
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Model trained successfully",
  "accuracy": 0.87,
  "precision": 0.84,
  "recall": 0.89,
  "training_samples": 1000
}
```

---

### Document Generation Endpoints

#### `POST /generate-document`
**Description:** Generate logistics documents (BOL, Commercial Invoice, Packing List) as PDF  
**Request Body:** `DocumentGenerationRequest`

```json
{
  "document_type": "BOL",  // or "COMMERCIAL_INVOICE" or "PACKING_LIST"
  "data": {
    "shipment_id": "job-2025-001",
    "carrier_name": "MAERSK LINE",
    "vessel_name": "MAERSK ANTWERP",
    "voyage_number": "MA001",
    "port_of_loading": "Shanghai",
    "port_of_discharge": "Los Angeles",
    "shipper_name": "Acme Corp",
    "shipper_address": "123 Main St",
    "consignee_name": "Global Import Co",
    "consignee_address": "456 Ocean Ave",
    "containers": [
      {
        "number": "MSCU1234567",
        "type": "40HC",
        "seal_number": "SEAL123",
        "description": "Electronics",
        "weight": 15000,
        "package_count": 100
      }
    ]
  }
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "document_type": "BILL_OF_LADING",
  "document_number": "BOL-job-2025-001",
  "file_path": "/path/to/generated_documents/BOL_job-2025-001_20260105_123456.pdf",
  "document_url": "/documents/BOL_job-2025-001_20260105_123456.pdf",
  "file_size_kb": 2.54
}
```

**Document Types:**

1. **BOL (Bill of Lading)**
   - Required fields: `shipment_id`, `carrier_name`, `vessel_name`, `port_of_loading`, `port_of_discharge`, `shipper_name`, `consignee_name`, `containers`
   - Use case: Proof of shipment, receipt, and title document

2. **COMMERCIAL_INVOICE**
   - Required fields: `shipment_id`, `invoice_number`, `exporter_name`, `importer_name`, `line_items`, `currency`, `incoterms`
   - Use case: Customs clearance and international trade
   - Response includes: `total_amount`, `currency`

3. **PACKING_LIST**
   - Required fields: `shipment_id`, `packing_list_number`, `shipper_name`, `consignee_name`, `packages`
   - Use case: Detailed cargo manifest
   - Response includes: `total_packages`, `total_weight_kg`

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Invalid document_type. Must be one of: BOL, COMMERCIAL_INVOICE, PACKING_LIST"
}
```

---

### Analytics Endpoints

#### `GET /analytics/routes`
**Description:** Get analytics for shipping routes  
**Response:** `200 OK`

```json
{
  "message": "Route analytics - placeholder for future implementation",
  "total_routes": 0,
  "active_routes": 0
}
```

#### `GET /analytics/carriers`
**Description:** Get analytics for carriers  
**Response:** `200 OK`

```json
{
  "message": "Carrier analytics - placeholder for future implementation",
  "total_carriers": 0,
  "active_carriers": 0
}
```

#### `GET /analytics/ports`
**Description:** Get analytics for ports  
**Response:** `200 OK`

```json
{
  "message": "Port analytics - placeholder for future implementation",
  "total_ports": 0,
  "busiest_ports": []
}
```

---

## Data Models

### DelayPredictionRequest
```python
{
  "shipment_data": Dict[str, Any]  # Shipment data dictionary
}
```

### DelayPredictionResponse
```python
{
  "success": bool,
  "will_delay": Optional[bool],
  "confidence": Optional[float],  # 0.0 to 1.0
  "delay_probability": Optional[float],  # 0.0 to 1.0
  "risk_factors": Optional[List[str]],
  "recommendation": Optional[str],
  "model_accuracy": Optional[float],
  "error": Optional[str]
}
```

### DocumentGenerationRequest
```python
{
  "document_type": str,  # "BOL", "COMMERCIAL_INVOICE", or "PACKING_LIST"
  "data": Dict[str, Any]  # Document-specific data
}
```

### ModelInfoResponse
```python
{
  "model_name": str,
  "model_type": str,
  "accuracy": float,
  "precision": Optional[float],
  "recall": Optional[float],
  "features": List[str],
  "trained_date": Optional[str]
}
```

---

### Real-Time Tracking Endpoints (Day 6 - Tools 12-14)

#### `POST /api/vessel/track`
**Description:** Track vessel in real-time using AIS data  
**Request Body:** `VesselTrackRequest`

```json
{
  "vessel_name": "MAERSK",
  "imo_number": "1234567",
  "mmsi": "123456789"
}
```

**Response:** `200 OK` - Real-time vessel tracking data

```json
{
  "success": true,
  "data": {
    "vessel_name": "MAERSK SEALAND",
    "imo": "9632179",
    "mmsi": "220532000",
    "position": {
      "lat": 37.776995,
      "lon": -122.420063
    },
    "speed": 12.64,
    "heading": 273.0,
    "status": "Underway using engine",
    "next_port": "Oakland",
    "eta": "2025-01-25T14:00:00Z"
  }
}
```

#### `GET /api/shipment/{shipment_id}/multimodal-tracking`
**Description:** Track shipment across multiple transport modes (ocean, rail, truck)  
**Path Parameters:**
- `shipment_id` (string): Shipment or job number (e.g., "job-2025-001")

**Response:** `200 OK` - Multimodal journey tracking data

```json
{
  "success": true,
  "data": {
    "shipment_id": "job-2025-001",
    "status": "in_transit",
    "progress_percentage": 16.7,
    "current_mode": "ocean",
    "journey": [
      {
        "leg_number": 1,
        "mode": "ocean",
        "carrier": "MAERSK LINE",
        "from": "Shanghai Port",
        "to": "Los Angeles Port",
        "status": "in_transit",
        "eta": "2025-01-23T14:00:00Z",
        "distance_km": 11500.0
      }
    ],
    "total_legs": 3,
    "completed_legs": 0
  }
}
```

#### `GET /api/container/{container_number}/live-tracking`
**Description:** Track container with live IoT sensor data  
**Path Parameters:**
- `container_number` (string): Container number (e.g., "MAEU1234567")

**Response:** `200 OK` - Live container tracking with IoT sensors

```json
{
  "success": true,
  "data": {
    "container_number": "MAEU1234567",
    "container_type": "40HC Reefer",
    "battery_level": 87,
    "gps": {
      "latitude": 37.776995,
      "longitude": -122.420063,
      "accuracy_meters": 13
    },
    "temperature": {
      "temperature_celsius": -15.8,
      "setpoint_celsius": -18.0,
      "deviation": 2.2
    },
    "alerts": [
      {
        "type": "temperature_deviation",
        "severity": "medium",
        "message": "Temperature deviation: 2.2°C from setpoint"
      }
    ],
    "alert_count": 1
  }
}
```

---

### Customer Communication Endpoints (Day 7 - Tool 28)

#### `POST /api/notifications/send`
**Description:** Send status update notification to customer via email or SMS  
**Request Body:**
```json
{
  "shipment_id": "SHIP12345",
  "notification_type": "departed",
  "recipient_email": "customer@example.com",
  "recipient_phone": "+1234567890",
  "language": "en",
  "tracking_url": "https://track.cwlogistics.com/SHIP12345",
  "additional_data": {}
}
```

**Notification Types:**
- `departed`: Shipment has left origin
- `in_transit`: Update while shipment is moving
- `arrived`: Shipment arrived at destination
- `customs_cleared`: Cleared customs successfully
- `delivered`: Final delivery completed
- `delayed`: Delay detected
- `exception`: Issue requiring attention

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "success": true,
    "notification_id": "NOTIF-20260107-84f6596c",
    "shipment_id": "SHIP12345",
    "notification_type": "departed",
    "sent_at": "2026-01-07T06:16:32.638982Z",
    "channels": ["email"],
    "recipient_email": "customer@example.com",
    "recipient_phone": null,
    "language": "en",
    "message_preview": "Your shipment SHIP12345 has departed",
    "tracking_url": "https://track.cwlogistics.com/SHIP12345"
  }
}
```

**Supported Languages:**
- `en`: English
- `es`: Spanish
- `zh`: Chinese

**Error Response:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "shipment_id"],
      "msg": "Field required"
    }
  ]
}
```

#### `POST /api/tracking-link/generate` (Day 7 - Tool 29)
**Description:** Generate secure public tracking link for customer portal access  
**Request Body:**
```json
{
  "shipment_id": "SHIP12345",
  "expires_in_days": 30
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "tracking_url": "https://track.cwlogistics.com/a3f8b2c1-4d5e-6f7g-8h9i-0j1k2l3m4n5o",
    "token": "a3f8b2c1-4d5e-6f7g-8h9i-0j1k2l3m4n5o",
    "shipment_id": "SHIP12345",
    "expires_at": "2026-02-06T12:00:00Z",
    "created_at": "2026-01-07T12:00:00Z"
  },
  "message": "Public tracking link generated successfully"
}
```

**Features:**
- UUID4-based secure tokens (RFC 4122 compliant)
- 30-day default expiration (configurable)
- Database persistence for validation
- No authentication required for access
- Revocable via database deletion

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Shipment not found: SHIP12345"
}
```

#### `POST /api/notifications/proactive-delay-warning` (Day 7 - Tool 30)
**Description:** Proactively warn customers about potential delays based on ML predictions  
**Request Body:**
```json
{
  "shipment_id": "SHIP12345",
  "recipient_email": "customer@example.com",
  "recipient_phone": "+1234567890",
  "language": "en"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "success": true,
    "shipment_id": "SHIP12345",
    "warning_sent": true,
    "ml_confidence": 0.85,
    "risk_factors": [
      "Weather conditions",
      "Port congestion"
    ],
    "predicted_delay_hours": 24,
    "notification_id": "NOTIF-20260107-8fdb75c9",
    "sent_at": "2026-01-07T14:30:00Z"
  },
  "message": "Proactive warning sent for shipment SHIP12345"
}
```

**Logic:**
- Runs ML prediction on shipment
- Only sends notification if confidence > 70%
- Returns `warning_sent: false` if confidence ≤ 70%
- Includes risk factors and predicted delay hours
- Automatic notification with "delayed" type

**Mock ML Data (MVP):**
```json
{
  "will_delay": true,
  "confidence": 0.85,
  "risk_factors": ["Weather conditions", "Port congestion"],
  "predicted_delay_hours": 24
}
```

**Response when confidence ≤ 70%:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "shipment_id": "SHIP12345",
    "warning_sent": false,
    "ml_confidence": 0.65,
    "reason": "Confidence 65.0% below threshold 70%"
  },
  "message": "Proactive warning not needed for shipment SHIP12345"
}
```

---

### Exception Monitor Background Service (Day 7)

**Description:** Automated background service that runs every 5 minutes to detect shipment exceptions

**Monitoring Checks:**
1. **Delays > 24 hours** - Shipments significantly behind schedule
2. **ML Predictions > 70%** - High confidence delay predictions
3. **Temperature Deviations** - Reefer container temp outside threshold (±5°C)
4. **Geofence Violations** - Shipments outside expected route
5. **Missing Milestones > 72 hours** - Expected milestones not recorded

**A2A Integration:**
- Automatically notifies Exception Crew via A2A Protocol
- Sends to: `http://localhost:9000/message:send`
- Skill: `handle-exception`
- Includes exception details: type, severity, shipment_id

**Database Logging:**
- Table: `exception_monitor_runs`
- Fields: `run_timestamp`, `exceptions_found`, `shipments_checked`, `notifications_sent`, `run_duration_ms`
- Indexed by: `run_timestamp`

**Service Lifecycle:**
- **Startup:** Automatically starts with Analytics Engine
- **Interval:** 5 minutes between cycles
- **Shutdown:** Gracefully stops with server shutdown

**Query Monitoring History:**
```sql
SELECT * FROM exception_monitor_runs 
ORDER BY run_timestamp DESC 
LIMIT 10;
```

**Example Log Entry:**
```json
{
  "run_timestamp": "2026-01-07T21:20:25.520328",
  "exceptions_found": 3,
  "shipments_checked": 8,
  "notifications_sent": 3,
  "run_duration_ms": 245
}
```

**Exception Types:**
- `delay`: Shipment delayed beyond threshold
- `ml_prediction`: High ML confidence for delay
- `temperature_deviation`: Reefer temp outside range
- `geofence_violation`: Route deviation
- `missing_milestone`: Overdue milestone

**Severity Levels:**
- `high`: Immediate attention required
- `medium`: Attention needed soon
- `low`: Informational

---

## Error Handling

All endpoints follow standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

Error responses include a `detail` field with error description:
```json
{
  "detail": "Error message here"
}
```

---

## Setup & Configuration

### Starting the Server

```bash
cd cw-analytics-engine
python start_server.py
```

Server runs on: `http://0.0.0.0:8002`

### Environment Variables

- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8002`)
- `DOCUMENT_OUTPUT_DIR`: Directory for generated PDFs (default: `generated_documents/`)

### Dependencies

- FastAPI
- Uvicorn
- scikit-learn
- pandas
- ReportLab (PDF generation)
- Jinja2
- Pillow

---

## Usage Examples

### cURL Examples

**Predict Delay:**
```bash
curl -X POST http://localhost:8002/predict-delay \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_data": {
      "id": "job-2025-001",
      "origin_port": "Shanghai",
      "destination_port": "Los Angeles",
      "vessel_name": "MAERSK LINE",
      "etd": "2026-01-10T00:00:00",
      "eta": "2026-02-05T00:00:00"
    }
  }'
```

**Generate BOL:**
```bash
curl -X POST http://localhost:8002/generate-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "BOL",
    "data": {
      "shipment_id": "job-2025-001",
      "carrier_name": "MAERSK",
      "vessel_name": "MAERSK SHIP",
      "port_of_loading": "Shanghai",
      "port_of_discharge": "Los Angeles",
      "shipper_name": "Acme Corp",
      "consignee_name": "Import Co",
      "containers": [{"number": "MSCU1234567", "type": "40HC"}]
    }
  }'
```

### Python Examples

```python
import httpx

# Predict delay
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8002/predict-delay",
        json={
            "shipment_data": {
                "id": "job-2025-001",
                "origin_port": "Shanghai",
                "destination_port": "Los Angeles"
            }
        }
    )
    result = response.json()
    print(f"Will delay: {result['will_delay']}")
    print(f"Confidence: {result['confidence']}")

# Generate document
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8002/generate-document",
        json={
            "document_type": "BOL",
            "data": {...}
        }
    )
    result = response.json()
    print(f"Document URL: {result['document_url']}")
```

---

## Notes

- All datetime fields use ISO 8601 format
- Generated documents are saved to `generated_documents/` directory
- ML model is loaded on server startup
- Document generator supports BOL, Commercial Invoice, and Packing List formats
- PDF generation uses ReportLab for professional formatting

---

## Version History

- **1.1.0** (2026-01-06): Added real-time tracking endpoints (vessel, multimodal, container) - Day 6 Priority 1
- **1.0.0** (2026-01-05): Initial release with ML delay prediction and document generation
