from sqlalchemy.orm import Session
from app.repositories.plan_repository import PlanRepository
from app.models.plan import PlanCreate, PlanUpdate
from app.db.models import DurationTypeEnum
from uuid import UUID
from typing import Optional, List

class PlanService:
    """
    Business logic layer for plan management.
    """

    @staticmethod
    def create_plan(db: Session, plan_data: PlanCreate):
        """
        Create a new plan.
        """
        duration_enum = DurationTypeEnum[plan_data.duration_unit.value.upper()]

        return PlanRepository.create(
            db=db,
            name=plan_data.name,
            slug=plan_data.slug,
            description=plan_data.description,
            price=plan_data.price,
            currency=plan_data.currency,
            duration_unit=duration_enum,
            duration_count=plan_data.duration_count
        )

    @staticmethod
    def get_plan_by_id(db: Session, plan_id: UUID):
        """
        Get plan by ID.
        """
        return PlanRepository.get_by_id(db, plan_id)

    @staticmethod
    def get_plan_by_slug(db: Session, slug: str):
        """
        Get plan by slug.
        """
        return PlanRepository.get_by_slug(db, slug)

    @staticmethod
    def list_plans(
        db: Session,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """
        List all plans with optional filtering.
        """
        return PlanRepository.get_all(
            db=db,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def search_plans(db: Session, search_term: str, limit: int = 50):
        """
        Search plans by name, description, or slug.
        """
        return PlanRepository.search(db, search_term, limit)

    @staticmethod
    def update_plan(db: Session, plan_id: UUID, plan_update: PlanUpdate):
        """
        Update plan information.
        """
        update_data = plan_update.model_dump(exclude_unset=True)

        if 'duration_unit' in update_data and update_data['duration_unit']:
            update_data['duration_unit'] = DurationTypeEnum[update_data['duration_unit'].upper()]

        return PlanRepository.update(db, plan_id, **update_data)

    @staticmethod
    def delete_plan(db: Session, plan_id: UUID) -> bool:
        """
        Soft delete a plan by setting is_active to False.
        """
        return PlanRepository.delete(db, plan_id)
