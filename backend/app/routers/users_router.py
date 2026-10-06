from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Employee
from app.schemas import UserOut, UserCreate, UserUpdate
from app.auth import get_password_hash, require_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/users", tags=["Users Management"])

@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return db.query(User).order_by(User.id.desc()).all()

@router.post("", response_model=UserOut)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        username=req.username,
        email=req.email,
        full_name=req.full_name,
        hashed_password=get_password_hash(req.password),
        role=req.role,
        is_active=req.is_active,
        employee_id=req.employee_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_activity(db, action="USER_CREATED", module="USERS", user=admin, record_id=str(new_user.id), details=f"Created user {new_user.username} with role {new_user.role}")
    return new_user

@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if req.email and req.email != user.email:
        if db.query(User).filter(User.email == req.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = req.email
        
    if req.full_name is not None:
        user.full_name = req.full_name
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password:
        user.hashed_password = get_password_hash(req.password)
        
    db.commit()
    db.refresh(user)
    log_activity(db, action="USER_UPDATED", module="USERS", user=admin, record_id=str(user.id), details=f"Updated user {user.username}")
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    username = user.username
    db.delete(user)
    db.commit()
    log_activity(db, action="USER_DELETED", module="USERS", user=admin, record_id=str(user_id), details=f"Deleted user {username}")
    return {"message": "User deleted successfully"}
