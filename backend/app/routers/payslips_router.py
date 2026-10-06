import calendar
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import io

from app.database import get_db
from app.models import Payslip, PayrollItem, Employee, User
from app.schemas import PayrollItemOut
from app.auth import get_current_user
from app.services.pdf_service import generate_payslip_pdf
from app.services.audit_service import log_activity

router = APIRouter(prefix="/payslips", tags=["Payslips"])

@router.get("")
def list_payslips(
    year: Optional[int] = None,
    month: Optional[int] = None,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payslip).join(PayrollItem).join(Employee)
    
    if current_user.role == "employee":
        if not current_user.employee_id:
            return []
        query = query.filter(Payslip.employee_id == current_user.employee_id)
    elif employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
        
    if year:
        query = query.filter(Payslip.year == year)
    if month:
        query = query.filter(Payslip.month == month)
        
    payslips = query.order_by(desc(Payslip.year), desc(Payslip.month), desc(Payslip.id)).all()
    
    results = []
    for ps in payslips:
        item = ps.payroll_item
        results.append({
            "id": ps.id,
            "payslip_number": ps.payslip_number,
            "month": ps.month,
            "month_name": calendar.month_name[ps.month],
            "year": ps.year,
            "employee_id": ps.employee_id,
            "employee_code": item.employee_code if item else "",
            "employee_name": item.employee_name if item else "",
            "department_name": item.department_name if item else "",
            "gross_salary": item.gross_salary if item else 0.0,
            "total_deductions": item.total_deductions if item else 0.0,
            "net_salary": item.net_salary if item else 0.0,
            "payment_status": item.payment_status if item else "pending",
            "generated_at": ps.generated_at
        })
    return results

@router.get("/{payslip_id}")
def get_payslip_detail(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ps = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not ps:
        raise HTTPException(status_code=404, detail="Payslip not found")
        
    if current_user.role == "employee" and current_user.employee_id != ps.employee_id:
        raise HTTPException(status_code=403, detail="Access denied to other employee payslip")
        
    item = ps.payroll_item
    item_out = PayrollItemOut.from_orm(item)
    item_out.payslip_id = ps.id
    return {
        "payslip": {
            "id": ps.id,
            "payslip_number": ps.payslip_number,
            "month": ps.month,
            "month_name": calendar.month_name[ps.month],
            "year": ps.year,
            "generated_at": ps.generated_at
        },
        "item": item_out
    }

@router.get("/{payslip_id}/download-pdf")
def download_payslip_pdf(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ps = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not ps:
        raise HTTPException(status_code=404, detail="Payslip not found")
        
    if current_user.role == "employee" and current_user.employee_id != ps.employee_id:
        raise HTTPException(status_code=403, detail="Access denied to download other employee payslip")
        
    item = ps.payroll_item
    if not item:
        raise HTTPException(status_code=404, detail="Payroll item not found for payslip")
        
    pdf_bytes = generate_payslip_pdf(item, ps)
    
    filename = f"Payslip_{ps.payslip_number}_{calendar.month_name[ps.month]}_{ps.year}.pdf"
    
    log_activity(
        db,
        action="PAYSLIP_DOWNLOADED",
        module="PAYSLIP",
        user=current_user,
        record_id=str(ps.id),
        details=f"Downloaded payslip PDF {ps.payslip_number}"
    )
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
