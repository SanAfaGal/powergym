import base64
from typing import Optional, List
from uuid import UUID
from app.core.database import get_supabase_client
from app.core.encryption import get_encryption_service
from app.models.biometric import (
    BiometricCreate,
    BiometricUpdate,
    Biometric,
    BiometricType,
    BiometricSearchResult
)


class BiometricService:
    """
    Service for managing biometric data with encryption support.
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
            supabase = get_supabase_client()
            encryption_service = get_encryption_service()

            encrypted_compressed_data = encryption_service.encrypt_image_data(
                biometric_data.compressed_data
            )

            encrypted_thumbnail = None
            if biometric_data.thumbnail:
                encrypted_thumbnail = encryption_service.encrypt_image_data(
                    biometric_data.thumbnail
                )

            encrypted_embedding = None
            if biometric_data.embedding:
                encrypted_embedding = encryption_service.encrypt_embedding(
                    biometric_data.embedding
                )

            meta_info = biometric_data.meta_info.copy()
            meta_info["encryption"] = "AES-256-GCM"

            data = {
                "client_id": str(biometric_data.client_id),
                "type": biometric_data.type.value,
                "compressed_data": encrypted_compressed_data,
                "thumbnail": encrypted_thumbnail,
                "embedding": encrypted_embedding,
                "is_active": True,
                "meta_info": meta_info
            }

            response = supabase.table("client_biometrics").insert(data).execute()

            if response and response.data:
                record = response.data[0]
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
            supabase = get_supabase_client()

            response = supabase.table("client_biometrics").select(
                "*"
            ).eq("id", str(biometric_id)).maybe_single().execute()

            if response and response.data:
                return BiometricService._decrypt_biometric_record(response.data)

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
            supabase = get_supabase_client()

            query = supabase.table("client_biometrics").select("*").eq(
                "client_id", str(client_id)
            )

            if biometric_type:
                query = query.eq("type", biometric_type.value)

            if active_only:
                query = query.eq("is_active", True)

            response = query.execute()

            if response and response.data:
                return [
                    BiometricService._decrypt_biometric_record(record)
                    for record in response.data
                ]

            return []
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
            supabase = get_supabase_client()
            encryption_service = get_encryption_service()

            data = {}

            if update_data.compressed_data is not None:
                data["compressed_data"] = encryption_service.encrypt_image_data(
                    update_data.compressed_data
                )

            if update_data.thumbnail is not None:
                data["thumbnail"] = encryption_service.encrypt_image_data(
                    update_data.thumbnail
                )

            if update_data.embedding is not None:
                data["embedding"] = encryption_service.encrypt_embedding(
                    update_data.embedding
                )

            if update_data.is_active is not None:
                data["is_active"] = update_data.is_active

            if update_data.meta_info is not None:
                meta_info = update_data.meta_info.copy()
                meta_info["encryption"] = "AES-256-GCM"
                data["meta_info"] = meta_info

            if not data:
                return BiometricService.get_biometric(biometric_id)

            response = supabase.table("client_biometrics").update(data).eq(
                "id", str(biometric_id)
            ).execute()

            if response and response.data:
                return BiometricService._decrypt_biometric_record(response.data[0])

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
            supabase = get_supabase_client()

            response = supabase.table("client_biometrics").update({
                "is_active": False
            }).eq("id", str(biometric_id)).execute()

            return bool(response and response.data)
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
            import numpy as np
            supabase = get_supabase_client()
            encryption_service = get_encryption_service()

            query = supabase.table("client_biometrics").select(
                "*"
            ).eq("is_active", True)

            if biometric_type:
                query = query.eq("type", biometric_type.value)

            response = query.execute()

            if not response or not response.data:
                return []

            results = []
            embedding_array = np.array(embedding)

            for record in response.data:
                if not record.get("embedding"):
                    continue

                try:
                    stored_embedding = encryption_service.decrypt_embedding(
                        record["embedding"]
                    )
                    stored_array = np.array(stored_embedding)

                    distance = np.linalg.norm(embedding_array - stored_array)
                    similarity = max(0.0, 1.0 - distance)

                    if similarity >= similarity_threshold:
                        biometric = BiometricService._decrypt_biometric_record(record)

                        client_response = supabase.table("clients").select(
                            "*"
                        ).eq("id", record["client_id"]).maybe_single().execute()

                        client_info = None
                        if client_response and client_response.data:
                            client_info = client_response.data

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
    def _decrypt_biometric_record(record: dict) -> Biometric:
        """
        Decrypt a biometric record from database.

        Args:
            record: Raw database record

        Returns:
            Decrypted Biometric object
        """
        try:
            encryption_service = get_encryption_service()

            meta_info = record.get("meta_info", {})
            is_encrypted = meta_info.get("encryption") == "AES-256-GCM"

            if is_encrypted:
                compressed_data = encryption_service.decrypt_image_data(
                    record["compressed_data"]
                )

                thumbnail = None
                if record.get("thumbnail"):
                    thumbnail = encryption_service.decrypt_image_data(
                        record["thumbnail"]
                    )

                embedding = None
                if record.get("embedding"):
                    embedding = encryption_service.decrypt_embedding(
                        record["embedding"]
                    )
            else:
                compressed_data = base64.b64decode(record["compressed_data"])

                thumbnail = None
                if record.get("thumbnail"):
                    thumbnail = base64.b64decode(record["thumbnail"])

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
