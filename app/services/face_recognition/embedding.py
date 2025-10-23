"""
Embedding generation and comparison utilities for face recognition.
Handles face encoding extraction and similarity calculations using InsightFace.
"""

from typing import List, Tuple, Optional
import numpy as np
import cv2
from insightface.app import FaceAnalysis

from app.core.config import settings
from app.core.async_processing import run_in_threadpool


class EmbeddingService:
    """Handles face embedding generation and comparison operations using InsightFace."""

    _app = None

    @classmethod
    def _get_face_analysis(cls):
        """Lazy initialization of InsightFace FaceAnalysis."""
        if cls._app is None:
            # Determinar provider según configuración
            providers = ['CPUExecutionProvider']
            if settings.INSIGHTFACE_CTX_ID >= 0:
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

            cls._app = FaceAnalysis(
                name=settings.INSIGHTFACE_MODEL,
                providers=providers
            )
            cls._app.prepare(
                ctx_id=settings.INSIGHTFACE_CTX_ID,
                det_size=(settings.INSIGHTFACE_DET_SIZE, settings.INSIGHTFACE_DET_SIZE)
            )
        return cls._app

    @staticmethod
    def extract_face_encoding(image_array: np.ndarray) -> np.ndarray:
        """
        Extract face encoding from an image array using InsightFace.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            512-dimensional face encoding as numpy array

        Raises:
            ValueError: If no face, multiple faces, or encoding extraction fails
        """
        app = EmbeddingService._get_face_analysis()

        # InsightFace espera BGR, convertir si viene en RGB
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # Verificar si ya está en BGR o necesita conversión
            # Asumimos que viene en RGB del frontend
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array

        # Detectar y extraer embeddings
        faces = app.get(image_bgr)

        if len(faces) == 0:
            raise ValueError("No face detected in the image")

        if len(faces) > 1:
            # Opcional: usar la cara más grande en lugar de error
            # faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
            # faces = [faces[0]]
            raise ValueError(
                f"Multiple faces detected ({len(faces)}). Please provide an image with a single face"
            )

        # El embedding ya viene normalizado con norma L2
        embedding = faces[0].normed_embedding

        # Convertir a float64 para consistencia
        return embedding.astype(np.float64)

    @staticmethod
    async def extract_face_encoding_async(image_array: np.ndarray) -> np.ndarray:
        """
        Extract face encoding asynchronously.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            512-dimensional face encoding as numpy array
        """
        return await run_in_threadpool(
            EmbeddingService.extract_face_encoding,
            image_array
        )

    @staticmethod
    def validate_embedding(embedding: any) -> np.ndarray:
        """
        Validate and convert embedding to numpy array with correct dimensions.

        Args:
            embedding: Embedding (list, numpy array, or string)

        Returns:
            Embedding as numpy array with dimensions from settings.EMBEDDING_DIMENSIONS

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

        expected_dim = settings.EMBEDDING_DIMENSIONS
        if len(embedding_array) != expected_dim:
            raise ValueError(
                f"Expected {expected_dim}-dimensional embedding, got {len(embedding_array)} dimensions"
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
        Compare two face embeddings for similarity using cosine similarity.

        InsightFace embeddings son L2-normalizados, por lo que usamos cosine similarity.

        Args:
            embedding_1: First embedding (512-dimensional)
            embedding_2: Second embedding (512-dimensional)
            tolerance: Similarity threshold (0.0-1.0, higher = more similar)
                      Default from config. Recommended: 0.4-0.5

        Returns:
            Tuple of (is_match: bool, similarity: float)
            - similarity: 1.0 = identical, 0.0 = orthogonal, -1.0 = opposite
            - is_match: True if similarity >= tolerance

        Raises:
            ValueError: If embeddings cannot be parsed or compared
        """
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        try:
            parsed_embedding_1 = (
                EmbeddingService.parse_embedding(embedding_1)
                if not isinstance(embedding_1, (list, np.ndarray))
                else embedding_1
            )
            parsed_embedding_2 = (
                EmbeddingService.parse_embedding(embedding_2)
                if not isinstance(embedding_2, (list, np.ndarray))
                else embedding_2
            )
        except ValueError as e:
            raise ValueError(f"Failed to parse embeddings for comparison: {str(e)}")

        face_encoding_1 = EmbeddingService.validate_embedding(parsed_embedding_1)
        face_encoding_2 = EmbeddingService.validate_embedding(parsed_embedding_2)

        # Calcular similitud coseno (dot product de vectores L2-normalizados)
        # Como InsightFace ya normaliza los embeddings, el dot product ES la similitud coseno
        similarity = float(np.dot(face_encoding_1, face_encoding_2))

        # Mayor similitud = match (opuesto a distancia euclidiana)
        match = similarity >= tolerance

        return match, similarity

    @staticmethod
    def calculate_euclidean_distance(
        embedding_1: List[float],
        embedding_2: List[float]
    ) -> float:
        """
        Calculate Euclidean distance between two embeddings.

        Note: Para InsightFace, cosine similarity es más apropiado.
        Esta función se mantiene por compatibilidad.

        Args:
            embedding_1: First embedding (512-dimensional)
            embedding_2: Second embedding (512-dimensional)

        Returns:
            Euclidean distance (lower = more similar)
        """
        vec1 = np.array(embedding_1, dtype=np.float64)
        vec2 = np.array(embedding_2, dtype=np.float64)

        distance = np.linalg.norm(vec1 - vec2)

        return float(distance)

    @staticmethod
    def calculate_cosine_similarity(
        embedding_1: List[float],
        embedding_2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding_1: First embedding (512-dimensional)
            embedding_2: Second embedding (512-dimensional)

        Returns:
            Cosine similarity score (1.0 = identical, 0.0 = orthogonal, -1.0 = opposite)
        """
        vec1 = np.array(embedding_1, dtype=np.float64)
        vec2 = np.array(embedding_2, dtype=np.float64)

        # Normalizar vectores
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Calcular similitud coseno
        similarity = np.dot(vec1, vec2) / (norm1 * norm2)

        return float(similarity)

    @staticmethod
    def get_face_quality_score(image_array: np.ndarray) -> dict:
        """
        Evaluar la calidad de una imagen facial para reconocimiento.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            Dictionary con métricas de calidad:
            - score: Puntuación general (0-1)
            - brightness: Nivel de brillo
            - sharpness: Nivel de nitidez
            - face_size: Tamaño de la cara detectada
            - recommendations: Lista de recomendaciones
        """
        app = EmbeddingService._get_face_analysis()

        # Convertir a BGR
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array

        faces = app.get(image_bgr)

        if len(faces) == 0:
            return {
                'score': 0.0,
                'brightness': None,
                'sharpness': None,
                'face_size': None,
                'recommendations': ['No face detected']
            }

        face = faces[0]
        recommendations = []

        # 1. Tamaño de la cara
        bbox = face.bbox.astype(int)
        face_width = bbox[2] - bbox[0]
        face_height = bbox[3] - bbox[1]
        face_area = face_width * face_height
        image_area = image_array.shape[0] * image_array.shape[1]
        face_ratio = face_area / image_area

        if face_ratio < 0.05:
            recommendations.append('Face is too small - move closer to camera')
        elif face_ratio > 0.8:
            recommendations.append('Face is too close - move back from camera')

        # 2. Brillo
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)

        if brightness < 80:
            recommendations.append('Image is too dark - improve lighting')
        elif brightness > 200:
            recommendations.append('Image is too bright - reduce lighting')

        # 3. Nitidez (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()

        if sharpness < 100:
            recommendations.append('Image is blurry - hold camera steady')

        # 4. Score general (normalizado 0-1)
        face_score = min(face_ratio * 10, 1.0)  # Optimal around 0.1-0.3
        brightness_score = 1.0 - abs(brightness - 140) / 140  # Optimal around 140
        sharpness_score = min(sharpness / 500, 1.0)  # Optimal > 500

        overall_score = (face_score + brightness_score + sharpness_score) / 3

        return {
            'score': float(overall_score),
            'brightness': float(brightness),
            'sharpness': float(sharpness),
            'face_size': float(face_ratio),
            'face_dimensions': {
                'width': int(face_width),
                'height': int(face_height)
            },
            'recommendations': recommendations if recommendations else ['Image quality is good']
        }

    @staticmethod
    def extract_multiple_faces(image_array: np.ndarray) -> List[dict]:
        """
        Detectar y extraer embeddings de múltiples caras en una imagen.

        Útil para fotos de grupo o registro masivo.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            Lista de diccionarios con información de cada cara:
            - embedding: Face embedding (512-dim)
            - bbox: Bounding box [x1, y1, x2, y2]
            - confidence: Detection confidence
            - landmarks: Facial landmarks
        """
        app = EmbeddingService._get_face_analysis()

        # Convertir a BGR
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array

        faces = app.get(image_bgr)

        results = []
        for face in faces:
            results.append({
                'embedding': face.normed_embedding.astype(np.float64).tolist(),
                'bbox': face.bbox.astype(int).tolist(),
                'confidence': float(face.det_score),
                'landmarks': face.kps.astype(int).tolist() if hasattr(face, 'kps') else None,
                'age': int(face.age) if hasattr(face, 'age') else None,
                'gender': 'M' if face.gender == 1 else 'F' if hasattr(face, 'gender') else None
            })

        return results

    @staticmethod
    def find_best_match(
        query_embedding: any,
        candidate_embeddings: List[any],
        tolerance: Optional[float] = None
    ) -> Tuple[Optional[int], float]:
        """
        Encontrar la mejor coincidencia entre un embedding de consulta y una lista de candidatos.

        Args:
            query_embedding: Embedding a buscar
            candidate_embeddings: Lista de embeddings candidatos
            tolerance: Umbral de similitud mínimo

        Returns:
            Tuple of (best_match_index: Optional[int], best_similarity: float)
            - best_match_index: Índice del mejor match, o None si ninguno supera el threshold
            - best_similarity: Similitud del mejor match
        """
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        query_emb = EmbeddingService.validate_embedding(query_embedding)

        best_similarity = -1.0
        best_index = None

        for idx, candidate in enumerate(candidate_embeddings):
            candidate_emb = EmbeddingService.validate_embedding(candidate)
            similarity = float(np.dot(query_emb, candidate_emb))

            if similarity > best_similarity:
                best_similarity = similarity
                best_index = idx

        # Solo retornar match si supera el threshold
        if best_similarity < tolerance:
            return None, best_similarity

        return best_index, best_similarity

    @staticmethod
    async def get_face_quality_score_async(image_array: np.ndarray) -> dict:
        """
        Evaluar la calidad de una imagen facial de forma asíncrona.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            Dictionary con métricas de calidad
        """
        return await run_in_threadpool(
            EmbeddingService.get_face_quality_score,
            image_array
        )

    @staticmethod
    async def extract_multiple_faces_async(image_array: np.ndarray) -> List[dict]:
        """
        Detectar y extraer embeddings de múltiples caras de forma asíncrona.

        Args:
            image_array: Image as numpy array in RGB format

        Returns:
            Lista de diccionarios con información de cada cara
        """
        return await run_in_threadpool(
            EmbeddingService.extract_multiple_faces,
            image_array
        )

    @staticmethod
    async def find_best_match_async(
        query_embedding: any,
        candidate_embeddings: List[any],
        tolerance: Optional[float] = None
    ) -> Tuple[Optional[int], float]:
        """
        Encontrar la mejor coincidencia de forma asíncrona.

        Args:
            query_embedding: Embedding a buscar
            candidate_embeddings: Lista de embeddings candidatos
            tolerance: Umbral de similitud mínimo

        Returns:
            Tuple of (best_match_index: Optional[int], best_similarity: float)
        """
        return await run_in_threadpool(
            EmbeddingService.find_best_match,
            query_embedding,
            candidate_embeddings,
            tolerance
        )