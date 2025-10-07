from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import json
from typing import List, Optional, Union


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive biometric data.
    Uses AES-256-GCM for authenticated encryption.
    """

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service with a base key.

        Args:
            encryption_key: Base64-encoded encryption key (minimum 32 bytes)
        """
        if not encryption_key:
            raise ValueError("Encryption key cannot be empty")

        try:
            key_bytes = base64.b64decode(encryption_key)
            if len(key_bytes) < 32:
                raise ValueError("Encryption key must be at least 32 bytes")
            self._key = key_bytes[:32]
        except Exception as e:
            raise ValueError(f"Invalid encryption key format: {str(e)}")

    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive a key using PBKDF2.

        Args:
            salt: Salt for key derivation

        Returns:
            Derived 32-byte key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self._key)

    def encrypt_embedding(self, embedding: List[float]) -> str:
        """
        Encrypt a face embedding vector.

        Args:
            embedding: List of float values representing the embedding

        Returns:
            Base64-encoded encrypted data with format: salt:nonce:ciphertext:tag
        """
        if not embedding:
            raise ValueError("Embedding cannot be empty")

        embedding_json = json.dumps(embedding)
        embedding_bytes = embedding_json.encode('utf-8')

        salt = os.urandom(16)
        derived_key = self._derive_key(salt)

        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(nonce, embedding_bytes, None)

        encrypted_data = salt + nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt_embedding(self, encrypted_data: str) -> List[float]:
        """
        Decrypt an encrypted embedding vector.

        Args:
            encrypted_data: Base64-encoded encrypted embedding

        Returns:
            Original embedding as list of floats
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        try:
            encrypted_bytes = base64.b64decode(encrypted_data)

            salt = encrypted_bytes[:16]
            nonce = encrypted_bytes[16:28]
            ciphertext = encrypted_bytes[28:]

            derived_key = self._derive_key(salt)

            aesgcm = AESGCM(derived_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            embedding_json = plaintext.decode('utf-8')
            embedding = json.loads(embedding_json)

            if not isinstance(embedding, list):
                raise ValueError("Decrypted data is not a list")

            return embedding
        except Exception as e:
            raise ValueError(f"Failed to decrypt embedding: {str(e)}")

    def encrypt_image_data(self, image_data: Union[bytes, str]) -> str:
        """
        Encrypt image data (compressed image or thumbnail).

        Args:
            image_data: Image bytes or base64-encoded string

        Returns:
            Base64-encoded encrypted data
        """
        if not image_data:
            raise ValueError("Image data cannot be empty")

        if isinstance(image_data, str):
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data

        salt = os.urandom(16)
        derived_key = self._derive_key(salt)

        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(nonce, image_bytes, None)

        encrypted_data = salt + nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt_image_data(self, encrypted_data: str) -> bytes:
        """
        Decrypt encrypted image data.

        Args:
            encrypted_data: Base64-encoded encrypted image

        Returns:
            Original image bytes
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        try:
            encrypted_bytes = base64.b64decode(encrypted_data)

            salt = encrypted_bytes[:16]
            nonce = encrypted_bytes[16:28]
            ciphertext = encrypted_bytes[28:]

            derived_key = self._derive_key(salt)

            aesgcm = AESGCM(derived_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext
        except Exception as e:
            raise ValueError(f"Failed to decrypt image data: {str(e)}")


_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get or create singleton encryption service instance.

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        from app.core.config import settings
        _encryption_service = EncryptionService(settings.BIOMETRIC_ENCRYPTION_KEY)
    return _encryption_service
