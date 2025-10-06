from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserUpdate, PasswordChange, UserRole
from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.services.user_service import UserService
from app.core.security import verify_password

router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    updated_user = UserService.update_user(current_user.username, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update user"
        )
    return updated_user

@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    user_in_db = UserService.get_user_by_username(current_user.username)
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(password_change.current_password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    success = UserService.change_password(current_user.username, password_change.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not change password"
        )

    return {"message": "Password changed successfully"}

@router.delete("/me", status_code=status.HTTP_200_OK)
async def disable_own_account(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    disabled_user = UserService.disable_user(current_user.username)
    if not disabled_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not disable account"
        )

    return {"message": "Account disabled successfully"}

@router.get("", response_model=list[User])
async def list_users(
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    return UserService.get_all_users()

@router.get("/{username}", response_model=User)
async def get_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{username}", response_model=User)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated_user = UserService.update_user(username, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update user"
        )
    return updated_user

@router.patch("/{username}/password", status_code=status.HTTP_200_OK)
async def reset_user_password(
    username: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    success = UserService.change_password(username, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not reset password"
        )

    return {"message": "Password reset successfully"}

@router.patch("/{username}/role", response_model=User)
async def change_user_role(
    username: str,
    new_role: UserRole,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    updated_user = UserService.change_user_role(username, new_role)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not change user role"
        )
    return updated_user

@router.patch("/{username}/disable", response_model=User)
async def disable_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    disabled_user = UserService.disable_user(username)
    if not disabled_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not disable user"
        )
    return disabled_user

@router.patch("/{username}/enable", response_model=User)
async def enable_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    enabled_user = UserService.enable_user(username)
    if not enabled_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not enable user"
        )
    return enabled_user

@router.delete("/{username}", status_code=status.HTTP_200_OK)
async def delete_user(
    username: str,
    current_user: Annotated[User, Depends(get_current_admin_user)]
):
    user = UserService.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = UserService.delete_user(username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete user"
        )

    return {"message": "User deleted successfully"}
