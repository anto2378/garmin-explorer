"""
WhatsApp integration service for sending digest messages
"""

import logging
import requests
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending messages via WhatsApp Business API"""
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    
    def send_message(self, group_id: str, message: str) -> Dict[str, Any]:
        """Send a text message to a WhatsApp group"""
        if not self._is_configured():
            logger.warning("WhatsApp API not configured, simulating message send")
            return self._simulate_send(group_id, message)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": group_id,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully sent WhatsApp message to group {group_id}")
                return {
                    "status": "sent",
                    "message_id": response.json().get("messages", [{}])[0].get("id"),
                    "group_id": group_id
                }
            else:
                logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
                return {
                    "status": "failed",
                    "error": response.text,
                    "group_id": group_id
                }
                
        except Exception as e:
            logger.error(f"Exception sending WhatsApp message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "group_id": group_id
            }
    
    def send_digest(self, group_whatsapp_id: str, digest_message: str) -> Dict[str, Any]:
        """Send a formatted digest message"""
        logger.info(f"Sending digest to WhatsApp group {group_whatsapp_id}")
        return self.send_message(group_whatsapp_id, digest_message)
    
    def _is_configured(self) -> bool:
        """Check if WhatsApp API is properly configured"""
        return bool(
            self.api_url and 
            self.api_token and 
            self.phone_number_id
        )
    
    def _simulate_send(self, group_id: str, message: str) -> Dict[str, Any]:
        """Simulate sending a message for testing purposes"""
        logger.info(f"[SIMULATION] Sending message to WhatsApp group {group_id}")
        logger.info(f"[SIMULATION] Message preview (first 200 chars): {message[:200]}...")
        
        # Save full message to file for review
        try:
            with open(f"/tmp/whatsapp_digest_{group_id}_{int(datetime.now().timestamp())}.txt", "w") as f:
                f.write(f"WhatsApp Group: {group_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n")
                f.write(message)
            
            logger.info(f"[SIMULATION] Full message saved to /tmp/whatsapp_digest_{group_id}_*.txt")
        except Exception as e:
            logger.warning(f"Could not save simulated message: {e}")
        
        return {
            "status": "simulated",
            "message_id": f"sim_{int(datetime.now().timestamp())}",
            "group_id": group_id,
            "message_length": len(message),
            "preview": message[:200] + "..." if len(message) > 200 else message
        }


# For backwards compatibility and testing
from datetime import datetime