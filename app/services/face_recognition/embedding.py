"""
Embedding generation and comparison utilities for face recognition.
Handles face encoding extraction and similarity calculations.
"""

from typing import List, Tuple, Optional
import numpy as np
import face_recognition

from app.core.config import settings
from app.core.async_processing import run_in_threadpool


class EmbeddingService:
    """Handles face embedding generation and comparison operations."""

    @staticmethod
    def extract_face_encoding(image_array: np.ndarray) -> np.ndarray:
        """
        Extract face encoding from an image array.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            128-dimensional face encoding as numpy array

        Raises:
            ValueError: If no face, multiple faces, or encoding extraction fails
        """
        face_locations = face_recognition.face_locations(
            image_array,
            model=settings.FACE_RECOGNITION_MODEL
        )

        if len(face_locations) == 0:
            raise ValueError("No face detected in the image")

        if len(face_locations) > 1:
            raise ValueError(
                "Multiple faces detected. Please provide an image with a single face"
            )

        face_encodings = face_recognition.face_encodings(
            image_array,
            known_face_locations=face_locations,
            num_jitters=2
        )

        if len(face_encodings) == 0:
            raise ValueError("Could not extract face encoding from the detected face")

        return face_encodings[0]

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
