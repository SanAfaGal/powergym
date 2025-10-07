"""
Image processing utilities for face recognition.
Handles image decoding, validation, compression, and thumbnail generation.
"""

import base64
import io
from typing import Tuple
import numpy as np
from PIL import Image

from app.core.config import settings


class ImageProcessor:
    """Handles all image processing operations for face recognition."""

    @staticmethod
    def validate_image_size(image_data: bytes) -> None:
        """
        Validate that image size is within allowed limits.

        Args:
            image_data: Raw image bytes

        Raises:
            ValueError: If image exceeds maximum size
        """
        max_size_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(image_data) > max_size_bytes:
            raise ValueError(
                f"Image size exceeds maximum allowed size of {settings.MAX_IMAGE_SIZE_MB}MB"
            )

    @staticmethod
    def decode_base64_image(image_base64: str) -> np.ndarray:
        """
        Decode base64 image string to numpy array.

        Args:
            image_base64: Base64 encoded image string (with or without data URI prefix)

        Returns:
            Image as numpy array in RGB format

        Raises:
            ValueError: If image format is invalid or decoding fails
        """
        try:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            image_bytes = base64.b64decode(image_base64)
            ImageProcessor.validate_image_size(image_bytes)

            image = Image.open(io.BytesIO(image_bytes))

            image_format = image.format.lower() if image.format else 'unknown'
            allowed_formats_lower = [fmt.lower() for fmt in settings.ALLOWED_IMAGE_FORMATS]

            if image_format not in allowed_formats_lower:
                raise ValueError(
                    f"Invalid image format '{image_format}'. "
                    f"Allowed formats: {settings.ALLOWED_IMAGE_FORMATS}"
                )

            image_rgb = image.convert('RGB')
            return np.array(image_rgb)

        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")

    @staticmethod
    def create_thumbnail(
        image_array: np.ndarray,
        size: Tuple[int, int] = (150, 150)
    ) -> bytes:
        """
        Create a thumbnail from an image array.

        Args:
            image_array: Image as numpy array
            size: Thumbnail dimensions (width, height)

        Returns:
            Thumbnail image as JPEG bytes

        Raises:
            ValueError: If thumbnail creation fails
        """
        try:
            image_pil = Image.fromarray(image_array)
            image_pil.thumbnail(size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            image_pil.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to create thumbnail: {str(e)}")

    @staticmethod
    def compress_image(image_array: np.ndarray, quality: int = 85) -> bytes:
        """
        Compress an image array to JPEG format.

        Args:
            image_array: Image as numpy array
            quality: JPEG quality (1-100)

        Returns:
            Compressed image as JPEG bytes

        Raises:
            ValueError: If compression fails
        """
        try:
            image_pil = Image.fromarray(image_array)
            buffer = io.BytesIO()
            image_pil.save(buffer, format='JPEG', quality=quality)
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to compress image: {str(e)}")
