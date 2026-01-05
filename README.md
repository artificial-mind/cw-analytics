# CW Analytics Engine

**Purpose**: Centralized ML/AI and analytics service for the CW logistics platform.

## Architecture

```
cw-analytics-engine/
├── src/
│   ├── ml/                    # Machine learning models
│   │   ├── delay_predictor.py
│   │   ├── eta_predictor.py (future)
│   │   └── cost_optimizer.py (future)
│   ├── analytics/             # Analytics computations
│   │   ├── route_analytics.py
│   │   └── carrier_analytics.py
│   ├── training/              # Model training scripts
│   │   ├── train_delay_model.py
│   │   └── generate_training_data.py
│   └── server.py             # FastAPI server
├── models/                    # Trained model artifacts
├── data/                      # Training datasets
└── requirements.txt
```

## Features

### ML Models
- **Delay Prediction**: Predict shipment delays 48-72 hours in advance (81.5% accuracy)
- **ETA Prediction**: (Coming soon)
- **Cost Optimization**: (Coming soon)

### Analytics
- Route performance analysis
- Carrier reliability metrics
- Port congestion insights

## API Endpoints

### ML Predictions
- `POST /predict-delay` - Predict if shipment will be delayed
- `POST /predict-eta` - Predict accurate ETA (future)

### Analytics
- `GET /analytics/routes` - Route performance metrics
- `GET /analytics/carriers` - Carrier reliability stats
- `GET /analytics/ports` - Port congestion analysis

### Model Management
- `POST /train-model` - Retrain ML models
- `GET /model-info` - Get model metadata

## Setup

```bash
cd cw-analytics-engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python src/server.py
```

Server runs on: http://localhost:8002

## Adding New ML Models

1. Create model in `src/ml/your_model.py`
2. Create training script in `src/training/train_your_model.py`
3. Add API endpoint in `src/server.py`
4. Document in this README

## Integration

**MCP Server** (cw-ai-server) calls analytics-engine via HTTP:
```python
async def predictive_delay_detection(identifier: str):
    response = await http_client.post(
        "http://localhost:8002/predict-delay",
        json={"shipment_id": identifier}
    )
    return response.json()
```

**A2A Server** (cw-agents) can also call directly for complex workflows.

## Why Separate Service?

✅ **Scalability**: Run on GPU instances for heavy ML workloads  
✅ **Isolation**: ML dependencies don't affect other services  
✅ **Reusability**: Multiple services can use analytics APIs  
✅ **Maintainability**: Clear separation of concerns  
✅ **Performance**: Can cache predictions, scale horizontally
