"""
Encryption utilities for sensitive data like Garmin credentials
"""

import base64
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        self.fernet = self._get_fernet()
    
    def _get_fernet(self) -> Fernet:
        """Get Fernet instance for encryption/decryption"""
        if settings.ENCRYPTION_KEY:
            # Use provided encryption key
            key = settings.ENCRYPTION_KEY.encode()
        else:
            # Generate a key from SECRET_KEY (not ideal for production)
            password = settings.SECRET_KEY.encode()
            salt = b"garmin_companion_salt"  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        if not data:
            return ""
        
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        if not encrypted_data:
            return ""
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")


# Global encryption service instance
encryption_service = EncryptionService()


def encrypt_credential(credential: str) -> str:
    """Encrypt a credential string"""
    return encryption_service.encrypt(credential)


def decrypt_credential(encrypted_credential: str) -> str:
    """Decrypt a credential string"""
    return encryption_service.decrypt(encrypted_credential)