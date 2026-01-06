"""
Vessel Tracking Service
=======================

Provides real-time vessel tracking using AIS (Automatic Identification System) data.
For Day 6, we use mock data. In production, this would integrate with:
- MarineTraffic API
- VesselFinder API
- AIS data providers

Features:
- Track vessels by name or IMO number
- Get real-time position, speed, heading
- Calculate ETA to next port
- Historical position tracking
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import math

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import query_vessel_positions, insert_vessel_position

class VesselTrackingService:
    """Service for real-time vessel tracking"""
    
    def __init__(self):
        """Initialize vessel tracking service"""
        self.mock_vessels = self._init_mock_vessels()
    
    def _init_mock_vessels(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock vessel database"""
        return {
            "MAERSK SEALAND": {
                "imo": "9321483",
                "mmsi": "235012345",
                "type": "Container Ship",
                "flag": "Denmark",
                "dwt": 170794,
                "base_lat": 37.7749,
                "base_lon": -122.4194,
                "base_speed": 12.5,
                "base_heading": 270
            },
            "MSC GULSUN": {
                "imo": "9839030",
                "mmsi": "235098765",
                "type": "Container Ship",
                "flag": "Liberia",
                "dwt": 232618,
                "base_lat": 34.0522,
                "base_lon": -118.2437,
                "base_speed": 0.0,
                "base_heading": 0
            },
            "EVER GIVEN": {
                "imo": "9811000",
                "mmsi": "235055566",
                "type": "Container Ship",
                "flag": "Panama",
                "dwt": 220940,
                "base_lat": 1.2921,
                "base_lon": 103.8558,
                "base_speed": 15.3,
                "base_heading": 90
            },
            "CMA CGM ANTOINE": {
                "imo": "9454436",
                "mmsi": "235077788",
                "type": "Container Ship",
                "flag": "France",
                "dwt": 185000,
                "base_lat": 31.2304,
                "base_lon": 121.4737,
                "base_speed": 14.2,
                "base_heading": 180
            }
        }
    
    def _calculate_position_delta(self, speed: float, heading: float, hours: float = 0.1) -> tuple:
        """Calculate position change based on speed and heading"""
        # Convert speed from knots to km/h
        speed_kmh = speed * 1.852
        
        # Calculate distance traveled
        distance_km = speed_kmh * hours
        
        # Convert heading to radians
        heading_rad = math.radians(heading)
        
        # Calculate lat/lon delta (approximate)
        lat_delta = (distance_km / 111.0) * math.cos(heading_rad)  # 111 km per degree latitude
        lon_delta = (distance_km / 111.0) * math.sin(heading_rad)
        
        return lat_delta, lon_delta
    
    def _generate_mock_position(self, vessel_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock real-time position with slight variations"""
        # Add small random variations to simulate movement
        lat_variation = random.uniform(-0.01, 0.01)
        lon_variation = random.uniform(-0.01, 0.01)
        speed_variation = random.uniform(-0.5, 0.5)
        heading_variation = random.uniform(-5, 5)
        
        current_lat = vessel_info['base_lat'] + lat_variation
        current_lon = vessel_info['base_lon'] + lon_variation
        current_speed = max(0, vessel_info['base_speed'] + speed_variation)
        current_heading = (vessel_info['base_heading'] + heading_variation) % 360
        
        # Determine status based on speed
        if current_speed < 0.5:
            status = "At anchor" if current_speed < 0.1 else "Moored"
        elif current_speed < 5:
            status = "Slow speed"
        else:
            status = "Underway using engine"
        
        # Mock next port and ETA
        next_ports = {
            "MAERSK SEALAND": ("Oakland", "2025-01-25T14:00:00Z"),
            "MSC GULSUN": ("Los Angeles", "2025-01-20T10:00:00Z"),
            "EVER GIVEN": ("Singapore", "2025-01-19T08:00:00Z"),
            "CMA CGM ANTOINE": ("Shanghai", "2025-01-22T16:00:00Z")
        }
        
        return {
            "latitude": round(current_lat, 6),
            "longitude": round(current_lon, 6),
            "speed": round(current_speed, 2),
            "heading": round(current_heading, 1),
            "status": status,
            "next_port": next_ports.get(vessel_info.get('vessel_name'), ("Unknown", None))[0],
            "eta": next_ports.get(vessel_info.get('vessel_name'), ("Unknown", None))[1]
        }
    
    def track_vessel(self, vessel_name: Optional[str] = None, 
                    imo_number: Optional[str] = None,
                    mmsi: Optional[str] = None) -> Dict[str, Any]:
        """
        Track a vessel by name, IMO number, or MMSI
        
        Args:
            vessel_name: Vessel name (partial match supported)
            imo_number: IMO number (exact match)
            mmsi: Maritime Mobile Service Identity
        
        Returns:
            Dictionary with vessel position and status
        """
        # Try to find vessel in mock database
        vessel_info = None
        matched_name = None
        
        if vessel_name:
            # Case-insensitive partial match
            vessel_name_upper = vessel_name.upper()
            for name, info in self.mock_vessels.items():
                if vessel_name_upper in name:
                    vessel_info = info.copy()
                    vessel_info['vessel_name'] = name
                    matched_name = name
                    break
        
        elif imo_number:
            for name, info in self.mock_vessels.items():
                if info['imo'] == imo_number:
                    vessel_info = info.copy()
                    vessel_info['vessel_name'] = name
                    matched_name = name
                    break
        
        elif mmsi:
            for name, info in self.mock_vessels.items():
                if info['mmsi'] == mmsi:
                    vessel_info = info.copy()
                    vessel_info['vessel_name'] = name
                    matched_name = name
                    break
        
        if not vessel_info:
            return {
                "error": "Vessel not found",
                "message": f"No vessel found matching: {vessel_name or imo_number or mmsi}"
            }
        
        # Generate current position
        position_data = self._generate_mock_position(vessel_info)
        
        # Store in database for historical tracking
        now = datetime.now().isoformat()
        db_record = {
            "vessel_name": matched_name,
            "imo_number": vessel_info['imo'],
            "mmsi": vessel_info['mmsi'],
            "latitude": position_data['latitude'],
            "longitude": position_data['longitude'],
            "speed": position_data['speed'],
            "heading": position_data['heading'],
            "status": position_data['status'],
            "next_port": position_data['next_port'],
            "eta": position_data['eta'],
            "timestamp": now
        }
        insert_vessel_position(db_record)
        
        # Return comprehensive vessel information
        return {
            "vessel_name": matched_name,
            "imo": vessel_info['imo'],
            "mmsi": vessel_info['mmsi'],
            "type": vessel_info['type'],
            "flag": vessel_info['flag'],
            "dwt": vessel_info['dwt'],
            "position": {
                "lat": position_data['latitude'],
                "lon": position_data['longitude']
            },
            "speed": position_data['speed'],
            "heading": position_data['heading'],
            "status": position_data['status'],
            "next_port": position_data['next_port'],
            "eta": position_data['eta'],
            "last_updated": now,
            "data_source": "Mock AIS (Day 6 Development)"
        }
    
    def get_vessel_history(self, vessel_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical positions for a vessel"""
        positions = query_vessel_positions(vessel_name=vessel_name)
        return positions[:limit]
    
    def get_all_tracked_vessels(self) -> List[str]:
        """Get list of all trackable vessels"""
        return list(self.mock_vessels.keys())

# Global service instance
_vessel_tracking_service = None

def get_vessel_tracking_service() -> VesselTrackingService:
    """Get or create vessel tracking service instance"""
    global _vessel_tracking_service
    if _vessel_tracking_service is None:
        _vessel_tracking_service = VesselTrackingService()
    return _vessel_tracking_service
