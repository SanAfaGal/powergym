from sqlalchemy.orm import Session
from app.models.client import (
    Client, ClientCreate, ClientUpdate, DocumentType, GenderType
)
from app.models.client_dashboard import (
    ClientDashboard, BiometricInfo, SubscriptionInfo, ClientStats
)
from app.repositories.client_repository import ClientRepository
from app.db.models import DocumentTypeEnum, GenderTypeEnum, BiometricTypeEnum, ClientBiometricModel
from app.core.encryption import get_encryption_service
from uuid import UUID
from typing import List, Optional
import base64

class ClientService:

    @staticmethod
    def create_client(db: Session, client_data: ClientCreate) -> Client | None:
        dni_type_enum = DocumentTypeEnum[client_data.dni_type.value]
        gender_enum = GenderTypeEnum[client_data.gender.value.upper()]

        client_model = ClientRepository.create(
            db=db,
            dni_type=dni_type_enum,
            dni_number=client_data.dni_number,
            first_name=client_data.first_name,
            middle_name=client_data.middle_name,
            last_name=client_data.last_name,
            second_last_name=client_data.second_last_name,
            phone=client_data.phone,
            alternative_phone=client_data.alternative_phone,
            birth_date=client_data.birth_date,
            gender=gender_enum,
            address=client_data.address
        )

        return Client(
            id=client_model.id,
            dni_type=DocumentType(client_model.dni_type.value),
            dni_number=client_model.dni_number,
            first_name=client_model.first_name,
            middle_name=client_model.middle_name,
            last_name=client_model.last_name,
            second_last_name=client_model.second_last_name,
            phone=client_model.phone,
            alternative_phone=client_model.alternative_phone,
            birth_date=client_model.birth_date,
            gender=GenderType(client_model.gender.value),
            address=client_model.address,
            is_active=client_model.is_active,
            created_at=client_model.created_at.isoformat(),
            updated_at=client_model.updated_at.isoformat(),
            meta_info=client_model.meta_info
        )

    @staticmethod
    def get_client_by_id(db: Session, client_id: UUID, include_biometrics: bool = False) -> Client | None:
        """
        Get client by ID with optional biometric information.

        Args:
            db: Database session
            client_id: Client UUID
            include_biometrics: Whether to include biometric summary in response

        Returns:
            Client model with optional biometric data or None if not found
        """
        if include_biometrics:
            client_model = ClientRepository.get_by_id_with_biometrics(db, client_id)
        else:
            client_model = ClientRepository.get_by_id(db, client_id)

        if client_model:

            return Client(
                id=client_model.id,
                dni_type=DocumentType(client_model.dni_type.value),
                dni_number=client_model.dni_number,
                first_name=client_model.first_name,
                middle_name=client_model.middle_name,
                last_name=client_model.last_name,
                second_last_name=client_model.second_last_name,
                phone=client_model.phone,
                alternative_phone=client_model.alternative_phone,
                birth_date=client_model.birth_date,
                gender=GenderType(client_model.gender.value),
                address=client_model.address,
                is_active=client_model.is_active,
                created_at=client_model.created_at.isoformat(),
                updated_at=client_model.updated_at.isoformat(),
                meta_info=client_model.meta_info,
            )
        return None

    @staticmethod
    def update_client(db: Session, client_id: UUID, client_update: ClientUpdate) -> Client | None:
        update_dict = {}
        if client_update.dni_type is not None:
            update_dict["dni_type"] = DocumentTypeEnum[client_update.dni_type.value]
        if client_update.dni_number is not None:
            update_dict["dni_number"] = client_update.dni_number
        if client_update.first_name is not None:
            update_dict["first_name"] = client_update.first_name
        if client_update.middle_name is not None:
            update_dict["middle_name"] = client_update.middle_name
        if client_update.last_name is not None:
            update_dict["last_name"] = client_update.last_name
        if client_update.second_last_name is not None:
            update_dict["second_last_name"] = client_update.second_last_name
        if client_update.phone is not None:
            update_dict["phone"] = client_update.phone
        if client_update.alternative_phone is not None:
            update_dict["alternative_phone"] = client_update.alternative_phone
        if client_update.birth_date is not None:
            update_dict["birth_date"] = client_update.birth_date
        if client_update.gender is not None:
            update_dict["gender"] = GenderTypeEnum[client_update.gender.value.upper()]
        if client_update.address is not None:
            update_dict["address"] = client_update.address
        if client_update.is_active is not None:
            update_dict["is_active"] = client_update.is_active

        if not update_dict:
            return ClientService.get_client_by_id(db, client_id)

        client_model = ClientRepository.update(db, client_id, **update_dict)

        if client_model:
            return Client(
                id=client_model.id,
                dni_type=DocumentType(client_model.dni_type.value),
                dni_number=client_model.dni_number,
                first_name=client_model.first_name,
                middle_name=client_model.middle_name,
                last_name=client_model.last_name,
                second_last_name=client_model.second_last_name,
                phone=client_model.phone,
                alternative_phone=client_model.alternative_phone,
                birth_date=client_model.birth_date,
                gender=GenderType(client_model.gender.value),
                address=client_model.address,
                is_active=client_model.is_active,
                created_at=client_model.created_at.isoformat(),
                updated_at=client_model.updated_at.isoformat(),
                meta_info=client_model.meta_info
            )
        return None

    @staticmethod
    def delete_client(db: Session, client_id: UUID) -> bool:
        return ClientRepository.delete(db, client_id)

    @staticmethod
    def list_clients(
        db: Session,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Client]:
        client_models = ClientRepository.get_all(db, is_active, limit, offset)

        return [
            Client(
                id=client.id,
                dni_type=DocumentType(client.dni_type.value),
                dni_number=client.dni_number,
                first_name=client.first_name,
                middle_name=client.middle_name,
                last_name=client.last_name,
                second_last_name=client.second_last_name,
                phone=client.phone,
                alternative_phone=client.alternative_phone,
                birth_date=client.birth_date,
                gender=GenderType(client.gender.value),
                address=client.address,
                is_active=client.is_active,
                created_at=client.created_at.isoformat(),
                updated_at=client.updated_at.isoformat(),
                meta_info=client.meta_info
            )
            for client in client_models
        ]

    @staticmethod
    def search_clients(db: Session, search_term: str, limit: int = 50) -> List[Client]:
        client_models = ClientRepository.search(db, search_term, limit)

        return [
            Client(
                id=client.id,
                dni_type=DocumentType(client.dni_type.value),
                dni_number=client.dni_number,
                first_name=client.first_name,
                middle_name=client.middle_name,
                last_name=client.last_name,
                second_last_name=client.second_last_name,
                phone=client.phone,
                alternative_phone=client.alternative_phone,
                birth_date=client.birth_date,
                gender=GenderType(client.gender.value),
                address=client.address,
                is_active=client.is_active,
                created_at=client.created_at.isoformat(),
                updated_at=client.updated_at.isoformat(),
                meta_info=client.meta_info
            )
            for client in client_models
        ]

    @staticmethod
    def get_client_dashboard(db: Session, client_id: UUID) -> Optional[ClientDashboard]:
        """
        Get comprehensive client dashboard data.
        """
        dashboard_data = ClientRepository.get_client_dashboard_data(db, client_id)

        if not dashboard_data:
            return None

        client_model = dashboard_data["client"]
        latest_subscription = dashboard_data["latest_subscription"]
        total_subscriptions = dashboard_data["total_subscriptions"]
        last_attendance = dashboard_data["last_attendance"]
        attendance_count = dashboard_data["attendance_count"]

        client = Client(
            id=client_model.id,
            dni_type=DocumentType(client_model.dni_type.value),
            dni_number=client_model.dni_number,
            first_name=client_model.first_name,
            middle_name=client_model.middle_name,
            last_name=client_model.last_name,
            second_last_name=client_model.second_last_name,
            phone=client_model.phone,
            alternative_phone=client_model.alternative_phone,
            birth_date=client_model.birth_date,
            gender=GenderType(client_model.gender.value),
            address=client_model.address,
            is_active=client_model.is_active,
            created_at=client_model.created_at.isoformat(),
            updated_at=client_model.updated_at.isoformat(),
            meta_info=client_model.meta_info
        )

        biometric_type = None
        thumbnail_data_uri = None
        biometric_updated_at = None

        if hasattr(client_model, 'biometrics') and client_model.biometrics:
            face_biometrics = [
                bio for bio in client_model.biometrics
                if bio.type == BiometricTypeEnum.FACE
            ]

            if face_biometrics:
                active_face = next((bio for bio in face_biometrics if bio.is_active), None)
                target_biometric = active_face if active_face else face_biometrics[0]

                biometric_type = target_biometric.type.value
                biometric_updated_at = target_biometric.updated_at.isoformat()

                if target_biometric.thumbnail:
                    try:
                        encryption_service = get_encryption_service()
                        decrypted_thumbnail = encryption_service.decrypt_image_data(target_biometric.thumbnail)
                        thumbnail_base64 = base64.b64encode(decrypted_thumbnail).decode('utf-8')
                        thumbnail_data_uri = f"data:image/jpeg;base64,{thumbnail_base64}"
                    except Exception:
                        pass

        biometric = BiometricInfo(
            type=biometric_type,
            thumbnail=thumbnail_data_uri,
            updated_at=biometric_updated_at or client_model.updated_at.isoformat()
        )

        subscription_status = None
        subscription_plan = None
        subscription_end_date = None

        if latest_subscription:
            subscription_status = latest_subscription.status.value.replace("_", " ").title()
            if hasattr(latest_subscription, 'plan') and latest_subscription.plan:
                subscription_plan = latest_subscription.plan.name
            subscription_end_date = latest_subscription.end_date.isoformat()

        subscription = SubscriptionInfo(
            status=subscription_status,
            plan=subscription_plan,
            end_date=subscription_end_date
        )

        stats = ClientStats(
            subscriptions=total_subscriptions,
            attendances = attendance_count,
            last_attendance=last_attendance.check_in.isoformat() if last_attendance else None,
            since=client_model.created_at.isoformat()
        )

        return ClientDashboard(
            client=client,
            biometric=biometric,
            subscription=subscription,
            stats=stats
        )
