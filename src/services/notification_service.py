"""
Notification Service
====================

Handles customer notifications via email and SMS.
Supports multiple notification types and multi-language templates.

For MVP: Uses mock/logging implementation
For Production: Integrate SendGrid (email) and Twilio (SMS)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import query_shipments

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending customer notifications"""
    
    # Notification types
    NOTIFICATION_TYPES = [
        "departed",
        "in_transit", 
        "arrived",
        "customs_cleared",
        "delivered",
        "delayed",
        "exception"
    ]
    
    # Supported languages
    LANGUAGES = ["en", "es", "zh"]
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize notification service.
        
        Args:
            mock_mode: If True, log notifications instead of sending (for testing)
        """
        self.mock_mode = mock_mode
        
        if not mock_mode:
            # In production, initialize real email/SMS clients
            # self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            # self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            pass
        
        logger.info(f"NotificationService initialized (mock_mode={mock_mode})")
    
    def _get_email_template(
        self, 
        notification_type: str, 
        language: str,
        shipment_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Get email subject and body for notification type.
        
        Args:
            notification_type: Type of notification
            language: Language code (en, es, zh)
            shipment_data: Shipment information
        
        Returns:
            Dict with 'subject' and 'body' keys
        """
        shipment_id = shipment_data.get('id', 'Unknown')
        origin = shipment_data.get('origin', 'Origin')
        destination = shipment_data.get('destination', 'Destination')
        container = shipment_data.get('container_number', 'N/A')
        
        # English templates
        templates_en = {
            "departed": {
                "subject": f"Your shipment {shipment_id} has departed",
                "body": f"""Dear Customer,

Your shipment {shipment_id} has departed from {origin} and is now on its way to {destination}.

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Origin: {origin}
- Destination: {destination}

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "in_transit": {
                "subject": f"Shipment {shipment_id} is in transit",
                "body": f"""Dear Customer,

Your shipment {shipment_id} is currently in transit from {origin} to {destination}.

Current Status: In Transit
Container: {container}

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "arrived": {
                "subject": f"Shipment {shipment_id} has arrived at {destination}",
                "body": f"""Dear Customer,

Great news! Your shipment {shipment_id} has arrived at {destination}.

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Destination: {destination}

Next steps: The shipment will proceed to customs clearance.

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "customs_cleared": {
                "subject": f"Shipment {shipment_id} cleared customs",
                "body": f"""Dear Customer,

Your shipment {shipment_id} has successfully cleared customs and is being prepared for final delivery.

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Location: {destination}

Your shipment will be delivered soon.

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "delivered": {
                "subject": f"Shipment {shipment_id} has been delivered",
                "body": f"""Dear Customer,

Your shipment {shipment_id} has been successfully delivered!

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Delivered to: {destination}

Thank you for choosing CW Logistics.

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "delayed": {
                "subject": f"Important: Shipment {shipment_id} may be delayed",
                "body": f"""Dear Customer,

We want to inform you that your shipment {shipment_id} may experience a delay.

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Route: {origin} to {destination}

Reason: {{delay_reason}}

We are working to minimize the impact and will keep you updated.

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            },
            "exception": {
                "subject": f"Attention: Exception for shipment {shipment_id}",
                "body": f"""Dear Customer,

An exception has been detected for your shipment {shipment_id}.

Shipment Details:
- Shipment ID: {shipment_id}
- Container: {container}
- Issue: {{exception_details}}

Our team is investigating and will provide updates soon.

Track your shipment: {{tracking_url}}

Best regards,
CW Logistics Team
"""
            }
        }
        
        # For MVP, only English. Add Spanish/Chinese translations later
        if language == "en":
            return templates_en.get(notification_type, templates_en["in_transit"])
        else:
            # Fallback to English for now
            logger.warning(f"Language {language} not fully implemented, using English")
            return templates_en.get(notification_type, templates_en["in_transit"])
    
    async def send_status_update(
        self,
        shipment_id: str,
        notification_type: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        language: str = "en",
        tracking_url: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send status update notification to customer.
        
        Args:
            shipment_id: Shipment ID
            notification_type: Type of notification (departed, in_transit, etc.)
            recipient_email: Customer email address
            recipient_phone: Customer phone number (optional)
            language: Notification language (en, es, zh)
            tracking_url: Public tracking URL
            additional_data: Extra data for template (delay_reason, exception_details, etc.)
        
        Returns:
            Notification result with delivery status
        """
        logger.info(f"Sending notification: {notification_type} for shipment {shipment_id}")
        
        # Validate notification type
        if notification_type not in self.NOTIFICATION_TYPES:
            return {
                "error": True,
                "message": f"Invalid notification type: {notification_type}. Must be one of {self.NOTIFICATION_TYPES}"
            }
        
        # Validate language
        if language not in self.LANGUAGES:
            logger.warning(f"Unsupported language: {language}, falling back to 'en'")
            language = "en"
        
        # Query shipment data
        shipment_data = None
        try:
            shipments = query_shipments(job_number=shipment_id)
            if shipments:
                shipment = shipments[0]
                shipment_data = {
                    "id": shipment_id,
                    "origin": shipment[2],  # origin
                    "destination": shipment[3],  # destination
                    "container_number": shipment[1],  # container_number
                    "status": shipment[4]  # status
                }
        except Exception as e:
            logger.error(f"Error querying shipment {shipment_id}: {e}")
            shipment_data = {
                "id": shipment_id,
                "origin": "Origin Port",
                "destination": "Destination Port",
                "container_number": "N/A",
                "status": "unknown"
            }
        
        # Get email template
        template = self._get_email_template(notification_type, language, shipment_data)
        
        # Insert tracking URL
        if not tracking_url:
            tracking_url = f"https://track.cwlogistics.com/{shipment_id}"
        
        body = template["body"].replace("{tracking_url}", tracking_url)
        
        # Insert additional data if provided
        if additional_data:
            for key, value in additional_data.items():
                body = body.replace(f"{{{key}}}", str(value))
        
        # Generate notification ID
        notification_id = f"NOTIF-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Send notification
        channels_used = []
        
        if recipient_email:
            if self.mock_mode:
                logger.info(f"📧 [MOCK] Email to {recipient_email}")
                logger.info(f"   Subject: {template['subject']}")
                logger.info(f"   Body preview: {body[:200]}...")
                channels_used.append("email")
            else:
                # Production: Send via SendGrid
                # await self._send_email(recipient_email, template['subject'], body)
                pass
        
        if recipient_phone:
            # SMS message (shorter version)
            sms_message = f"CW Logistics: Shipment {shipment_id} - {notification_type.replace('_', ' ').title()}. Track: {tracking_url}"
            
            if self.mock_mode:
                logger.info(f"📱 [MOCK] SMS to {recipient_phone}")
                logger.info(f"   Message: {sms_message}")
                channels_used.append("sms")
            else:
                # Production: Send via Twilio
                # await self._send_sms(recipient_phone, sms_message)
                pass
        
        # Log to database (notifications table)
        # In production, store in database for audit trail
        
        return {
            "success": True,
            "notification_id": notification_id,
            "shipment_id": shipment_id,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat() + "Z",
            "channels": channels_used,
            "recipient_email": recipient_email,
            "recipient_phone": recipient_phone,
            "language": language,
            "message_preview": template["subject"],
            "tracking_url": tracking_url
        }
    
    async def proactive_delay_warning(
        self,
        shipment_id: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        language: str = "en",
        ml_prediction_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Proactively warn customer about potential delays based on ML predictions (Tool 30).
        
        This function checks ML confidence and automatically sends a delay notification
        if the confidence exceeds 70%. It includes risk factors and predicted delay duration.
        
        Args:
            shipment_id: Shipment ID to check
            recipient_email: Customer email address (optional)
            recipient_phone: Customer phone number (optional)
            language: Notification language (default: en)
            ml_prediction_data: Pre-computed ML prediction (optional, will fetch if not provided)
        
        Returns:
            Dictionary with warning sent status and details
        """
        logger.info(f"🔔 Proactive delay warning check for shipment: {shipment_id}")
        
        try:
            # If ML prediction not provided, we would fetch it from ML service
            # For now, use the provided data or check confidence threshold
            if not ml_prediction_data:
                # In production, call ML prediction service here
                # ml_prediction_data = await self._get_ml_prediction(shipment_id)
                logger.warning(f"No ML prediction data provided for {shipment_id}, skipping")
                return {
                    "success": False,
                    "shipment_id": shipment_id,
                    "warning_sent": False,
                    "reason": "No ML prediction data available"
                }
            
            will_delay = ml_prediction_data.get("will_delay", False)
            confidence = ml_prediction_data.get("confidence", 0.0)
            risk_factors = ml_prediction_data.get("risk_factors", [])
            predicted_delay_hours = ml_prediction_data.get("predicted_delay_hours", 0)
            
            # Threshold: Only send warning if confidence > 70%
            CONFIDENCE_THRESHOLD = 0.70
            
            if not will_delay or confidence < CONFIDENCE_THRESHOLD:
                logger.info(f"No proactive warning needed: will_delay={will_delay}, confidence={confidence:.2%}")
                return {
                    "success": True,
                    "shipment_id": shipment_id,
                    "warning_sent": False,
                    "reason": f"Confidence {confidence:.1%} below threshold {CONFIDENCE_THRESHOLD:.0%}",
                    "ml_confidence": confidence
                }
            
            # Get shipment data for notification
            shipment_data = query_shipments(filters={"id": shipment_id})
            shipment_info = shipment_data[0] if shipment_data else {"id": shipment_id}
            
            # Build risk factors message
            risk_msg = ", ".join(risk_factors) if risk_factors else "Multiple factors"
            delay_msg = f"{predicted_delay_hours} hours" if predicted_delay_hours > 0 else "significant delay"
            
            # Create enhanced notification with risk details
            additional_data = {
                "ml_confidence": f"{confidence:.1%}",
                "risk_factors": risk_msg,
                "predicted_delay": delay_msg,
                "action_recommended": "Please contact your logistics coordinator for alternative routing options"
            }
            
            # Send delay notification automatically
            notification_result = await self.send_status_update(
                shipment_id=shipment_id,
                notification_type="delayed",
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                language=language,
                additional_data=additional_data
            )
            
            logger.info(f"✅ Proactive delay warning sent for {shipment_id}: confidence={confidence:.1%}")
            
            return {
                "success": True,
                "shipment_id": shipment_id,
                "warning_sent": True,
                "ml_confidence": confidence,
                "risk_factors": risk_factors,
                "predicted_delay_hours": predicted_delay_hours,
                "notification_id": notification_result.get("notification_id")
            }
            
        except Exception as e:
            logger.error(f"Error in proactive delay warning for {shipment_id}: {e}", exc_info=True)
            return {
                "success": False,
                "shipment_id": shipment_id,
                "warning_sent": False,
                "error": str(e)
            }
    
    async def send_bulk_notifications(
        self,
        shipment_ids: List[str],
        notification_type: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Send notifications for multiple shipments.
        
        Args:
            shipment_ids: List of shipment IDs
            notification_type: Type of notification
            language: Notification language
        
        Returns:
            Summary of sent notifications
        """
        results = []
        
        for shipment_id in shipment_ids:
            try:
                result = await self.send_status_update(
                    shipment_id=shipment_id,
                    notification_type=notification_type,
                    language=language
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error sending notification for {shipment_id}: {e}")
                results.append({
                    "success": False,
                    "shipment_id": shipment_id,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "total": len(shipment_ids),
            "successful": successful,
            "failed": len(shipment_ids) - successful,
            "results": results
        }


# Singleton instance
_notification_service_instance = None

def get_notification_service() -> NotificationService:
    """Get or create singleton instance of NotificationService"""
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService(mock_mode=True)
    return _notification_service_instance
