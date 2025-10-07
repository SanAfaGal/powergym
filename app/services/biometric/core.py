"""
Core biometric service combining all operations.
Provides high-level API for biometric data management.
"""

from typing import Optional, List
from uuid import UUID

from app.models.biometric import (
    BiometricCreate,
    BiometricUpdate,
    Biometric,
    BiometricType,
    BiometricSearchResult
)
from .database import BiometricDatabase
from .encryption import BiometricEncryption
from .search import BiometricSearch


class BiometricService:
    """
    Main service for managing biometric data with encryption support.
    Handles storage, retrieval, and search of encrypted biometric information.
    """

    @staticmethod
    def create_biometric(biometric_data: BiometricCreate) -> Optional[Biometric]:
        """
        Create a new biometric record with encrypted data.

        Args:
            biometric_data: Biometric data to create

        Returns:
            Created Biometric object or None if failed
        """
        try:
            encrypted_compressed_data, encrypted_thumbnail, encrypted_embedding = (
                BiometricEncryption.encrypt_biometric_data(
                    compressed_data=biometric_data.compressed_data,
                    thumbnail=biometric_data.thumbnail,
                    embedding=biometric_data.embedding
                )
            )

            meta_info = biometric_data.meta_info.copy()
            meta_info["encryption"] = "AES-256-GCM"

            record = BiometricDatabase.insert_biometric(
                client_id=biometric_data.client_id,
                biometric_type=biometric_data.type,
                encrypted_compressed_data=encrypted_compressed_data,
                encrypted_thumbnail=encrypted_thumbnail,
                encrypted_embedding=encrypted_embedding,
                meta_info=meta_info
            )

            if record:
                return BiometricService._decrypt_biometric_record(record)

            return None

        except Exception as e:
            print(f"Error creating biometric: {str(e)}")
            return None

    @staticmethod
    def get_biometric(biometric_id: UUID) -> Optional[Biometric]:
        """
        Retrieve a biometric record by ID and decrypt it.

        Args:
            biometric_id: UUID of the biometric record

        Returns:
            Decrypted Biometric object or None if not found
        """
        try:
            record = BiometricDatabase.get_biometric_by_id(biometric_id)

            if record:
                return BiometricService._decrypt_biometric_record(record)

            return None

        except Exception as e:
            print(f"Error retrieving biometric: {str(e)}")
            return None

    @staticmethod
    def get_biometrics_by_client(
        client_id: UUID,
        biometric_type: Optional[BiometricType] = None,
        active_only: bool = True
    ) -> List[Biometric]:
        """
        Retrieve all biometric records for a client.

        Args:
            client_id: UUID of the client
            biometric_type: Optional filter by biometric type
            active_only: Only return active records

        Returns:
            List of decrypted Biometric objects
        """
        try:
            records = BiometricDatabase.get_biometrics_by_client(
                client_id=client_id,
                biometric_type=biometric_type,
                active_only=active_only
            )

            return [
                BiometricService._decrypt_biometric_record(record)
                for record in records
            ]

        except Exception as e:
            print(f"Error retrieving biometrics: {str(e)}")
            return []

    @staticmethod
    def update_biometric(
        biometric_id: UUID,
        update_data: BiometricUpdate
    ) -> Optional[Biometric]:
        """
        Update a biometric record with encrypted data.

        Args:
            biometric_id: UUID of the biometric to update
            update_data: Update data

        Returns:
            Updated Biometric object or None if failed
        """
        try:
            data = {}

            if update_data.compressed_data is not None:
                encrypted_compressed_data, _, _ = (
                    BiometricEncryption.encrypt_biometric_data(
                        compressed_data=update_data.compressed_data
                    )
                )
                data["compressed_data"] = encrypted_compressed_data

            if update_data.thumbnail is not None:
                _, encrypted_thumbnail, _ = BiometricEncryption.encrypt_biometric_data(
                    compressed_data=b"",
                    thumbnail=update_data.thumbnail
                )
                data["thumbnail"] = encrypted_thumbnail

            if update_data.embedding is not None:
                _, _, encrypted_embedding = BiometricEncryption.encrypt_biometric_data(
                    compressed_data=b"",
                    embedding=update_data.embedding
                )
                data["embedding"] = encrypted_embedding

            if update_data.is_active is not None:
                data["is_active"] = update_data.is_active

            if update_data.meta_info is not None:
                meta_info = update_data.meta_info.copy()
                meta_info["encryption"] = "AES-256-GCM"
                data["meta_info"] = meta_info

            record = BiometricDatabase.update_biometric(biometric_id, data)

            if record:
                return BiometricService._decrypt_biometric_record(record)

            return None

        except Exception as e:
            print(f"Error updating biometric: {str(e)}")
            return None

    @staticmethod
    def delete_biometric(biometric_id: UUID) -> bool:
        """
        Soft delete a biometric record by setting is_active to False.

        Args:
            biometric_id: UUID of the biometric to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            return BiometricDatabase.deactivate_biometric(biometric_id)
        except Exception as e:
            print(f"Error deleting biometric: {str(e)}")
            return False

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
            List of BiometricSearchResult objects
        """
        try:
            return BiometricSearch.search_by_embedding(
                embedding=embedding,
                biometric_type=biometric_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
        except Exception as e:
            print(f"Error searching by embedding: {str(e)}")
            return []

    @staticmethod
    def _decrypt_biometric_record(record: dict) -> Biometric:
        """
        Decrypt a biometric record from database.

        Args:
            record: Raw database record

        Returns:
            Decrypted Biometric object
        """
        try:
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

        except Exception as e:
            print(f"Error decrypting biometric record: {str(e)}")
            raise
