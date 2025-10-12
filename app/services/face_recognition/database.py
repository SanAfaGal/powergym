"""
Database operations for face recognition biometric data.
Handles CRUD operations for face biometrics with encryption.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.biometric_repository import BiometricRepository
from app.repositories.client_repository import ClientRepository
from app.db.models import BiometricTypeEnum
from app.core.encryption import get_encryption_service
from app.core.compression import CompressionService
from app.models.biometric import BiometricType
from app.core.config import settings


class FaceDatabase:
    """Handles database operations for face biometric data."""

    @staticmethod
    def store_face_biometric(
        db: Session,
        client_id: UUID,
        embedding: List[float],
        compressed_data: bytes,
        thumbnail: bytes,
        original_image_bytes: bytes = None
    ) -> dict:
        """
        Store face biometric data in database with compression and encryption.
        Pipeline: Compress -> Encrypt -> Store

        Args:
            client_id: UUID of the client
            embedding: 512-dimensional face embedding
            compressed_data: Compressed face image bytes
            thumbnail: Thumbnail image bytes
            original_image_bytes: Original image bytes for compression stats (optional)

        Returns:
            Dictionary with success status, biometric_id, and compression stats

        Raises:
            Exception: If database operation fails
        """
        try:
            existing_biometrics = BiometricRepository.get_by_client_id(
                db, client_id, is_active=True
            )

            for biometric in existing_biometrics:
                if biometric.type == BiometricTypeEnum.FACE:
                    BiometricRepository.update(db, biometric.id, is_active=False)

            compression_service = CompressionService()
            encryption_service = get_encryption_service()

            compressed_embedding = compression_service.compress_embedding(embedding)
            encrypted_embedding = encryption_service.encrypt_embedding(compressed_embedding)

            encrypted_compressed_data = encryption_service.encrypt_image_data(
                compressed_data
            )
            encrypted_thumbnail = encryption_service.encrypt_image_data(thumbnail)

            compression_stats = None
            if original_image_bytes:
                compression_stats = compression_service.get_compression_stats(
                    original_embedding=embedding,
                    compressed_embedding=compressed_embedding,
                    original_image=original_image_bytes,
                    compressed_image=compressed_data,
                    thumbnail=thumbnail
                )

            meta_info = {
                "encoding_version": "face_recognition_v2_compressed_encrypted",
                "model": settings.FACE_RECOGNITION_MODEL,
                "compression": "zlib_level_9",
                "encryption": "AES-256-GCM",
                "image_quality": settings.IMAGE_COMPRESSION_QUALITY,
                "thumbnail_quality": settings.THUMBNAIL_COMPRESSION_QUALITY
            }

            if compression_stats:
                meta_info["compression_stats"] = compression_stats

            biometric = BiometricRepository.create(
                db=db,
                client_id=client_id,
                biometric_type=BiometricTypeEnum.FACE,
                compressed_data=encrypted_compressed_data,
                thumbnail=encrypted_thumbnail,
                embedding=encrypted_embedding,
                meta_info=meta_info
            )

            return {
                "success": True,
                "biometric_id": str(biometric.id),
                "client_id": str(client_id),
                "compression_stats": compression_stats
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Database operation failed: {str(e)}"
            }

    @staticmethod
    def get_all_active_face_biometrics(db: Session) -> List[dict]:
        """
        Retrieve all active face biometric records from database.

        Returns:
            List of biometric records with encrypted data

        Raises:
            Exception: If database query fails
        """
        try:
            biometrics = BiometricRepository.get_by_type(
                db, BiometricTypeEnum.FACE, is_active=True
            )

            return [
                {
                    "id": str(bio.id),
                    "client_id": str(bio.client_id),
                    "embedding": bio.embedding,
                    "meta_info": bio.meta_info
                }
                for bio in biometrics
            ]

        except Exception as e:
            raise Exception(f"Failed to retrieve biometric data: {str(e)}")

    @staticmethod
    def get_client_info(db: Session, client_id: str) -> Optional[dict]:
        """
        Retrieve client information by ID.

        Args:
            client_id: UUID string of the client

        Returns:
            Client information dictionary or None if not found

        Raises:
            Exception: If database query fails
        """
        try:
            from uuid import UUID as UUID_Parser
            client_uuid = UUID_Parser(client_id)

            client = ClientRepository.get_by_id(db, client_uuid)

            if client and client.is_active:
                return {
                    "id": str(client.id),
                    "dni_type": client.dni_type.value,
                    "dni_number": client.dni_number,
                    "first_name": client.first_name,
                    "middle_name": client.middle_name,
                    "last_name": client.last_name,
                    "second_last_name": client.second_last_name,
                    "phone": client.phone,
                    "alternative_phone": client.alternative_phone,
                    "birth_date": client.birth_date.isoformat(),
                    "gender": client.gender.value,
                    "address": client.address,
                    "is_active": client.is_active,
                    "created_at": client.created_at.isoformat(),
                    "updated_at": client.updated_at.isoformat(),
                    "meta_info": client.meta_info
                }

            return None

        except Exception as e:
            raise Exception(f"Failed to retrieve client info: {str(e)}")

    @staticmethod
    def deactivate_face_biometric(db: Session, client_id: UUID) -> dict:
        """
        Deactivate all face biometric records for a client.

        Args:
            client_id: UUID of the client

        Returns:
            Dictionary with success status

        Raises:
            Exception: If database operation fails
        """
        try:
            biometrics = BiometricRepository.get_by_client_id(
                db, client_id, is_active=True
            )

            deactivated_count = 0
            for biometric in biometrics:
                if biometric.type == BiometricTypeEnum.FACE:
                    BiometricRepository.update(db, biometric.id, is_active=False)
                    deactivated_count += 1

            if deactivated_count > 0:
                return {
                    "success": True,
                    "message": "Face biometric deactivated successfully"
                }

            return {
                "success": False,
                "error": "No active face biometric found"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Database operation failed: {str(e)}"
            }
