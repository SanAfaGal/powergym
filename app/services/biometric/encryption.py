"""
Encryption utilities for biometric data.
Handles encryption and decryption of biometric data including embeddings and images.
"""

from typing import Optional, List

from app.core.encryption import get_encryption_service


class BiometricEncryption:
    """Handles encryption and decryption of biometric data."""

    @staticmethod
    def encrypt_biometric_data(
        compressed_data: bytes,
        thumbnail: Optional[bytes] = None,
        embedding: Optional[List[float]] = None
    ) -> tuple:
        """
        Encrypt all biometric data components.

        Args:
            compressed_data: Compressed image data
            thumbnail: Optional thumbnail image data
            embedding: Optional embedding vector

        Returns:
            Tuple of (encrypted_compressed_data, encrypted_thumbnail, encrypted_embedding)
        """
        encryption_service = get_encryption_service()

        encrypted_compressed_data = encryption_service.encrypt_image_data(
            compressed_data
        )

        encrypted_thumbnail = None
        if thumbnail:
            encrypted_thumbnail = encryption_service.encrypt_image_data(thumbnail)

        encrypted_embedding = None
        if embedding:
            encrypted_embedding = encryption_service.encrypt_embedding(embedding)

        return encrypted_compressed_data, encrypted_thumbnail, encrypted_embedding

    @staticmethod
    def decrypt_biometric_data(
        encrypted_compressed_data: str,
        encrypted_thumbnail: Optional[str] = None,
        encrypted_embedding: Optional[str] = None
    ) -> tuple:
        """
        Decrypt all biometric data components.

        Args:
            encrypted_compressed_data: Encrypted compressed image
            encrypted_thumbnail: Optional encrypted thumbnail
            encrypted_embedding: Optional encrypted embedding

        Returns:
            Tuple of (compressed_data, thumbnail, embedding)
        """
        encryption_service = get_encryption_service()

        compressed_data = encryption_service.decrypt_image_data(
            encrypted_compressed_data
        )

        thumbnail = None
        if encrypted_thumbnail:
            thumbnail = encryption_service.decrypt_image_data(encrypted_thumbnail)

        embedding = None
        if encrypted_embedding:
            embedding = encryption_service.decrypt_embedding(encrypted_embedding)

        return compressed_data, thumbnail, embedding
