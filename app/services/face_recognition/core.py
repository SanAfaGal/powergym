"""
Core face recognition service combining all operations.
Provides high-level API for face registration, authentication, and comparison.
"""

from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.encryption import get_encryption_service
from app.core.compression import CompressionService
from .image_processor import ImageProcessor
from .embedding import EmbeddingService
from .database import FaceDatabase


class FaceRecognitionService:
    """Main service for face recognition operations."""

    @staticmethod
    def extract_face_encoding(image_base64: str) -> Tuple[List[float], bytes, bytes, bytes]:
        """
        Extract face encoding and process image with optimized compression.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            Tuple of (512-dim embedding, compressed_image, thumbnail, original_bytes)

        Raises:
            ValueError: If image processing or face extraction fails
        """
        import base64

        if ',' in image_base64:
            original_bytes = base64.b64decode(image_base64.split(',')[1])
        else:
            original_bytes = base64.b64decode(image_base64)

        image_array = ImageProcessor.decode_base64_image(image_base64)

        face_encoding_128 = EmbeddingService.extract_face_encoding(image_array)
        embedding_128 = face_encoding_128.tolist()
        embedding_512 = EmbeddingService.expand_embedding_to_512(embedding_128)

        compressed_data = ImageProcessor.compress_image(image_array)
        thumbnail = ImageProcessor.create_thumbnail(image_array)

        return embedding_512, compressed_data, thumbnail, original_bytes

    @staticmethod
    async def extract_face_encoding_async(
        image_base64: str
    ) -> Tuple[List[float], bytes, bytes, bytes]:
        """
        Extract face encoding asynchronously.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            Tuple of (512-dim embedding, compressed_image, thumbnail, original_bytes)
        """
        from app.core.async_processing import run_in_threadpool
        return await run_in_threadpool(
            FaceRecognitionService.extract_face_encoding,
            image_base64
        )

    @staticmethod
    def compare_faces(
        embedding_1: any,
        embedding_2: any,
        tolerance: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Compare two face embeddings.

        Args:
            embedding_1: First embedding (512-dimensional)
            embedding_2: Second embedding (512-dimensional)
            tolerance: Similarity threshold

        Returns:
            Tuple of (is_match: bool, distance: float)
        """
        return EmbeddingService.compare_embeddings(
            embedding_1,
            embedding_2,
            tolerance
        )

    @staticmethod
    def register_face(db: Session, client_id: UUID, image_base64: str) -> dict:
        """
        Register a face biometric for a client with compression.

        Args:
            db: Database session
            client_id: UUID of the client
            image_base64: Base64 encoded face image

        Returns:
            Dictionary with success status, biometric info, and compression stats
        """
        try:
            embedding, compressed_data, thumbnail, original_bytes = (
                FaceRecognitionService.extract_face_encoding(image_base64)
            )

            result = FaceDatabase.store_face_biometric(
                db=db,
                client_id=client_id,
                embedding=embedding,
                compressed_data=compressed_data,
                thumbnail=thumbnail,
                original_image_bytes=original_bytes
            )

            return result

        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
            }

    @staticmethod
    def authenticate_face(
        db: Session,
        image_base64: str,
        tolerance: Optional[float] = None
    ) -> dict:
        """
        Authenticate a client by face image.

        Args:
            db: Database session
            image_base64: Base64 encoded face image
            tolerance: Optional similarity threshold

        Returns:
            Dictionary with authentication result and client info
        """
        try:
            embedding, _, _, _ = FaceRecognitionService.extract_face_encoding(image_base64)

            biometric_records = FaceDatabase.get_all_active_face_biometrics(db)

            if not biometric_records:
                return {
                    "success": False,
                    "error": "No registered faces found in the system"
                }

            encryption_service = get_encryption_service()
            compression_service = CompressionService()
            best_match = None
            best_distance = float('inf')

            for biometric in biometric_records:
                if not biometric.get("embedding"):
                    continue

                try:
                    meta_info = biometric.get("meta_info", {})
                    encoding_version = meta_info.get("encoding_version", "")
                    is_encrypted = "encrypted" in encoding_version
                    is_compressed = "compressed" in encoding_version

                    if is_encrypted and is_compressed:
                        compressed_bytes = encryption_service.decrypt_embedding(
                            biometric["embedding"],
                            is_compressed=True
                        )
                        stored_embedding = compression_service.decompress_embedding(
                            compressed_bytes
                        )
                    elif is_encrypted:
                        stored_embedding = encryption_service.decrypt_embedding(
                            biometric["embedding"]
                        )
                    else:
                        stored_embedding = EmbeddingService.parse_embedding(
                            biometric["embedding"]
                        )
                except ValueError:
                    continue

                match, distance = FaceRecognitionService.compare_faces(
                    embedding,
                    stored_embedding,
                    tolerance
                )

                if match and distance < best_distance:
                    best_distance = distance
                    best_match = biometric

            if best_match:
                client_info = FaceDatabase.get_client_info(db, best_match["client_id"])

                if client_info:
                    confidence = max(0.0, 1.0 - best_distance)

                    return {
                        "success": True,
                        "client_id": best_match["client_id"],
                        "client_info": client_info,
                        "confidence": confidence,
                        "distance": best_distance
                    }

            return {
                "success": False,
                "error": "No matching face found"
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}"
            }

    @staticmethod
    def update_face(db: Session, client_id: UUID, image_base64: str) -> dict:
        """
        Update face biometric for a client.

        Args:
            db: Database session
            client_id: UUID of the client
            image_base64: Base64 encoded face image

        Returns:
            Dictionary with success status and biometric info
        """
        return FaceRecognitionService.register_face(db, client_id, image_base64)

    @staticmethod
    def delete_face(db: Session, client_id: UUID) -> dict:
        """
        Delete (deactivate) face biometric for a client.

        Args:
            db: Database session
            client_id: UUID of the client

        Returns:
            Dictionary with success status
        """
        try:
            return FaceDatabase.deactivate_face_biometric(db, client_id)
        except Exception as e:
            return {
                "success": False,
                "error": f"Deletion failed: {str(e)}"
            }

    @staticmethod
    def compare_two_faces(
        image_base64_1: str,
        image_base64_2: str,
        tolerance: Optional[float] = None
    ) -> dict:
        """
        Compare two face images directly.

        Args:
            image_base64_1: First base64 encoded face image
            image_base64_2: Second base64 encoded face image
            tolerance: Optional similarity threshold

        Returns:
            Dictionary with comparison result and confidence
        """
        try:
            embedding_1, _, _, _ = FaceRecognitionService.extract_face_encoding(
                image_base64_1
            )
            embedding_2, _, _, _ = FaceRecognitionService.extract_face_encoding(
                image_base64_2
            )

            match, distance = FaceRecognitionService.compare_faces(
                embedding_1,
                embedding_2,
                tolerance
            )

            confidence = max(0.0, 1.0 - distance)

            return {
                "success": True,
                "match": match,
                "distance": distance,
                "confidence": confidence
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Comparison failed: {str(e)}"
            }
