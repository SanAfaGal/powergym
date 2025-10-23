"""
Core face recognition service combining all operations.
Provides high-level API for face registration, authentication, and comparison.
"""

from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy.orm import Session

from .image_processor import ImageProcessor
from .embedding import EmbeddingService
from .database import FaceDatabase


class FaceRecognitionService:
    """Main service for face recognition operations."""

    @staticmethod
    def extract_face_encoding(image_base64: str) -> Tuple[List[float], bytes]:
        """
        Extract face encoding and create thumbnail.

        Args:
            image_base64: Base64 encoded image string

        Returns:
            Tuple of (dim embedding, thumbnail)

        Raises:
            ValueError: If image processing or face extraction fails
        """
        image_array = ImageProcessor.decode_base64_image(image_base64)

        face_encoding= EmbeddingService.extract_face_encoding(image_array)
        embedding= face_encoding.tolist()

        thumbnail = ImageProcessor.create_thumbnail(image_array)

        return embedding, thumbnail

    @staticmethod
    def compare_faces(
        embedding_1: any,
        embedding_2: any,
        tolerance: Optional[float] = 0.4
    ) -> Tuple[bool, float]:
        """
        Compare two face embeddings.

        Args:
            embedding_1: First embedding (128-dimensional)
            embedding_2: Second embedding (128-dimensional)
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
        Register a face biometric for a client.

        Args:
            db: Database session
            client_id: UUID of the client
            image_base64: Base64 encoded face image

        Returns:
            Dictionary with success status and biometric info
        """
        try:
            embedding, thumbnail = FaceRecognitionService.extract_face_encoding(image_base64)

            result = FaceDatabase.store_face_biometric(
                db=db,
                client_id=client_id,
                embedding=embedding,
                thumbnail=thumbnail
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
        Authenticate a client by face image using vector similarity search.

        Args:
            db: Database session
            image_base64: Base64 encoded face image
            tolerance: Optional similarity threshold

        Returns:
            Dictionary with authentication result and client info
        """
        try:
            embedding, _ = FaceRecognitionService.extract_face_encoding(image_base64)

            if tolerance is None:
                from app.core.config import settings
                tolerance = settings.FACE_RECOGNITION_TOLERANCE

            similar_faces = FaceDatabase.search_similar_faces(
                db=db,
                embedding=embedding,
                limit=5,
                distance_threshold=tolerance
            )

            if not similar_faces:
                return {
                    "success": False,
                    "error": "No matching face found"
                }

            best_match = similar_faces[0]
            client_info = FaceDatabase.get_client_info(db, best_match["client_id"])

            if client_info:
                return {
                    "success": True,
                    "client_id": best_match["client_id"],
                    "client_info": client_info,
                    "confidence": best_match["similarity"],
                    "distance": best_match["distance"]
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
        tolerance: Optional[float] = 0.4
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
            embedding_1, _ = FaceRecognitionService.extract_face_encoding(image_base64_1)
            embedding_2, _ = FaceRecognitionService.extract_face_encoding(image_base64_2)

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
