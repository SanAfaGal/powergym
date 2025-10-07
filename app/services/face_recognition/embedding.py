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
    def expand_embedding_to_512(embedding_128: List[float]) -> List[float]:
        """
        Expand 128-dimensional embedding to 512 dimensions for database storage.

        Args:
            embedding_128: 128-dimensional face encoding

        Returns:
            512-dimensional embedding as list
        """
        embedding_array = np.array(embedding_128)
        repeated = np.tile(embedding_array, 4)
        embedding_512 = repeated[:512].tolist()
        return embedding_512

    @staticmethod
    def compress_embedding_from_512(embedding_512: any) -> np.ndarray:
        """
        Compress 512-dimensional embedding back to 128 dimensions.

        Args:
            embedding_512: 512-dimensional embedding (list, numpy array, or string)

        Returns:
            128-dimensional embedding as numpy array

        Raises:
            ValueError: If embedding format is invalid or dimension mismatch
        """
        if isinstance(embedding_512, list):
            parsed_embedding = embedding_512
        else:
            parsed_embedding = EmbeddingService.parse_embedding(embedding_512)

        try:
            embedding_array = np.array(parsed_embedding, dtype=np.float64)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Failed to convert embedding to numpy array: {str(e)}, "
                f"type: {type(parsed_embedding)}"
            )

        if len(embedding_array) != 512:
            raise ValueError(
                f"Expected 512-dimensional embedding, got {len(embedding_array)} dimensions"
            )

        embedding_array = embedding_array[:128]
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
        Compare two face embeddings for similarity.

        Args:
            embedding_1: First embedding (512-dimensional)
            embedding_2: Second embedding (512-dimensional)
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

        face_encoding_1 = EmbeddingService.compress_embedding_from_512(parsed_embedding_1)
        face_encoding_2 = EmbeddingService.compress_embedding_from_512(parsed_embedding_2)

        distance = np.linalg.norm(face_encoding_1 - face_encoding_2)
        match = distance <= tolerance

        return match, float(distance)
