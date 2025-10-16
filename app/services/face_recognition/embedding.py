"""
Embedding generation and comparison utilities for face recognition.
Handles face encoding extraction and similarity calculations using MediaPipe.
"""

from typing import List, Tuple, Optional
import numpy as np
import mediapipe as mp
import cv2

from app.core.config import settings
from app.core.async_processing import run_in_threadpool


class EmbeddingService:
    """Handles face embedding generation and comparison operations."""

    _face_mesh = None
    _face_detection = None

    @classmethod
    def _get_face_mesh(cls):
        """Lazy initialization of MediaPipe FaceMesh."""
        if cls._face_mesh is None:
            min_confidence = settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE
            cls._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=2,
                refine_landmarks=True,
                min_detection_confidence=min_confidence,
                min_tracking_confidence=min_confidence
            )
        return cls._face_mesh

    @classmethod
    def _get_face_detection(cls):
        """Lazy initialization of MediaPipe FaceDetection."""
        if cls._face_detection is None:
            min_confidence = settings.MEDIAPIPE_MIN_DETECTION_CONFIDENCE
            cls._face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=min_confidence
            )
        return cls._face_detection

    @staticmethod
    def extract_face_encoding(image_array: np.ndarray) -> np.ndarray:
        """
        Extract face encoding from an image array using MediaPipe.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            128-dimensional face encoding as numpy array

        Raises:
            ValueError: If no face, multiple faces, or encoding extraction fails
        """
        face_detection = EmbeddingService._get_face_detection()

        results = face_detection.process(image_array)

        if not results.detections:
            raise ValueError("No face detected in the image")

        if len(results.detections) > 1:
            raise ValueError(
                "Multiple faces detected. Please provide an image with a single face"
            )

        face_mesh = EmbeddingService._get_face_mesh()
        mesh_results = face_mesh.process(image_array)

        if not mesh_results.multi_face_landmarks:
            raise ValueError("Could not extract face landmarks from the detected face")

        landmarks = mesh_results.multi_face_landmarks[0]

        embedding = EmbeddingService._landmarks_to_embedding(landmarks, image_array.shape)

        return embedding

    @staticmethod
    def _landmarks_to_embedding(landmarks, image_shape) -> np.ndarray:
        """
        Convert MediaPipe face landmarks to a 128-dimensional embedding.

        Args:
            landmarks: MediaPipe face landmarks
            image_shape: Shape of the original image (height, width, channels)

        Returns:
            128-dimensional embedding vector
        """
        height, width = image_shape[:2]

        key_points = []
        for idx in [1, 33, 61, 199, 263, 291, 4, 152, 10, 338, 297,
                    332, 284, 251, 389, 356, 454, 323, 361, 288, 397,
                    365, 379, 378, 400, 377, 152, 148, 176, 149, 150,
                    136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103,
                    67, 109, 10, 338, 297, 332, 284]:
            landmark = landmarks.landmark[idx]
            key_points.extend([landmark.x * width, landmark.y * height, landmark.z])

        key_points_array = np.array(key_points, dtype=np.float64)

        centroid = key_points_array.reshape(-1, 3).mean(axis=0)
        normalized_points = key_points_array.reshape(-1, 3) - centroid

        scale = np.linalg.norm(normalized_points, axis=1).max()
        if scale > 0:
            normalized_points = normalized_points / scale

        embedding = normalized_points.flatten()

        if len(embedding) < 128:
            embedding = np.pad(embedding, (0, 128 - len(embedding)), mode='constant')
        elif len(embedding) > 128:
            embedding = embedding[:128]

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    @staticmethod
    async def extract_face_encoding_async(image_array: np.ndarray) -> np.ndarray:
        """
        Extract face encoding asynchronously.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            128-dimensional face encoding as numpy array
        """
        return await run_in_threadpool(
            EmbeddingService.extract_face_encoding,
            image_array
        )

    @staticmethod
    def validate_embedding_128(embedding: any) -> np.ndarray:
        """
        Validate and convert embedding to 128-dimensional numpy array.

        Args:
            embedding: 128-dimensional embedding (list, numpy array, or string)

        Returns:
            128-dimensional embedding as numpy array

        Raises:
            ValueError: If embedding format is invalid or dimension mismatch
        """
        if isinstance(embedding, list):
            parsed_embedding = embedding
        else:
            parsed_embedding = EmbeddingService.parse_embedding(embedding)

        try:
            embedding_array = np.array(parsed_embedding, dtype=np.float64)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Failed to convert embedding to numpy array: {str(e)}, "
                f"type: {type(parsed_embedding)}"
            )

        if len(embedding_array) != 128:
            raise ValueError(
                f"Expected 128-dimensional embedding, got {len(embedding_array)} dimensions"
            )

        return embedding_array

    @staticmethod
    def parse_embedding(embedding: any) -> List[float]:
        """
        Parse embedding from various formats to list of floats.

        Args:
            embedding: Embedding in various formats (list, numpy array, string, JSON)

        Returns:
            Embedding as list of floats

        Raises:
            ValueError: If parsing fails or format is unsupported
        """
        if embedding is None:
            raise ValueError("Embedding cannot be None")

        if isinstance(embedding, list):
            return embedding

        if isinstance(embedding, np.ndarray):
            return embedding.tolist()

        if isinstance(embedding, str):
            import json
            try:
                parsed = json.loads(embedding)
                if isinstance(parsed, list):
                    return parsed
                raise ValueError(f"Parsed embedding is not a list, got {type(parsed)}")
            except json.JSONDecodeError:
                embedding_clean = embedding.strip('[]').replace(' ', '')
                try:
                    return [float(x) for x in embedding_clean.split(',') if x]
                except Exception as parse_error:
                    raise ValueError(
                        f"Failed to parse embedding string: {str(parse_error)}"
                    )

        raise ValueError(f"Unsupported embedding type: {type(embedding)}")

    @staticmethod
    def compare_embeddings(
        embedding_1: any,
        embedding_2: any,
        tolerance: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Compare two face embeddings for similarity using Euclidean distance.

        Args:
            embedding_1: First embedding (128-dimensional)
            embedding_2: Second embedding (128-dimensional)
            tolerance: Similarity threshold (defaults to config value)

        Returns:
            Tuple of (is_match: bool, distance: float)

        Raises:
            ValueError: If embeddings cannot be parsed or compared
        """
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        try:
            parsed_embedding_1 = (
                EmbeddingService.parse_embedding(embedding_1)
                if not isinstance(embedding_1, list)
                else embedding_1
            )
            parsed_embedding_2 = (
                EmbeddingService.parse_embedding(embedding_2)
                if not isinstance(embedding_2, list)
                else embedding_2
            )
        except ValueError as e:
            raise ValueError(f"Failed to parse embeddings for comparison: {str(e)}")

        face_encoding_1 = EmbeddingService.validate_embedding_128(parsed_embedding_1)
        face_encoding_2 = EmbeddingService.validate_embedding_128(parsed_embedding_2)

        distance = np.linalg.norm(face_encoding_1 - face_encoding_2)
        match = distance <= tolerance

        return match, float(distance)

    @staticmethod
    def calculate_cosine_similarity(
        embedding_1: List[float],
        embedding_2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding_1: First embedding (128-dimensional)
            embedding_2: Second embedding (128-dimensional)

        Returns:
            Cosine similarity score (1.0 = identical, 0.0 = orthogonal, -1.0 = opposite)
        """
        vec1 = np.array(embedding_1, dtype=np.float64)
        vec2 = np.array(embedding_2, dtype=np.float64)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
