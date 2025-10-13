from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.models import PlanModel, DurationTypeEnum
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

class PlanRepository:
    @staticmethod
    def create(db: Session, name: str, slug: Optional[str], description: Optional[str],
               price: Decimal, currency: str, duration_unit: DurationTypeEnum,
               duration_count: int) -> PlanModel:
        """
        Create a new plan in the database.
        """
        db_plan = PlanModel(
            name=name,
            slug=slug,
            description=description,
            price=price,
            currency=currency,
            duration_unit=duration_unit,
            duration_count=duration_count,
            is_active=True
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan

    @staticmethod
    def get_by_id(db: Session, plan_id: UUID) -> Optional[PlanModel]:
        """
        Get plan by ID.
        """
        return db.query(PlanModel).filter(PlanModel.id == plan_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[PlanModel]:
        """
        Get plan by slug.
        """
        return db.query(PlanModel).filter(PlanModel.slug == slug).first()

    @staticmethod
    def get_all(db: Session, is_active: Optional[bool] = None, limit: int = 100,
                offset: int = 0) -> List[PlanModel]:
        """
        Get all plans with optional filtering.
        """
        query = db.query(PlanModel)

        if is_active is not None:
            query = query.filter(PlanModel.is_active == is_active)

        query = query.order_by(PlanModel.created_at.desc()).offset(offset).limit(limit)
        return query.all()

    @staticmethod
    def search(db: Session, search_term: str, limit: int = 50) -> List[PlanModel]:
        """
        Search plans by name or description.
        """
        search_pattern = f"%{search_term}%"
        return db.query(PlanModel).filter(
            or_(
                PlanModel.name.ilike(search_pattern),
                PlanModel.description.ilike(search_pattern),
                PlanModel.slug.ilike(search_pattern)
            )
        ).limit(limit).all()

    @staticmethod
    def update(db: Session, plan_id: UUID, **kwargs) -> Optional[PlanModel]:
        """
        Update plan by ID.
        """
        plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
        if not plan:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(plan, key):
                setattr(plan, key, value)

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def delete(db: Session, plan_id: UUID) -> bool:
        """
        Soft delete plan by setting is_active to False.
        """
        plan = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
        if not plan:
            return False

        plan.is_active = False
        db.commit()
        return True

    @staticmethod
    async def create_async(db: AsyncSession, name: str, slug: Optional[str],
                          description: Optional[str], price: Decimal, currency: str,
                          duration_unit: DurationTypeEnum, duration_count: int) -> PlanModel:
        """
        Create a new plan in the database (async).
        """
        db_plan = PlanModel(
            name=name,
            slug=slug,
            description=description,
            price=price,
            currency=currency,
            duration_unit=duration_unit,
            duration_count=duration_count,
            is_active=True
        )
        db.add(db_plan)
        await db.commit()
        await db.refresh(db_plan)
        return db_plan

    @staticmethod
    async def get_by_id_async(db: AsyncSession, plan_id: UUID) -> Optional[PlanModel]:
        """
        Get plan by ID (async).
        """
        result = await db.execute(select(PlanModel).filter(PlanModel.id == plan_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug_async(db: AsyncSession, slug: str) -> Optional[PlanModel]:
        """
        Get plan by slug (async).
        """
        result = await db.execute(select(PlanModel).filter(PlanModel.slug == slug))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_async(db: AsyncSession, is_active: Optional[bool] = None,
                           limit: int = 100, offset: int = 0) -> List[PlanModel]:
        """
        Get all plans with optional filtering (async).
        """
        query = select(PlanModel)

        if is_active is not None:
            query = query.filter(PlanModel.is_active == is_active)

        query = query.order_by(PlanModel.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def search_async(db: AsyncSession, search_term: str, limit: int = 50) -> List[PlanModel]:
        """
        Search plans by name or description (async).
        """
        search_pattern = f"%{search_term}%"
        query = select(PlanModel).filter(
            or_(
                PlanModel.name.ilike(search_pattern),
                PlanModel.description.ilike(search_pattern),
                PlanModel.slug.ilike(search_pattern)
            )
        ).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_async(db: AsyncSession, plan_id: UUID, **kwargs) -> Optional[PlanModel]:
        """
        Update plan by ID (async).
        """
        result = await db.execute(select(PlanModel).filter(PlanModel.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(plan, key):
                setattr(plan, key, value)

        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def delete_async(db: AsyncSession, plan_id: UUID) -> bool:
        """
        Soft delete plan by setting is_active to False (async).
        """
        result = await db.execute(select(PlanModel).filter(PlanModel.id == plan_id))
        plan = result.scalar_one_or_none()

        if not plan:
            return False

        plan.is_active = False
        await db.commit()
        return True
