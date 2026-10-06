from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Leave, Employee, User
from app.schemas import LeaveOut, LeaveCreate, LeaveStatusUpdate
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/leaves", tags=["Leaves Management"])

def build_leave_out(leave: Leave) -> LeaveOut:
    out = LeaveOut.from_orm(leave)
    if leave.employee:
        out.employee_name = f"{leave.employee.first_name} {leave.employee.last_name}"
        out.employee_code = leave.employee.employee_code
        out.department_name = leave.employee.department.name if leave.employee.department else None
    return out

@router.get("", response_model=List[LeaveOut])
def list_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Leave).join(Employee)
    
    if current_user.role == "employee":
        if not current_user.employee_id:
            return []
        query = query.filter(Leave.employee_id == current_user.employee_id)
    elif employee_id:
        query = query.filter(Leave.employee_id == employee_id)
        
    if status:
        query = query.filter(Leave.status == status)
        
    leaves = query.order_by(Leave.id.desc()).all()
    return [build_leave_out(l) for l in leaves]

@router.post("", response_model=LeaveOut)
def apply_leave(
    req: LeaveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If employee role, ensure applying for self
    emp_id = req.employee_id
    if current_user.role == "employee":
        if not current_user.employee_id:
            raise HTTPException(status_code=400, detail="Employee record not linked to this user")
        emp_id = current_user.employee_id
        
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    leave = Leave(
        employee_id=emp_id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        total_days=req.total_days,
        reason=req.reason,
        status="pending" if current_user.role == "employee" else "approved",
        approved_by_user_id=current_user.id if current_user.role != "employee" else None
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    log_activity(db, action="LEAVE_APPLIED", module="LEAVES", user=current_user, record_id=str(leave.id), details=f"Applied {req.leave_type} leave for {req.total_days} days")
    return build_leave_out(leave)

@router.patch("/{leave_id}/status", response_model=LeaveOut)
def update_leave_status(
    leave_id: int,
    req: LeaveStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
        
    leave.status = req.status
    leave.approved_by_user_id = current_user.id
    if req.rejection_reason:
        leave.rejection_reason = req.rejection_reason
        
    db.commit()
    db.refresh(leave)
    log_activity(db, action=f"LEAVE_{req.status.upper()}", module="LEAVES", user=current_user, record_id=str(leave.id), details=f"Leave request marked {req.status}")
    return build_leave_out(leave)
