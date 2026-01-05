"""
Delay Prediction Service - Load and use trained ML model for predictions.
"""
import joblib
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DelayPredictor:
    """Service for predicting shipment delays using trained ML model."""
    
    def __init__(self, model_dir: str = "models"):
        """
        Initialize predictor by loading trained model and encoders.
        
        Args:
            model_dir: Directory containing model artifacts
        """
        self.model_dir = Path(model_dir)
        self.model = None
        self.encoders = None
        self.feature_names = None
        self.metrics = None
        self._load_model()
    
    def _load_model(self):
        """Load model, encoders, and metadata from disk."""
        try:
            # Load model
            model_path = self.model_dir / "delay_prediction_model.pkl"
            self.model = joblib.load(model_path)
            logger.info(f"✅ Loaded delay prediction model from {model_path}")
            
            # Load encoders
            encoders_path = self.model_dir / "label_encoders.pkl"
            self.encoders = joblib.load(encoders_path)
            logger.info(f"✅ Loaded label encoders")
            
            # Load feature names
            features_path = self.model_dir / "feature_names.json"
            with open(features_path, 'r') as f:
                self.feature_names = json.load(f)
            
            # Load metrics
            metrics_path = self.model_dir / "model_metrics.json"
            with open(metrics_path, 'r') as f:
                self.metrics = json.load(f)
            
            logger.info(f"✅ Model ready - Accuracy: {self.metrics['accuracy']:.1%}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def extract_features(self, shipment_data: Dict[str, Any]) -> Optional[list]:
        """
        Extract features from shipment data for prediction.
        
        Args:
            shipment_data: Shipment information dict
            
        Returns:
            Feature vector ready for model.predict()
        """
        try:
            # Extract and encode categorical features
            origin_port = shipment_data.get("origin_port", "Unknown")
            destination_port = shipment_data.get("destination_port", "Unknown")
            carrier_name = shipment_data.get("vessel_name", "Unknown")  # Or carrier if available
            container_type = shipment_data.get("container_type", "40HC")
            
            # Encode categoricals
            try:
                origin_encoded = self.encoders["origin_port"].transform([origin_port])[0]
            except:
                origin_encoded = 0  # Unknown origin
            
            try:
                dest_encoded = self.encoders["destination_port"].transform([destination_port])[0]
            except:
                dest_encoded = 0  # Unknown destination
            
            try:
                carrier_encoded = self.encoders["carrier_name"].transform([carrier_name])[0]
            except:
                carrier_encoded = 0  # Unknown carrier
            
            try:
                container_encoded = self.encoders["container_type"].transform([container_type])[0]
            except:
                container_encoded = 0  # Default 40HC
            
            # Get temporal features
            if "etd" in shipment_data:
                try:
                    from dateutil.parser import parse
                    etd = parse(str(shipment_data["etd"]))
                    month = etd.month
                    day_of_week = etd.weekday()
                except:
                    month = datetime.now().month
                    day_of_week = datetime.now().weekday()
            else:
                month = datetime.now().month
                day_of_week = datetime.now().weekday()
            
            # Calculate seasonal and weekday factors
            seasonal_factors = {
                1: 0.05, 2: 0.15, 3: 0.10, 4: 0.02, 5: 0.00, 6: 0.00,
                7: 0.03, 8: 0.05, 9: 0.08, 10: 0.12, 11: 0.10, 12: 0.08
            }
            weekday_factors = {0: 0.02, 1: 0.01, 2: 0.00, 3: 0.01, 4: 0.03, 5: 0.05, 6: 0.05}
            
            seasonal_factor = seasonal_factors.get(month, 0.0)
            weekday_factor = weekday_factors.get(day_of_week, 0.0)
            
            # Other features
            carrier_reliability = 0.88  # Default average
            transit_days = 20  # Default
            risk_flag = int(shipment_data.get("risk_flag", False))
            base_delay_rate = 0.20  # Default average
            
            # Build feature vector in correct order
            features = [
                origin_encoded,
                dest_encoded,
                carrier_encoded,
                carrier_reliability,
                month,
                day_of_week,
                transit_days,
                container_encoded,
                risk_flag,
                base_delay_rate,
                seasonal_factor,
                weekday_factor,
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None
    
    def predict(self, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if shipment will be delayed.
        
        Args:
            shipment_data: Dictionary with shipment information
            
        Returns:
            {
                "will_delay": bool,
                "confidence": float (0-1),
                "delay_probability": float,
                "risk_factors": [str],
                "recommendation": str
            }
        """
        try:
            # Extract features
            features = self.extract_features(shipment_data)
            if features is None:
                return {
                    "success": False,
                    "error": "Could not extract features from shipment data"
                }
            
            # Make prediction
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]
            
            will_delay = bool(prediction == 1)
            delay_probability = float(probabilities[1])
            confidence = float(max(probabilities))
            
            # Analyze risk factors
            risk_factors = self._analyze_risk_factors(shipment_data, features)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                will_delay, confidence, delay_probability, risk_factors
            )
            
            result = {
                "success": True,
                "will_delay": will_delay,
                "confidence": round(confidence, 3),
                "delay_probability": round(delay_probability, 3),
                "risk_factors": risk_factors,
                "recommendation": recommendation,
                "model_accuracy": self.metrics["accuracy"]
            }
            
            logger.info(f"🔮 Prediction: {'DELAYED' if will_delay else 'ON-TIME'} (confidence: {confidence:.1%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_risk_factors(self, shipment_data: Dict[str, Any], features: list) -> list:
        """Identify key risk factors contributing to delay prediction."""
        risk_factors = []
        
        # Risk flag
        if shipment_data.get("risk_flag"):
            risk_factors.append("High-risk shipment flagged")
        
        # Seasonal factors
        if features[10] > 0.08:  # seasonal_factor index
            risk_factors.append("Peak shipping season (higher congestion)")
        
        # Weekend factor
        if features[11] > 0.03:  # weekday_factor index
            risk_factors.append("Weekend port operations (slower processing)")
        
        # Route complexity (high transit days)
        if features[6] > 30:  # transit_days index
            risk_factors.append("Long-haul route (higher delay risk)")
        
        # Carrier reliability
        if features[3] < 0.85:  # carrier_reliability index
            risk_factors.append("Carrier with lower reliability score")
        
        # If no specific factors, add generic one
        if not risk_factors:
            risk_factors.append("Historical route performance analysis")
        
        return risk_factors
    
    def _generate_recommendation(
        self,
        will_delay: bool,
        confidence: float,
        delay_probability: float,
        risk_factors: list
    ) -> str:
        """Generate actionable recommendation based on prediction."""
        
        if will_delay:
            if confidence > 0.80:
                return (
                    f"HIGH RISK: {delay_probability*100:.0f}% chance of delay. "
                    "Consider: (1) Notify customer proactively, (2) Explore alternative routing, "
                    "(3) Monitor closely for early intervention."
                )
            elif confidence > 0.60:
                return (
                    f"MODERATE RISK: {delay_probability*100:.0f}% chance of delay. "
                    "Recommend increased monitoring and customer communication."
                )
            else:
                return (
                    f"POSSIBLE DELAY: {delay_probability*100:.0f}% chance. "
                    "Continue normal monitoring."
                )
        else:
            if confidence > 0.90:
                return "Low delay risk - shipment on track for on-time delivery."
            else:
                return "Moderate confidence in on-time delivery - continue monitoring."


# Global predictor instance
_predictor = None

def get_delay_predictor() -> DelayPredictor:
    """Get or create global DelayPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DelayPredictor()
    return _predictor
