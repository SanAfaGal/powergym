"""
Compression service for biometric data and images.
Handles compression of embeddings, images, and thumbnails before encryption.
"""

import zlib
import json
import io
from typing import List, Tuple
from PIL import Image
import numpy as np

from app.core.config import settings


class CompressionService:
    """
    Service for compressing biometric data before encryption.
    Uses zlib for embedding compression and optimized JPEG for images.
    """

    @staticmethod
    def compress_embedding(embedding: List[float], level: int = 9) -> bytes:
        """
        Compress a face embedding vector using zlib.

        JSON arrays of floats compress very well (typically 70-80% reduction).

        Args:
            embedding: List of float values representing the embedding
            level: Compression level (0-9, where 9 is maximum compression)

        Returns:
            Compressed bytes

        Raises:
            ValueError: If compression fails
        """
        if not embedding:
            raise ValueError("Embedding cannot be empty")

        try:
            embedding_json = json.dumps(embedding)
            embedding_bytes = embedding_json.encode('utf-8')

            compressed = zlib.compress(embedding_bytes, level=level)

            return compressed
        except Exception as e:
            raise ValueError(f"Failed to compress embedding: {str(e)}")

    @staticmethod
    def decompress_embedding(compressed_data: bytes) -> List[float]:
        """
        Decompress a compressed embedding vector.

        Args:
            compressed_data: Compressed embedding bytes

        Returns:
            Original embedding as list of floats

        Raises:
            ValueError: If decompression fails
        """
        if not compressed_data:
            raise ValueError("Compressed data cannot be empty")

        try:
            decompressed_bytes = zlib.decompress(compressed_data)
            embedding_json = decompressed_bytes.decode('utf-8')
            embedding = json.loads(embedding_json)

            if not isinstance(embedding, list):
                raise ValueError("Decompressed data is not a list")

            return embedding
        except Exception as e:
            raise ValueError(f"Failed to decompress embedding: {str(e)}")

    @staticmethod
    def compress_image(
        image_array: np.ndarray,
        quality: int = None,
        optimize: bool = True
    ) -> bytes:
        """
        Compress an image array to optimized JPEG format.

        Args:
            image_array: Image as numpy array
            quality: JPEG quality (1-100). Defaults to config value.
            optimize: Enable JPEG optimization (slower but smaller files)

        Returns:
            Compressed image as JPEG bytes

        Raises:
            ValueError: If compression fails
        """
        if quality is None:
            quality = settings.IMAGE_COMPRESSION_QUALITY

        try:
            image_pil = Image.fromarray(image_array)

            buffer = io.BytesIO()
            image_pil.save(
                buffer,
                format='JPEG',
                quality=quality,
                optimize=optimize,
                progressive=True
            )

            compressed_bytes = buffer.getvalue()

            return compressed_bytes
        except Exception as e:
            raise ValueError(f"Failed to compress image: {str(e)}")

    @staticmethod
    def compress_thumbnail(
        image_array: np.ndarray,
        size: Tuple[int, int] = None,
        quality: int = None
    ) -> bytes:
        """
        Create and compress a thumbnail with aggressive optimization.
        Thumbnails are preview images, so we use lower quality for smaller size.

        Args:
            image_array: Image as numpy array
            size: Thumbnail dimensions (width, height). Defaults to config value.
            quality: JPEG quality (1-100). Defaults to config value.

        Returns:
            Compressed thumbnail as JPEG bytes

        Raises:
            ValueError: If thumbnail creation fails
        """
        if size is None:
            size = (
                settings.THUMBNAIL_WIDTH,
                settings.THUMBNAIL_HEIGHT
            )

        if quality is None:
            quality = settings.THUMBNAIL_COMPRESSION_QUALITY

        try:
            image_pil = Image.fromarray(image_array)

            image_pil.thumbnail(size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            image_pil.save(
                buffer,
                format='JPEG',
                quality=quality,
                optimize=True,
                progressive=True
            )

            compressed_bytes = buffer.getvalue()

            return compressed_bytes
        except Exception as e:
            raise ValueError(f"Failed to create compressed thumbnail: {str(e)}")

    @staticmethod
    def get_compression_ratio(original_size: int, compressed_size: int) -> float:
        """
        Calculate compression ratio.

        Args:
            original_size: Original data size in bytes
            compressed_size: Compressed data size in bytes

        Returns:
            Compression ratio as percentage (e.g., 75.5 means 75.5% reduction)
        """
        if original_size == 0:
            return 0.0

        reduction = original_size - compressed_size
        ratio = (reduction / original_size) * 100

        return round(ratio, 2)

    @staticmethod
    def get_compression_stats(
        original_embedding: List[float],
        compressed_embedding: bytes,
        original_image: bytes,
        compressed_image: bytes,
        thumbnail: bytes
    ) -> dict:
        """
        Calculate compression statistics for monitoring and optimization.

        Args:
            original_embedding: Original embedding list
            compressed_embedding: Compressed embedding bytes
            original_image: Original image bytes
            compressed_image: Compressed image bytes
            thumbnail: Compressed thumbnail bytes

        Returns:
            Dictionary with compression statistics
        """
        original_embedding_size = len(json.dumps(original_embedding).encode('utf-8'))
        compressed_embedding_size = len(compressed_embedding)

        original_image_size = len(original_image)
        compressed_image_size = len(compressed_image)
        thumbnail_size = len(thumbnail)

        embedding_ratio = CompressionService.get_compression_ratio(
            original_embedding_size,
            compressed_embedding_size
        )

        image_ratio = CompressionService.get_compression_ratio(
            original_image_size,
            compressed_image_size
        )

        total_original = original_embedding_size + original_image_size
        total_compressed = compressed_embedding_size + compressed_image_size + thumbnail_size
        total_ratio = CompressionService.get_compression_ratio(
            total_original,
            total_compressed
        )

        return {
            "embedding": {
                "original_size_bytes": original_embedding_size,
                "compressed_size_bytes": compressed_embedding_size,
                "compression_ratio_percent": embedding_ratio
            },
            "image": {
                "original_size_bytes": original_image_size,
                "compressed_size_bytes": compressed_image_size,
                "compression_ratio_percent": image_ratio
            },
            "thumbnail": {
                "size_bytes": thumbnail_size
            },
            "total": {
                "original_size_bytes": total_original,
                "compressed_size_bytes": total_compressed,
                "compression_ratio_percent": total_ratio,
                "saved_bytes": total_original - total_compressed
            }
        }
