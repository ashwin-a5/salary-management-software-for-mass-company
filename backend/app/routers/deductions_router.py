from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Deduction, Employee, User
from app.schemas import DeductionOut, DeductionCreate
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/deductions", tags=["Deductions Management"])

def build_deduction_out(d: Deduction) -> DeductionOut:
    out = DeductionOut.from_orm(d)
    if d.employee:
        out.employee_name = f"{d.employee.first_name} {d.employee.last_name}"
        out.employee_code = d.employee.employee_code
        out.department_name = d.employee.department.name if d.employee.department else None
    return out

@router.get("", response_model=List[DeductionOut])
def list_deductions(
    month: Optional[int] = None,
    year: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Deduction).join(Employee)
    
    if current_user.role == "employee":
        if not current_user.employee_id:
            return []
        query = query.filter(Deduction.employee_id == current_user.employee_id)
    elif employee_id:
        query = query.filter(Deduction.employee_id == employee_id)
        
    if month:
        query = query.filter(Deduction.month == month)
    if year:
        query = query.filter(Deduction.year == year)
        
    deductions = query.order_by(Deduction.id.desc()).all()
    return [build_deduction_out(d) for d in deductions]

@router.post("", response_model=DeductionOut)
def create_deduction(
    req: DeductionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    ded = Deduction(
        employee_id=req.employee_id,
        title=req.title,
        deduction_type=req.deduction_type,
        amount=req.amount,
        month=req.month,
        year=req.year,
        reason=req.reason,
        status=req.status or "approved",
        created_by_user_id=current_user.id
    )
    db.add(ded)
    db.commit()
    db.refresh(ded)
    
    log_activity(db, action="DEDUCTION_ADDED", module="DEDUCTION", user=current_user, record_id=str(ded.id), details=f"Added {req.deduction_type} deduction of Rs. {req.amount:,.2f} for {emp.first_name} {emp.last_name}")
    return build_deduction_out(ded)

@router.delete("/{ded_id}")
def delete_deduction(
    ded_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    ded = db.query(Deduction).filter(Deduction.id == ded_id).first()
    if not ded:
        raise HTTPException(status_code=404, detail="Deduction not found")
    db.delete(ded)
    db.commit()
    log_activity(db, action="DEDUCTION_DELETED", module="DEDUCTION", user=current_user, record_id=str(ded_id), details=f"Deleted deduction of Rs. {ded.amount}")
    return {"message": "Deduction deleted successfully"}
