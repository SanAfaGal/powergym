from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.plan import Plan, PlanCreate, PlanUpdate
from app.services.plan_service import PlanService
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.db.session import get_db
from uuid import UUID
from typing import List

router = APIRouter()

@router.post(
    "/",
    response_model=Plan,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new plan",
    description="Register a new subscription plan in the system.",
    responses={
        201: {
            "description": "Plan successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Basic Plan",
                        "slug": "basic-plan",
                        "description": "A basic subscription plan",
                        "price": 50000.00,
                        "currency": "COP",
                        "duration_unit": "month",
                        "duration_count": 1,
                        "is_active": True,
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T10:30:00Z",
                        "meta_info": {}
                    }
                }
            }
        },
        400: {"description": "Plan with this slug already exists"},
        401: {"description": "Not authenticated"}
    }
)
def create_plan(
    plan_data: PlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subscription plan.
    """
    if plan_data.slug:
        existing_plan = PlanService.get_plan_by_slug(db, plan_data.slug)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A plan with this slug already exists"
            )

    plan = PlanService.create_plan(db, plan_data)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating plan"
        )

    return plan

@router.get(
    "/",
    response_model=List[Plan],
    summary="List all plans",
    description="Retrieve a paginated list of plans with optional filtering.",
    responses={
        200: {
            "description": "List of plans",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Basic Plan",
                            "slug": "basic-plan",
                            "description": "A basic subscription plan",
                            "price": 50000.00,
                            "currency": "COP",
                            "duration_unit": "month",
                            "duration_count": 1,
                            "is_active": True,
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z",
                            "meta_info": {}
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def list_plans(
    is_active: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all subscription plans with pagination.
    """
    plans = PlanService.list_plans(
        db=db,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return plans

@router.get(
    "/search",
    response_model=List[Plan],
    summary="Search plans",
    description="Search plans by name, description, or slug.",
    responses={
        200: {
            "description": "Search results",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Basic Plan",
                            "slug": "basic-plan",
                            "description": "A basic subscription plan",
                            "price": 50000.00,
                            "currency": "COP",
                            "duration_unit": "month",
                            "duration_count": 1,
                            "is_active": True,
                            "created_at": "2025-10-13T10:30:00Z",
                            "updated_at": "2025-10-13T10:30:00Z",
                            "meta_info": {}
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def search_plans(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search plans by name, description, or slug.
    """
    plans = PlanService.search_plans(db=db, search_term=q, limit=limit)
    return plans

@router.get(
    "/slug/{slug}",
    response_model=Plan,
    summary="Get plan by slug",
    description="Retrieve a specific plan by its slug.",
    responses={
        200: {
            "description": "Plan found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Basic Plan",
                        "slug": "basic-plan",
                        "description": "A basic subscription plan",
                        "price": 50000.00,
                        "currency": "COP",
                        "duration_unit": "month",
                        "duration_count": 1,
                        "is_active": True,
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T10:30:00Z",
                        "meta_info": {}
                    }
                }
            }
        },
        404: {"description": "Plan not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_plan_by_slug(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a plan by its slug.
    """
    plan = PlanService.get_plan_by_slug(db, slug)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return plan

@router.get(
    "/{plan_id}",
    response_model=Plan,
    summary="Get plan by ID",
    description="Retrieve a specific plan by its ID.",
    responses={
        200: {
            "description": "Plan found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Basic Plan",
                        "slug": "basic-plan",
                        "description": "A basic subscription plan",
                        "price": 50000.00,
                        "currency": "COP",
                        "duration_unit": "month",
                        "duration_count": 1,
                        "is_active": True,
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T10:30:00Z",
                        "meta_info": {}
                    }
                }
            }
        },
        404: {"description": "Plan not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a plan by its ID.
    """
    plan = PlanService.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return plan

@router.put(
    "/{plan_id}",
    response_model=Plan,
    summary="Update a plan",
    description="Update an existing subscription plan.",
    responses={
        200: {
            "description": "Plan successfully updated",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Updated Plan",
                        "slug": "updated-plan",
                        "description": "An updated subscription plan",
                        "price": 75000.00,
                        "currency": "COP",
                        "duration_unit": "month",
                        "duration_count": 1,
                        "is_active": True,
                        "created_at": "2025-10-13T10:30:00Z",
                        "updated_at": "2025-10-13T11:00:00Z",
                        "meta_info": {}
                    }
                }
            }
        },
        404: {"description": "Plan not found"},
        400: {"description": "Another plan with this slug already exists"},
        401: {"description": "Not authenticated"}
    }
)
def update_plan(
    plan_id: UUID,
    plan_update: PlanUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a plan's information.
    """
    existing_plan = PlanService.get_plan_by_id(db, plan_id)
    if not existing_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    if plan_update.slug and plan_update.slug != existing_plan.slug:
        duplicate_plan = PlanService.get_plan_by_slug(db, plan_update.slug)
        if duplicate_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another plan with this slug already exists"
            )

    updated_plan = PlanService.update_plan(db, plan_id, plan_update)
    if not updated_plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating plan"
        )

    return updated_plan

@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a plan",
    description="Soft delete a plan by setting is_active to False.",
    responses={
        204: {"description": "Plan successfully deleted"},
        404: {"description": "Plan not found"},
        401: {"description": "Not authenticated"}
    }
)
def delete_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a plan.
    """
    existing_plan = PlanService.get_plan_by_id(db, plan_id)
    if not existing_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )

    success = PlanService.delete_plan(db, plan_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting plan"
        )

    return None
