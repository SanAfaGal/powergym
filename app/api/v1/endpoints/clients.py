from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.client import Client, ClientCreate, ClientUpdate
from app.models.client_dashboard import ClientDashboard
from app.services.client_service import ClientService
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.db.session import get_db
from uuid import UUID
from typing import List

router = APIRouter()

@router.post(
    "/",
    response_model=Client,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="Register a new client in the system.",
    responses={
        201: {
            "description": "Client successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "dni_type": "DNI",
                        "dni_number": "12345678",
                        "email": "juan.perez@example.com",
                        "phone": "+51987654321",
                        "is_active": True,
                        "created_at": "2025-10-07T10:30:00Z",
                        "updated_at": "2025-10-07T10:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Client with this DNI already exists"},
        401: {"description": "Not authenticated"}
    }
)
def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    existing_client = ClientService.get_client_by_dni(db, client_data.dni_number)
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con este número de documento"
        )

    client = ClientService.create_client(db, client_data)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el cliente"
        )

    return client

@router.get(
    "/",
    response_model=List[Client],
    summary="List all clients",
    description="Retrieve a paginated list of clients with optional filtering.",
    responses={
        200: {
            "description": "List of clients",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "first_name": "Juan",
                            "last_name": "Pérez",
                            "dni_type": "DNI",
                            "dni_number": "12345678",
                            "email": "juan.perez@example.com",
                            "phone": "+51987654321",
                            "is_active": True,
                            "created_at": "2025-10-07T10:30:00Z",
                            "updated_at": "2025-10-07T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def list_clients(
    is_active: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    clients = ClientService.list_clients(
        db=db,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return clients

@router.get(
    "/search",
    response_model=List[Client],
    summary="Search clients",
    description="Search clients by name, DNI, email, or phone.",
    responses={
        200: {
            "description": "Search results",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "first_name": "Juan",
                            "last_name": "Pérez",
                            "dni_type": "DNI",
                            "dni_number": "12345678",
                            "email": "juan.perez@example.com",
                            "phone": "+51987654321",
                            "is_active": True,
                            "created_at": "2025-10-07T10:30:00Z",
                            "updated_at": "2025-10-07T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
def search_clients(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    clients = ClientService.search_clients(db=db, search_term=q, limit=limit)
    return clients

@router.get(
    "/dni/{dni_number}",
    response_model=Client,
    summary="Get client by DNI",
    description="Retrieve a specific client by their DNI number.",
    responses={
        200: {
            "description": "Client found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "dni_type": "DNI",
                        "dni_number": "12345678",
                        "email": "juan.perez@example.com",
                        "phone": "+51987654321",
                        "is_active": True,
                        "created_at": "2025-10-07T10:30:00Z",
                        "updated_at": "2025-10-07T10:30:00Z"
                    }
                }
            }
        },
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_client_by_dni(
    dni_number: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    client = ClientService.get_client_by_dni(db, dni_number)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return client

@router.get(
    "/{client_id}",
    response_model=Client,
    summary="Get client by ID",
    description="Retrieve a specific client by their ID with optional biometric information.",
    responses={
        200: {
            "description": "Client found",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "dni_type": "CC",
                        "dni_number": "12345678",
                        "phone": "+573001234567",
                        "birth_date": "1990-05-15",
                        "gender": "male",
                        "is_active": True,
                        "created_at": "2025-10-07T10:30:00Z",
                        "updated_at": "2025-10-07T10:30:00Z",
                        "biometric": {
                            "has_face_biometric": True,
                            "is_active": True,
                            "thumbnail": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
                        }
                    }
                }
            }
        },
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_client(
    client_id: UUID,
    include_biometrics: bool = Query(
        default=True,
        description="Include facial biometric information in the response"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific client by their ID.

    - **client_id**: UUID of the client to retrieve
    - **include_biometrics**: If true, includes facial biometric data (thumbnail, active status)
    """
    client = ClientService.get_client_by_id(db, client_id, include_biometrics=include_biometrics)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return client

@router.put("/{client_id}", response_model=Client)
def update_client(
    client_id: UUID,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    existing_client = ClientService.get_client_by_id(db, client_id)
    if not existing_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    if client_update.dni_number and client_update.dni_number != existing_client.dni_number:
        duplicate_client = ClientService.get_client_by_dni(db, client_update.dni_number)
        if duplicate_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con este número de documento"
            )

    updated_client = ClientService.update_client(db, client_id, client_update)
    if not updated_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el cliente"
        )

    return updated_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    existing_client = ClientService.get_client_by_id(db, client_id)
    if not existing_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    success = ClientService.delete_client(db, client_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el cliente"
        )

    return None

@router.get(
    "/{client_id}/dashboard",
    response_model=ClientDashboard,
    summary="Get client dashboard",
    description="Retrieve complete dashboard information for a client including biometrics, subscription, and statistics.",
    responses={
        200: {
            "description": "Client dashboard information",
            "content": {
                "application/json": {
                    "example": {
                        "client": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "first_name": "Juan",
                            "last_name": "Pérez",
                            "dni_type": "DNI",
                            "dni_number": "12345678",
                            "phone": "+51987654321",
                            "is_active": True,
                            "created_at": "2025-10-07T10:30:00Z",
                            "updated_at": "2025-10-07T10:30:00Z"
                        },
                        "biometric": {
                            "type": "FACE",
                            "thumbnail": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
                            "updated_at": "2025-10-07T10:30:00Z"
                        },
                        "subscription": {
                            "status": "active",
                            "plan": "Premium Monthly",
                            "end_date": "2025-11-07"
                        },
                        "stats": {
                            "subscriptions": 3,
                            "last_attendance": "2025-10-18T18:45:00Z",
                            "since": "2025-10-07T10:30:00Z"
                        }
                    }
                }
            }
        },
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_client_dashboard(
    client_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get complete dashboard information for a specific client.

    Returns:
    - **client**: Basic client information
    - **biometric**: Latest facial biometric data with thumbnail
    - **subscription**: Current subscription status and plan
    - **stats**: Statistics including total subscriptions, attendance count, and account age
    """
    dashboard = ClientService.get_client_dashboard(db, client_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return dashboard

@router.get(
    "/{client_id}/dashboard",
    response_model=ClientDashboard,
    summary="Get client dashboard",
    description="Retrieve comprehensive dashboard information for a specific client.",
    responses={
        200: {
            "description": "Client dashboard data",
            "content": {
                "application/json": {
                    "example": {
                        "client": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "first_name": "Juan",
                            "last_name": "Pérez",
                            "dni_type": "DNI",
                            "dni_number": "12345678",
                            "phone": "+51987654321",
                            "is_active": True,
                            "created_at": "2025-10-07T10:30:00Z",
                            "updated_at": "2025-10-07T10:30:00Z"
                        },
                        "biometric": {
                            "type": "FACE",
                            "thumbnail": "data:image/jpeg;base64,...",
                            "updated_at": "2025-10-07T10:30:00Z"
                        },
                        "subscription": {
                            "status": "Active",
                            "plan": "Plan Mensual",
                            "end_date": "2025-11-07"
                        },
                        "stats": {
                            "subscriptions": 3,
                            "last_attendance": "2025-10-15T08:30:00Z",
                            "since": "2025-01-15T10:00:00Z"
                        }
                    }
                }
            }
        },
        404: {"description": "Client not found"},
        401: {"description": "Not authenticated"}
    }
)
def get_client_dashboard(
    client_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard information for a specific client.
    Includes client details, biometric info, latest subscription, and statistics.
    """
    dashboard = ClientService.get_client_dashboard(db, client_id)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return dashboard
