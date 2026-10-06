import calendar
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import (
    Payroll, PayrollItem, Employee, Department, User, Payslip
)
from app.schemas import (
    PayrollOut, PayrollItemOut, PayrollGenerateRequest, PayrollStatusUpdate
)
from app.auth import get_current_user, require_hr_or_admin
from app.services.payroll_service import generate_monthly_payroll, calculate_employee_payroll
from app.services.audit_service import log_activity

router = APIRouter(prefix="/payroll", tags=["Payroll Management"])

def build_payroll_out(p: Payroll, include_items: bool = False) -> PayrollOut:
    out = PayrollOut.from_orm(p)
    out.department_name = p.department.name if p.department else "All Departments"
    out.generated_by_name = p.generated_by.full_name if p.generated_by else None
    out.approved_by_name = p.approved_by.full_name if p.approved_by else None
    
    if include_items and p.items:
        items_out = []
        for item in p.items:
            item_out = PayrollItemOut.from_orm(item)
            if item.payslip:
                item_out.payslip_id = item.payslip.id
            items_out.append(item_out)
        out.items = items_out
    else:
        out.items = []
    return out

@router.get("", response_model=List[PayrollOut])
def list_payrolls(
    year: Optional[int] = None,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    query = db.query(Payroll)
    if year:
        query = query.filter(Payroll.year == year)
    if month:
        query = query.filter(Payroll.month == month)
    if department_id:
        query = query.filter(Payroll.department_id == department_id)
    if status:
        query = query.filter(Payroll.status == status)
        
    payrolls = query.order_by(desc(Payroll.year), desc(Payroll.month), desc(Payroll.id)).all()
    return [build_payroll_out(p, include_items=False) for p in payrolls]

@router.get("/{payroll_id}", response_model=PayrollOut)
def get_payroll_details(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll batch not found")
    return build_payroll_out(payroll, include_items=True)

@router.post("/generate", response_model=PayrollOut)
def generate_payroll(
    req: PayrollGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    try:
        payroll, warnings = generate_monthly_payroll(
            db=db,
            month=req.month,
            year=req.year,
            department_id=req.department_id,
            employee_ids=req.employee_ids,
            user_id=current_user.id,
            remarks=req.remarks
        )
        
        month_name = calendar.month_name[req.month]
        log_activity(
            db,
            action="PAYROLL_GENERATED",
            module="PAYROLL",
            user=current_user,
            record_id=str(payroll.id),
            details=f"Generated payroll for {month_name} {req.year} ({payroll.total_employees} employees, Total Net: Rs. {payroll.total_net_pay:,.2f})"
        )
        return build_payroll_out(payroll, include_items=True)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate payroll: {str(e)}")

@router.patch("/{payroll_id}/status", response_model=PayrollOut)
def update_payroll_status(
    payroll_id: int,
    req: PayrollStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll batch not found")
        
    old_status = payroll.status
    new_status = req.status.lower()
    
    if new_status not in ["draft", "processing", "approved", "paid", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid payroll status")
        
    payroll.status = new_status
    if req.remarks:
        payroll.remarks = req.remarks
        
    if new_status == "approved":
        payroll.approved_by_user_id = current_user.id
    elif new_status == "paid":
        payroll.paid_date = date.today()
        # Mark all items as paid
        for itm in payroll.items:
            itm.payment_status = "paid"
            
    db.commit()
    db.refresh(payroll)
    
    month_name = calendar.month_name[payroll.month]
    log_activity(
        db,
        action=f"PAYROLL_{new_status.upper()}",
        module="PAYROLL",
        user=current_user,
        record_id=str(payroll.id),
        details=f"Payroll for {month_name} {payroll.year} changed from {old_status} to {new_status}"
    )
    return build_payroll_out(payroll, include_items=True)

@router.get("/item/{item_id}", response_model=PayrollItemOut)
def get_payroll_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(PayrollItem).filter(PayrollItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Payroll item not found")
        
    if current_user.role == "employee" and current_user.employee_id != item.employee_id:
        raise HTTPException(status_code=403, detail="Access denied to other employee payroll details")
        
    out = PayrollItemOut.from_orm(item)
    if item.payslip:
        out.payslip_id = item.payslip.id
    return out

@router.delete("/{payroll_id}")
def delete_payroll_draft(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll batch not found")
        
    if payroll.status in ["approved", "paid"]:
        raise HTTPException(status_code=400, detail="Cannot delete approved or paid payroll batch. Cancel it instead.")
        
    code = payroll.payroll_code
    db.delete(payroll)
    db.commit()
    log_activity(db, action="PAYROLL_DELETED", module="PAYROLL", user=current_user, record_id=str(payroll_id), details=f"Deleted draft payroll batch {code}")
    return {"message": f"Payroll {code} deleted successfully"}
