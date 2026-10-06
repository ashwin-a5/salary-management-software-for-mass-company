from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bonus, Employee, User
from app.schemas import BonusOut, BonusCreate
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/bonuses", tags=["Bonuses & Incentives"])

def build_bonus_out(b: Bonus) -> BonusOut:
    out = BonusOut.from_orm(b)
    if b.employee:
        out.employee_name = f"{b.employee.first_name} {b.employee.last_name}"
        out.employee_code = b.employee.employee_code
        out.department_name = b.employee.department.name if b.employee.department else None
    return out

@router.get("", response_model=List[BonusOut])
def list_bonuses(
    month: Optional[int] = None,
    year: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bonus).join(Employee)
    
    if current_user.role == "employee":
        if not current_user.employee_id:
            return []
        query = query.filter(Bonus.employee_id == current_user.employee_id)
    elif employee_id:
        query = query.filter(Bonus.employee_id == employee_id)
        
    if month:
        query = query.filter(Bonus.month == month)
    if year:
        query = query.filter(Bonus.year == year)
        
    bonuses = query.order_by(Bonus.id.desc()).all()
    return [build_bonus_out(b) for b in bonuses]

@router.post("", response_model=BonusOut)
def create_bonus(
    req: BonusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    bonus = Bonus(
        employee_id=req.employee_id,
        title=req.title,
        bonus_type=req.bonus_type,
        amount=req.amount,
        month=req.month,
        year=req.year,
        reason=req.reason,
        is_taxable=req.is_taxable,
        status=req.status or "approved",
        created_by_user_id=current_user.id
    )
    db.add(bonus)
    db.commit()
    db.refresh(bonus)
    
    log_activity(db, action="BONUS_ADDED", module="BONUS", user=current_user, record_id=str(bonus.id), details=f"Awarded {req.bonus_type} bonus of Rs. {req.amount:,.2f} to {emp.first_name} {emp.last_name}")
    return build_bonus_out(bonus)

@router.delete("/{bonus_id}")
def delete_bonus(
    bonus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    bonus = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    db.delete(bonus)
    db.commit()
    log_activity(db, action="BONUS_DELETED", module="BONUS", user=current_user, record_id=str(bonus_id), details=f"Deleted bonus of Rs. {bonus.amount}")
    return {"message": "Bonus deleted successfully"}
