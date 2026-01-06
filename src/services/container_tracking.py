"""
Container Tracking Service
===========================

Provides real-time container tracking with IoT sensor data:
- GPS location tracking
- Temperature monitoring
- Humidity monitoring
- Shock/impact detection
- Door open/close events
- Battery levels
- Alert generation

Features:
- Track by container number
- Live sensor readings
- Historical sensor data
- Geofencing alerts
- Condition monitoring
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import query_container_sensors, query_shipments

class ContainerTrackingService:
    """Service for tracking containers with IoT sensors"""
    
    def __init__(self):
        """Initialize container tracking service"""
        # Mock sensor data for different containers
        self.container_sensors = {
            "MAEU1234567": {
                "container_type": "40HC Reefer",
                "current_shipment": "job-2025-001",
                "gps_enabled": True,
                "temp_sensor": True,
                "humidity_sensor": True,
                "shock_sensor": True,
                "door_sensor": True,
                "battery_level": 87,
                "last_sync": datetime.utcnow().isoformat() + "Z"
            },
            "MSCU7654321": {
                "container_type": "40HC Standard",
                "current_shipment": "job-2025-002",
                "gps_enabled": True,
                "temp_sensor": False,
                "humidity_sensor": False,
                "shock_sensor": True,
                "door_sensor": True,
                "battery_level": 64,
                "last_sync": datetime.utcnow().isoformat() + "Z"
            },
            "TEMU9876543": {
                "container_type": "20DC Standard",
                "current_shipment": "job-2025-005",
                "gps_enabled": True,
                "temp_sensor": False,
                "humidity_sensor": False,
                "shock_sensor": True,
                "door_sensor": True,
                "battery_level": 92,
                "last_sync": datetime.utcnow().isoformat() + "Z"
            }
        }
    
    def _generate_live_gps(self, container_number: str) -> Dict[str, Any]:
        """Generate live GPS coordinates (mock data)"""
        # Base positions for different containers
        base_positions = {
            "MAEU1234567": {"lat": 37.776995, "lon": -122.420063},  # San Francisco Bay
            "MSCU7654321": {"lat": 40.712776, "lon": -74.005974},   # New York Harbor
            "TEMU9876543": {"lat": 1.352083, "lon": 103.819839}     # Singapore
        }
        
        base = base_positions.get(container_number, {"lat": 0.0, "lon": 0.0})
        
        # Add small random drift to simulate movement
        return {
            "latitude": round(base["lat"] + random.uniform(-0.01, 0.01), 6),
            "longitude": round(base["lon"] + random.uniform(-0.01, 0.01), 6),
            "accuracy_meters": random.randint(5, 15),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_live_temperature(self, container_number: str) -> Dict[str, Any]:
        """Generate live temperature reading (mock data)"""
        # Reefer containers maintain lower temps
        if "MAEU" in container_number:
            temp_c = round(random.uniform(-18.0, -15.0), 1)
            setpoint = -18.0
        else:
            temp_c = round(random.uniform(20.0, 28.0), 1)
            setpoint = None
        
        temp_f = round(temp_c * 9/5 + 32, 1)
        
        result = {
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if setpoint:
            result["setpoint_celsius"] = setpoint
            result["deviation"] = round(temp_c - setpoint, 1)
        
        return result
    
    def _generate_live_humidity(self, container_number: str) -> Dict[str, Any]:
        """Generate live humidity reading (mock data)"""
        return {
            "relative_humidity_percent": round(random.uniform(45.0, 65.0), 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_shock_events(self, container_number: str) -> List[Dict[str, Any]]:
        """Generate recent shock events (mock data)"""
        # Random chance of shock events
        if random.random() < 0.3:  # 30% chance of having events
            num_events = random.randint(1, 3)
            events = []
            
            for i in range(num_events):
                hours_ago = random.randint(1, 48)
                event_time = datetime.utcnow() - timedelta(hours=hours_ago)
                
                events.append({
                    "timestamp": event_time.isoformat() + "Z",
                    "severity": random.choice(["low", "medium", "high"]),
                    "g_force": round(random.uniform(2.0, 8.0), 1),
                    "duration_ms": random.randint(50, 500),
                    "location": random.choice([
                        "During loading",
                        "During transport",
                        "During unloading",
                        "Port operations"
                    ])
                })
            
            return sorted(events, key=lambda x: x["timestamp"], reverse=True)
        
        return []
    
    def _generate_door_events(self, container_number: str) -> List[Dict[str, Any]]:
        """Generate door open/close events (mock data)"""
        events = []
        
        # Generate 2-4 door events
        num_events = random.randint(2, 4)
        
        for i in range(num_events):
            hours_ago = random.randint(1, 120)  # Last 5 days
            event_time = datetime.utcnow() - timedelta(hours=hours_ago)
            
            events.append({
                "timestamp": event_time.isoformat() + "Z",
                "action": "opened" if i % 2 == 0 else "closed",
                "location": random.choice([
                    "Origin warehouse",
                    "Port of loading",
                    "Customs inspection",
                    "Port of discharge"
                ]),
                "authorized": True
            })
        
        return sorted(events, key=lambda x: x["timestamp"], reverse=True)
    
    def _generate_alerts(self, container_data: Dict[str, Any],
                        temp_data: Dict[str, Any],
                        shock_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alerts based on sensor readings"""
        alerts = []
        
        # Temperature deviation alert
        if temp_data.get("deviation") and abs(temp_data["deviation"]) > 2.0:
            alerts.append({
                "type": "temperature_deviation",
                "severity": "high" if abs(temp_data["deviation"]) > 3.0 else "medium",
                "message": f"Temperature deviation: {temp_data['deviation']}°C from setpoint",
                "timestamp": temp_data["timestamp"]
            })
        
        # High shock alert
        high_shocks = [e for e in shock_events if e["severity"] in ["high", "medium"]]
        if high_shocks:
            alerts.append({
                "type": "shock_impact",
                "severity": high_shocks[0]["severity"],
                "message": f"Shock event detected: {high_shocks[0]['g_force']}g",
                "timestamp": high_shocks[0]["timestamp"]
            })
        
        # Low battery alert
        if container_data["battery_level"] < 20:
            alerts.append({
                "type": "low_battery",
                "severity": "high" if container_data["battery_level"] < 10 else "medium",
                "message": f"Low battery: {container_data['battery_level']}%",
                "timestamp": container_data["last_sync"]
            })
        
        return alerts
    
    def track_container_live(self, container_number: str) -> Dict[str, Any]:
        """
        Track container with live IoT sensor data.
        
        Args:
            container_number: Container number (e.g., MAEU1234567)
        
        Returns:
            Live tracking data including GPS, sensors, alerts
        """
        # Check if container exists
        if container_number not in self.container_sensors:
            return {
                "error": True,
                "message": f"Container {container_number} not found or not equipped with sensors"
            }
        
        container_data = self.container_sensors[container_number]
        
        # Build response
        result = {
            "container_number": container_number,
            "container_type": container_data["container_type"],
            "shipment_id": container_data["current_shipment"],
            "tracking_status": "active",
            "battery_level": container_data["battery_level"],
            "last_sync": container_data["last_sync"]
        }
        
        # Add GPS location
        if container_data["gps_enabled"]:
            result["gps"] = self._generate_live_gps(container_number)
        
        # Add temperature data
        if container_data["temp_sensor"]:
            result["temperature"] = self._generate_live_temperature(container_number)
        
        # Add humidity data
        if container_data["humidity_sensor"]:
            result["humidity"] = self._generate_live_humidity(container_number)
        
        # Add shock events
        if container_data["shock_sensor"]:
            shock_events = self._generate_shock_events(container_number)
            result["shock_events"] = shock_events
            result["total_shock_events"] = len(shock_events)
        
        # Add door events
        if container_data["door_sensor"]:
            door_events = self._generate_door_events(container_number)
            result["door_events"] = door_events[:5]  # Last 5 events
            result["current_door_status"] = "closed" if door_events[0]["action"] == "closed" else "open"
        
        # Generate alerts
        temp_data = result.get("temperature", {})
        shock_events = result.get("shock_events", [])
        alerts = self._generate_alerts(container_data, temp_data, shock_events)
        
        result["alerts"] = alerts
        result["alert_count"] = len(alerts)
        
        return result
    
    def get_all_tracked_containers(self) -> List[Dict[str, str]]:
        """Get list of all containers with IoT sensors"""
        return [
            {
                "container_number": number,
                "type": data["container_type"],
                "shipment": data["current_shipment"],
                "battery": data["battery_level"]
            }
            for number, data in self.container_sensors.items()
        ]


# Singleton instance
_container_tracking_service_instance = None

def get_container_tracking_service() -> ContainerTrackingService:
    """Get or create singleton instance of ContainerTrackingService"""
    global _container_tracking_service_instance
    if _container_tracking_service_instance is None:
        _container_tracking_service_instance = ContainerTrackingService()
    return _container_tracking_service_instance
