import face_recognition
import numpy as np
import base64
import io
from PIL import Image
from typing import Optional, List, Tuple
from app.core.config import settings
from app.core.database import get_supabase_client
from app.models.biometric import BiometricType
from uuid import UUID
from app.core.async_processing import run_in_threadpool

class FaceRecognitionService:

    @staticmethod
    def _validate_image_size(image_data: bytes) -> None:
        max_size_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(image_data) > max_size_bytes:
            raise ValueError(f"Image size exceeds maximum allowed size of {settings.MAX_IMAGE_SIZE_MB}MB")

    @staticmethod
    def _decode_base64_image(image_base64: str) -> np.ndarray:
        try:
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            image_bytes = base64.b64decode(image_base64)
            FaceRecognitionService._validate_image_size(image_bytes)

            image = Image.open(io.BytesIO(image_bytes))

            image_format = image.format.lower() if image.format else 'unknown'
            allowed_formats_lower = [fmt.lower() for fmt in settings.ALLOWED_IMAGE_FORMATS]

            if image_format not in allowed_formats_lower:
                raise ValueError(f"Invalid image format '{image_format}'. Allowed formats: {settings.ALLOWED_IMAGE_FORMATS}")

            image_rgb = image.convert('RGB')
            return np.array(image_rgb)

        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")

    @staticmethod
    def _create_thumbnail(image_array: np.ndarray, size: Tuple[int, int] = (150, 150)) -> bytes:
        try:
            image_pil = Image.fromarray(image_array)
            image_pil.thumbnail(size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            image_pil.save(buffer, format='JPEG', quality=85)
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to create thumbnail: {str(e)}")

    @staticmethod
    def _compress_image(image_array: np.ndarray, quality: int = 85) -> bytes:
        try:
            image_pil = Image.fromarray(image_array)
            buffer = io.BytesIO()
            image_pil.save(buffer, format='JPEG', quality=quality)
            return buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to compress image: {str(e)}")

    @staticmethod
    def extract_face_encoding(image_base64: str) -> Tuple[List[float], bytes, bytes]:
        image_array = FaceRecognitionService._decode_base64_image(image_base64)

        face_locations = face_recognition.face_locations(
            image_array,
            model=settings.FACE_RECOGNITION_MODEL
        )

        if len(face_locations) == 0:
            raise ValueError("No face detected in the image")

        if len(face_locations) > 1:
            raise ValueError("Multiple faces detected. Please provide an image with a single face")

        face_encodings = face_recognition.face_encodings(
            image_array,
            known_face_locations=face_locations,
            num_jitters=2
        )

        if len(face_encodings) == 0:
            raise ValueError("Could not extract face encoding from the detected face")

        face_encoding = face_encodings[0]

        embedding_128 = face_encoding.tolist()
        embedding_512 = FaceRecognitionService._expand_embedding_to_512(embedding_128)

        compressed_data = FaceRecognitionService._compress_image(image_array)
        thumbnail = FaceRecognitionService._create_thumbnail(image_array)

        return embedding_512, compressed_data, thumbnail

    @staticmethod
    async def extract_face_encoding_async(image_base64: str) -> Tuple[List[float], bytes, bytes]:
        return await run_in_threadpool(
            FaceRecognitionService.extract_face_encoding,
            image_base64
        )

    @staticmethod
    def _expand_embedding_to_512(embedding_128: List[float]) -> List[float]:
        embedding_array = np.array(embedding_128)

        repeated = np.tile(embedding_array, 4)

        embedding_512 = repeated[:512].tolist()

        return embedding_512

    @staticmethod
    def _parse_embedding(embedding: any) -> List[float]:
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
            except json.JSONDecodeError as e:
                embedding_clean = embedding.strip('[]').replace(' ', '')
                try:
                    return [float(x) for x in embedding_clean.split(',') if x]
                except Exception as parse_error:
                    raise ValueError(f"Failed to parse embedding string: {str(parse_error)}")

        raise ValueError(f"Unsupported embedding type: {type(embedding)}")

    @staticmethod
    def _compress_embedding_from_512(embedding_512: any) -> np.ndarray:
        if isinstance(embedding_512, list):
            parsed_embedding = embedding_512
        else:
            parsed_embedding = FaceRecognitionService._parse_embedding(embedding_512)

        try:
            embedding_array = np.array(parsed_embedding, dtype=np.float64)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Failed to convert embedding to numpy array: {str(e)}, type: {type(parsed_embedding)}")

        if len(embedding_array) != 512:
            raise ValueError(f"Expected 512-dimensional embedding, got {len(embedding_array)} dimensions")

        embedding_array = embedding_array[:128]

        return embedding_array

    @staticmethod
    def compare_faces(embedding_1: any, embedding_2: any, tolerance: Optional[float] = None) -> Tuple[bool, float]:
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        try:
            parsed_embedding_1 = FaceRecognitionService._parse_embedding(embedding_1) if not isinstance(embedding_1, list) else embedding_1
            parsed_embedding_2 = FaceRecognitionService._parse_embedding(embedding_2) if not isinstance(embedding_2, list) else embedding_2
        except ValueError as e:
            raise ValueError(f"Failed to parse embeddings for comparison: {str(e)}")

        face_encoding_1 = FaceRecognitionService._compress_embedding_from_512(parsed_embedding_1)
        face_encoding_2 = FaceRecognitionService._compress_embedding_from_512(parsed_embedding_2)

        distance = np.linalg.norm(face_encoding_1 - face_encoding_2)

        match = distance <= tolerance
        confidence = max(0.0, 1.0 - distance)

        return match, float(distance)

    @staticmethod
    def register_face(client_id: UUID, image_base64: str) -> dict:
        try:
            embedding, compressed_data, thumbnail = FaceRecognitionService.extract_face_encoding(image_base64)

            supabase = get_supabase_client()

            existing_response = supabase.table("client_biometrics").select("id").eq(
                "client_id", str(client_id)
            ).eq("type", BiometricType.FACE.value).eq("is_active", True).maybe_single().execute()

            if existing_response and existing_response.data:
                supabase.table("client_biometrics").update({
                    "is_active": False
                }).eq("id", existing_response.data["id"]).execute()

            compressed_data_b64 = base64.b64encode(compressed_data).decode('utf-8')
            thumbnail_b64 = base64.b64encode(thumbnail).decode('utf-8')

            biometric_data = {
                "client_id": str(client_id),
                "type": BiometricType.FACE.value,
                "compressed_data": compressed_data_b64,
                "thumbnail": thumbnail_b64,
                "embedding": embedding,
                "is_active": True,
                "meta_info": {
                    "encoding_version": "face_recognition_v1",
                    "model": settings.FACE_RECOGNITION_MODEL
                }
            }

            response = supabase.table("client_biometrics").insert(biometric_data).execute()

            if response and response.data:
                return {
                    "success": True,
                    "biometric_id": response.data[0]["id"],
                    "client_id": str(client_id)
                }

            raise Exception("Failed to store biometric data")

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
    def authenticate_face(image_base64: str, tolerance: Optional[float] = None) -> dict:
        try:
            embedding, _, _ = FaceRecognitionService.extract_face_encoding(image_base64)

            supabase = get_supabase_client()

            response = supabase.table("client_biometrics").select(
                "id, client_id, embedding"
            ).eq("type", BiometricType.FACE.value).eq("is_active", True).execute()

            if not response or not response.data:
                return {
                    "success": False,
                    "error": "No registered faces found in the system"
                }

            best_match = None
            best_distance = float('inf')

            for biometric in response.data:
                if not biometric.get("embedding"):
                    continue

                try:
                    stored_embedding = FaceRecognitionService._parse_embedding(biometric["embedding"])
                except ValueError as parse_error:
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
                client_response = supabase.table("clients").select("*").eq(
                    "id", best_match["client_id"]
                ).eq("is_active", True).maybe_single().execute()

                if client_response and client_response.data:
                    confidence = max(0.0, 1.0 - best_distance)

                    return {
                        "success": True,
                        "client_id": best_match["client_id"],
                        "client_info": client_response.data,
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
    def update_face(client_id: UUID, image_base64: str) -> dict:
        return FaceRecognitionService.register_face(client_id, image_base64)

    @staticmethod
    def delete_face(client_id: UUID) -> dict:
        try:
            supabase = get_supabase_client()

            response = supabase.table("client_biometrics").update({
                "is_active": False
            }).eq("client_id", str(client_id)).eq(
                "type", BiometricType.FACE.value
            ).execute()

            if response:
                return {
                    "success": True,
                    "message": "Face biometric deactivated successfully"
                }

            return {
                "success": False,
                "error": "Failed to deactivate face biometric"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Deletion failed: {str(e)}"
            }

    @staticmethod
    def compare_two_faces(image_base64_1: str, image_base64_2: str, tolerance: Optional[float] = None) -> dict:
        try:
            embedding_1, _, _ = FaceRecognitionService.extract_face_encoding(image_base64_1)
            embedding_2, _, _ = FaceRecognitionService.extract_face_encoding(image_base64_2)

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
