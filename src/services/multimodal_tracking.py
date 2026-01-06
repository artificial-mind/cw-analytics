"""
Multimodal Tracking Service
============================

Provides tracking across multiple transportation modes:
- Ocean shipping (port to port)
- Rail transport (port to inland terminal)
- Truck delivery (terminal to warehouse)

Features:
- Track complete journey from origin to destination
- View all transport legs (segments)
- Calculate progress percentage
- Identify handoff points between modes
- Show current location and status
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import query_shipments, query_transport_legs

class MultimodalTrackingService:
    """Service for tracking shipments across multiple transport modes"""
    
    def __init__(self):
        """Initialize multimodal tracking service"""
        pass
    
    def _calculate_progress(self, legs: List[Dict[str, Any]]) -> float:
        """Calculate journey completion percentage"""
        if not legs:
            return 0.0
        
        completed_legs = sum(1 for leg in legs if leg['status'] == 'completed')
        total_legs = len(legs)
        
        # Also consider partially completed current leg
        in_transit_legs = sum(1 for leg in legs if leg['status'] == 'in_transit')
        progress = ((completed_legs + (in_transit_legs * 0.5)) / total_legs) * 100
        
        return round(progress, 1)
    
    def _determine_current_mode_and_location(self, legs: List[Dict[str, Any]]) -> tuple:
        """Determine current transportation mode and location"""
        if not legs:
            return None, "Unknown"
        
        # Find the current active leg
        for leg in legs:
            if leg['status'] in ['in_transit', 'loading', 'unloading']:
                return leg['mode'], leg['from_location'] if leg['departed_at'] is None else "En route"
            
        # If all completed, at final destination
        if all(leg['status'] == 'completed' for leg in legs):
            last_leg = legs[-1]
            return last_leg['mode'], last_leg['to_location']
        
        # If all planned, at first location
        first_leg = legs[0]
        return first_leg['mode'], first_leg['from_location']
    
    def _identify_handoff_events(self, legs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify handoff points between transport modes"""
        handoffs = []
        
        for i in range(len(legs) - 1):
            current_leg = legs[i]
            next_leg = legs[i + 1]
            
            if current_leg['arrived_at']:
                handoffs.append({
                    "event": f"{current_leg['mode'].title()} to {next_leg['mode'].title()}",
                    "location": current_leg['to_location'],
                    "timestamp": current_leg['arrived_at']
                })
        
        return handoffs
    
    def track_multimodal_shipment(self, shipment_id: Optional[str] = None,
                                  job_number: Optional[str] = None,
                                  include_history: bool = True) -> Dict[str, Any]:
        """
        Track a shipment across multiple transportation modes
        
        Args:
            shipment_id: Internal shipment ID (database ID)
            job_number: Job/tracking number (e.g., "job-2025-001")
            include_history: Whether to include complete journey history
        
        Returns:
            Dictionary with multimodal tracking information
        """
        # Find the shipment
        filters = {}
        if job_number:
            filters['job_number'] = job_number
        
        shipments = query_shipments(filters)
        
        if not shipments:
            return {
                "error": "Shipment not found",
                "message": f"No shipment found matching: {job_number or shipment_id}"
            }
        
        shipment = shipments[0]
        shipment_db_id = shipment['id']
        
        # Get transport legs
        legs = query_transport_legs(shipment_db_id)
        
        if not legs:
            # No multimodal tracking data - return basic shipment info
            return {
                "shipment_id": shipment['job_number'],
                "container_number": shipment['container_number'],
                "status": shipment['status'],
                "origin": shipment['origin'],
                "destination": shipment['destination'],
                "current_mode": "unknown",
                "current_location": shipment['origin'] if shipment['status'] == 'loading' else shipment['destination'],
                "journey": [],
                "progress_percentage": 50.0 if shipment['status'] == 'in_transit' else 0.0,
                "handoff_events": [],
                "multimodal_data_available": False,
                "message": "No detailed multimodal tracking data available for this shipment"
            }
        
        # Calculate progress and current status
        progress = self._calculate_progress(legs)
        current_mode, current_location = self._determine_current_mode_and_location(legs)
        handoff_events = self._identify_handoff_events(legs)
        
        # Format journey legs
        journey = []
        for leg in legs:
            journey_leg = {
                "leg_number": leg['leg_number'],
                "mode": leg['mode'],
                "carrier": leg['carrier'],
                "vehicle": leg['vessel_or_vehicle'],
                "from": leg['from_location'],
                "to": leg['to_location'],
                "status": leg['status']
            }
            
            if leg['departed_at']:
                journey_leg['departed'] = leg['departed_at']
            if leg['arrived_at']:
                journey_leg['arrived'] = leg['arrived_at']
            if leg['eta']:
                journey_leg['eta'] = leg['eta']
            if leg['distance_km']:
                journey_leg['distance_km'] = leg['distance_km']
            
            journey.append(journey_leg)
        
        # Build response
        return {
            "shipment_id": shipment['job_number'],
            "container_number": shipment['container_number'],
            "status": shipment['status'],
            "origin": shipment['origin'],
            "destination": shipment['destination'],
            "current_mode": current_mode,
            "current_location": current_location,
            "journey": journey if include_history else [j for j in journey if j['status'] != 'completed'],
            "progress_percentage": progress,
            "handoff_events": handoff_events,
            "total_legs": len(legs),
            "completed_legs": sum(1 for leg in legs if leg['status'] == 'completed'),
            "multimodal_data_available": True,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_transport_modes(self) -> List[str]:
        """Get list of supported transport modes"""
        return ["ocean", "air", "rail", "truck", "barge"]

# Global service instance
_multimodal_tracking_service = None

def get_multimodal_tracking_service() -> MultimodalTrackingService:
    """Get or create multimodal tracking service instance"""
    global _multimodal_tracking_service
    if _multimodal_tracking_service is None:
        _multimodal_tracking_service = MultimodalTrackingService()
    return _multimodal_tracking_service
