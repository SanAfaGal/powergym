"""
Search utilities for biometric data.
Handles similarity search and matching operations.
"""

from typing import List, Optional
import numpy as np

from app.models.biometric import BiometricType, BiometricSearchResult, Biometric
from .database import BiometricDatabase
from .encryption import BiometricEncryption


class BiometricSearch:
    """Handles search and similarity matching for biometric data."""

    @staticmethod
    def search_by_embedding(
        embedding: List[float],
        biometric_type: Optional[BiometricType] = None,
        limit: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[BiometricSearchResult]:
        """
        Search for similar biometric records by embedding.

        Args:
            embedding: Embedding vector to search for
            biometric_type: Optional filter by biometric type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of BiometricSearchResult objects sorted by similarity
        """
        try:
            records = BiometricDatabase.get_all_active_biometrics(biometric_type)

            if not records:
                return []

            results = []
            embedding_array = np.array(embedding)

            for record in records:
                if not record.get("embedding"):
                    continue

                try:
                    _, _, stored_embedding = BiometricEncryption.decrypt_biometric_data(
                        encrypted_compressed_data=record["compressed_data"],
                        encrypted_thumbnail=record.get("thumbnail"),
                        encrypted_embedding=record.get("embedding")
                    )

                    if stored_embedding is None:
                        continue

                    stored_array = np.array(stored_embedding)
                    distance = np.linalg.norm(embedding_array - stored_array)
                    similarity = max(0.0, 1.0 - distance)

                    if similarity >= similarity_threshold:
                        biometric = BiometricSearch._record_to_biometric(record)
                        client_info = BiometricDatabase.get_client_info(
                            record["client_id"]
                        )

                        results.append(BiometricSearchResult(
                            biometric=biometric,
                            similarity=similarity,
                            client_info=client_info
                        ))

                except Exception as e:
                    print(f"Error processing record: {str(e)}")
                    continue

            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"Error searching by embedding: {str(e)}")
            return []

    @staticmethod
    def _record_to_biometric(record: dict) -> Biometric:
        """
        Convert database record to Biometric object with decryption.

        Args:
            record: Raw database record

        Returns:
            Decrypted Biometric object
        """
        meta_info = record.get("meta_info", {})
        is_encrypted = meta_info.get("encryption") == "AES-256-GCM"

        if is_encrypted:
            compressed_data, thumbnail, embedding = (
                BiometricEncryption.decrypt_biometric_data(
                    encrypted_compressed_data=record["compressed_data"],
                    encrypted_thumbnail=record.get("thumbnail"),
                    encrypted_embedding=record.get("embedding")
                )
            )
        else:
            import base64
            compressed_data = base64.b64decode(record["compressed_data"])
            thumbnail = (
                base64.b64decode(record["thumbnail"])
                if record.get("thumbnail")
                else None
            )
            embedding = record.get("embedding")

        return Biometric(
            id=record["id"],
            client_id=record["client_id"],
            type=BiometricType(record["type"]),
            compressed_data=compressed_data,
            thumbnail=thumbnail,
            embedding=embedding,
            is_active=record["is_active"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            meta_info=meta_info
        )
