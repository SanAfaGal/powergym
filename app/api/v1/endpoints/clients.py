from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
import logging

from app.schemas.client import Client, ClientCreate, ClientUpdate, ClientDashboard
from app.services.client_service import ClientService
from app.api.dependencies import get_current_active_user
from app.schemas.user import User
from app.db.session import get_db
from app.utils.client.validators import ClientValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clients", tags=["clients"])


# ============= CLIENTS =============

@router.post(
    "/",
    response_model=Client,
    status_code=status.HTTP_201_CREATED,
    summary="Create new client",
    description="Register a new client in the gym"
)
def create_client(
        client_data: ClientCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Create a new client"""
    ClientValidator.verify_dni_uniqueness(db, client_data.dni_number)

    client = ClientService.create_client(db, client_data)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating client"
        )
    return client


@router.get(
    "/",
    response_model=List[Client],
    summary="List all clients",
    description="Get a paginated list of clients with optional filters"
)
def list_clients(
        is_active: bool | None = Query(None, description="Filter by active/inactive status"),
        search: str | None = Query(None, min_length=1, description="Search by name, DNI, email or phone"),
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """List all clients with optional filters"""
    if search:
        return ClientService.search_clients(db, search, limit)

    return ClientService.list_clients(db, is_active, limit, offset)


@router.get(
    "/dni/{dni_number}",
    response_model=Client,
    summary="Get client by DNI",
    description="Retrieve a client using their document number (useful for check-in)"
)
def get_client_by_dni(
        dni_number: str,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get client by DNI - useful for check-in"""
    client = ClientService.get_client_by_dni(db, dni_number)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.get(
    "/{client_id}",
    response_model=Client,
    summary="Get client by ID",
    description="Retrieve detailed information of a specific client"
)
def get_client(
        client_id: UUID,
        include_biometrics: bool = Query(
            True,
            description="Include biometric information in response"
        ),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get client by ID"""
    client = ClientService.get_client_by_id(db, client_id, include_biometrics=include_biometrics)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.put(
    "/{client_id}",
    response_model=Client,
    summary="Update client",
    description="Update information of an existing client"
)
def update_client(
        client_id: UUID,
        client_update: ClientUpdate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Update client information"""
    existing_client = ClientValidator.get_or_404(db, client_id)

    ClientValidator.verify_dni_uniqueness(
        db,
        client_update.dni_number,
        existing_client.dni_number
    )

    updated = ClientService.update_client(db, client_id, client_update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating client"
        )
    return updated


@router.patch(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate client",
    description="Deactivate a client (soft delete). The client can be reactivated"
)
def deactivate_client(
        client_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Deactivate a client"""
    ClientValidator.get_or_404(db, client_id)

    if not ClientService.delete_client(db, client_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating client"
        )


@router.get(
    "/{client_id}/dashboard",
    response_model=ClientDashboard,
    summary="Get client dashboard",
    description="Get summarized client information including current subscription and statistics"
)
def get_client_dashboard(
        client_id: UUID,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get client dashboard"""
    dashboard = ClientService.get_client_dashboard(db, client_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return dashboard