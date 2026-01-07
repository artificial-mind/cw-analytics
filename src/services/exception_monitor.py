"""
Exception Monitor Service

Automated background service that continuously monitors shipments for exceptions:
- Delays > 24 hours
- ML predictions > 70% confidence
- Temperature deviations
- Geofence violations
- Missing milestones > 72 hours

Runs every 5 minutes and notifies Exception Crew via A2A Protocol.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import httpx
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import get_db_connection, query_shipments

logger = logging.getLogger(__name__)

# Thresholds for exception detection
DELAY_THRESHOLD_HOURS = 24
ML_CONFIDENCE_THRESHOLD = 0.70
TEMP_DEVIATION_THRESHOLD = 5.0  # degrees Celsius
MILESTONE_DELAY_THRESHOLD_HOURS = 72

# A2A Integration
A2A_SERVER_URL = "http://localhost:9000"
A2A_MESSAGE_ENDPOINT = f"{A2A_SERVER_URL}/message:send"


class ExceptionMonitor:
    """
    Background service for detecting and reporting shipment exceptions.
    """
    
    def __init__(self):
        """Initialize the exception monitor"""
        self.running = False
        self.last_run_time = None
        self.total_runs = 0
        logger.info("ExceptionMonitor initialized")
    
    def _get_active_shipments(self) -> List[Dict[str, Any]]:
        """
        Get all active shipments that need monitoring.
        
        Returns:
            List of active shipment records
        """
        try:
            # Query shipments with status != 'delivered'
            shipments = query_shipments()
            active = [s for s in shipments if s.get('status') != 'delivered']
            logger.info(f"Found {len(active)} active shipments to monitor")
            return active
        except Exception as e:
            logger.error(f"Error getting active shipments: {e}", exc_info=True)
            return []
    
    def _check_delay_exception(self, shipment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if shipment has a delay > 24 hours.
        
        Args:
            shipment: Shipment record
            
        Returns:
            Exception details if found, None otherwise
        """
        try:
            # Check if shipment has delay_hours field
            delay_hours = shipment.get('delay_hours', 0)
            if delay_hours > DELAY_THRESHOLD_HOURS:
                return {
                    "type": "delay",
                    "severity": "high" if delay_hours > 48 else "medium",
                    "message": f"Shipment delayed by {delay_hours} hours (threshold: {DELAY_THRESHOLD_HOURS}h)",
                    "delay_hours": delay_hours
                }
        except Exception as e:
            logger.error(f"Error checking delay for shipment {shipment.get('id')}: {e}")
        return None
    
    def _check_ml_prediction(self, shipment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if ML prediction indicates high risk of delay.
        
        Args:
            shipment: Shipment record
            
        Returns:
            Exception details if found, None otherwise
        """
        try:
            # For MVP, use mock ML data
            # In production, call actual ML service
            ml_confidence = shipment.get('ml_delay_confidence', 0)
            if ml_confidence > ML_CONFIDENCE_THRESHOLD:
                return {
                    "type": "ml_prediction",
                    "severity": "high" if ml_confidence > 0.85 else "medium",
                    "message": f"ML predicts delay with {ml_confidence:.0%} confidence",
                    "ml_confidence": ml_confidence,
                    "predicted_delay_hours": shipment.get('predicted_delay_hours', 24)
                }
        except Exception as e:
            logger.error(f"Error checking ML prediction for shipment {shipment.get('id')}: {e}")
        return None
    
    def _check_temperature_deviation(self, shipment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check for temperature deviations in reefer containers.
        
        Args:
            shipment: Shipment record
            
        Returns:
            Exception details if found, None otherwise
        """
        try:
            # Query containers for this shipment
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT container_id, current_temp, target_temp, container_type
                    FROM containers 
                    WHERE shipment_id = ? AND container_type = 'reefer'
                """, (shipment.get('id'),))
                
                containers = cursor.fetchall()
                for container in containers:
                    current = container[1]
                    target = container[2]
                    if current is not None and target is not None:
                        deviation = abs(current - target)
                        if deviation > TEMP_DEVIATION_THRESHOLD:
                            return {
                                "type": "temperature_deviation",
                                "severity": "high",
                                "message": f"Container {container[0]} temperature deviation: {deviation:.1f}°C",
                                "container_id": container[0],
                                "current_temp": current,
                                "target_temp": target,
                                "deviation": deviation
                            }
        except Exception as e:
            logger.error(f"Error checking temperature for shipment {shipment.get('id')}: {e}")
        return None
    
    def _check_geofence_violation(self, shipment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check for geofence violations.
        
        Args:
            shipment: Shipment record
            
        Returns:
            Exception details if found, None otherwise
        """
        try:
            # Check if shipment has geofence violation flag
            if shipment.get('geofence_violation'):
                return {
                    "type": "geofence_violation",
                    "severity": "high",
                    "message": "Shipment outside expected route",
                    "current_location": shipment.get('current_location', 'Unknown')
                }
        except Exception as e:
            logger.error(f"Error checking geofence for shipment {shipment.get('id')}: {e}")
        return None
    
    def _check_missing_milestones(self, shipment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check for missing milestones > 72 hours.
        
        Args:
            shipment: Shipment record
            
        Returns:
            Exception details if found, None otherwise
        """
        try:
            # Query milestones for this shipment
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT milestone_name, expected_time, actual_time
                    FROM milestones 
                    WHERE shipment_id = ? AND actual_time IS NULL
                    ORDER BY expected_time
                """, (shipment.get('id'),))
                
                milestones = cursor.fetchall()
                now = datetime.now()
                
                for milestone in milestones:
                    expected = milestone[1]
                    if expected:
                        expected_dt = datetime.fromisoformat(expected)
                        hours_late = (now - expected_dt).total_seconds() / 3600
                        if hours_late > MILESTONE_DELAY_THRESHOLD_HOURS:
                            return {
                                "type": "missing_milestone",
                                "severity": "medium",
                                "message": f"Milestone '{milestone[0]}' overdue by {hours_late:.0f} hours",
                                "milestone_name": milestone[0],
                                "hours_overdue": hours_late
                            }
        except Exception as e:
            logger.error(f"Error checking milestones for shipment {shipment.get('id')}: {e}")
        return None
    
    def _detect_exceptions(self, shipment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run all exception checks on a shipment.
        
        Args:
            shipment: Shipment record
            
        Returns:
            List of detected exceptions
        """
        exceptions = []
        
        # Run all checks
        checks = [
            self._check_delay_exception,
            self._check_ml_prediction,
            self._check_temperature_deviation,
            self._check_geofence_violation,
            self._check_missing_milestones
        ]
        
        for check in checks:
            try:
                result = check(shipment)
                if result:
                    result['shipment_id'] = shipment.get('id')
                    result['detected_at'] = datetime.now().isoformat()
                    exceptions.append(result)
            except Exception as e:
                logger.error(f"Error in check {check.__name__}: {e}")
        
        return exceptions
    
    async def _notify_a2a_server(self, exceptions: List[Dict[str, Any]]) -> int:
        """
        Send exceptions to A2A Exception Crew for handling.
        
        Args:
            exceptions: List of detected exceptions
            
        Returns:
            Number of notifications sent successfully
        """
        notifications_sent = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for exception in exceptions:
                try:
                    # Build A2A message
                    message = {
                        "skill": "handle-exception",
                        "crew": "exception",
                        "input": {
                            "shipment_id": exception.get('shipment_id'),
                            "exception_type": exception.get('type'),
                            "severity": exception.get('severity'),
                            "details": exception
                        }
                    }
                    
                    logger.info(f"Sending exception to A2A server: {exception.get('type')} for {exception.get('shipment_id')}")
                    
                    response = await client.post(
                        A2A_MESSAGE_ENDPOINT,
                        json=message,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        notifications_sent += 1
                        logger.info(f"Successfully notified A2A server about {exception.get('type')}")
                    else:
                        logger.warning(f"A2A server returned status {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error notifying A2A server: {e}", exc_info=True)
        
        return notifications_sent
    
    def _log_run_to_database(self, run_data: Dict[str, Any]):
        """
        Log monitoring run to database.
        
        Args:
            run_data: Run statistics
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO exception_monitor_runs 
                    (run_timestamp, exceptions_found, shipments_checked, notifications_sent, run_duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    run_data['timestamp'],
                    run_data['exceptions_found'],
                    run_data['shipments_checked'],
                    run_data['notifications_sent'],
                    run_data['duration_ms']
                ))
                conn.commit()
                logger.info(f"Logged monitoring run to database: {run_data}")
        except Exception as e:
            logger.error(f"Error logging run to database: {e}", exc_info=True)
    
    async def run_once(self) -> Dict[str, Any]:
        """
        Run one monitoring cycle.
        
        Returns:
            Run statistics
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("Starting exception monitoring cycle")
        
        try:
            # Get active shipments
            shipments = self._get_active_shipments()
            
            # Detect exceptions
            all_exceptions = []
            for shipment in shipments:
                exceptions = self._detect_exceptions(shipment)
                all_exceptions.extend(exceptions)
            
            logger.info(f"Detected {len(all_exceptions)} exceptions across {len(shipments)} shipments")
            
            # Notify A2A server
            notifications_sent = 0
            if all_exceptions:
                notifications_sent = await self._notify_a2a_server(all_exceptions)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Build run data
            run_data = {
                'timestamp': datetime.now().isoformat(),
                'exceptions_found': len(all_exceptions),
                'shipments_checked': len(shipments),
                'notifications_sent': notifications_sent,
                'duration_ms': duration_ms
            }
            
            # Log to database
            self._log_run_to_database(run_data)
            
            # Update stats
            self.last_run_time = datetime.now()
            self.total_runs += 1
            
            logger.info(f"Monitoring cycle complete: {run_data}")
            logger.info("=" * 80)
            
            return run_data
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
            return {
                'timestamp': datetime.now().isoformat(),
                'exceptions_found': 0,
                'shipments_checked': 0,
                'notifications_sent': 0,
                'duration_ms': int((time.time() - start_time) * 1000),
                'error': str(e)
            }
    
    async def start_monitoring(self, interval_minutes: int = 5):
        """
        Start the monitoring loop.
        
        Args:
            interval_minutes: Minutes between monitoring cycles (default: 5)
        """
        self.running = True
        logger.info(f"Starting exception monitor (interval: {interval_minutes} minutes)")
        
        while self.running:
            try:
                await self.run_once()
                
                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        logger.info("Stopping exception monitor")
        self.running = False


# Singleton instance
_exception_monitor = None

def get_exception_monitor() -> ExceptionMonitor:
    """Get or create singleton ExceptionMonitor instance"""
    global _exception_monitor
    if _exception_monitor is None:
        _exception_monitor = ExceptionMonitor()
    return _exception_monitor
