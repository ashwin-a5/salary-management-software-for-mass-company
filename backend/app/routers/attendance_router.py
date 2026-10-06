import calendar
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_

from app.database import get_db
from app.models import Attendance, Employee, Department, User
from app.schemas import (
    AttendanceOut, AttendanceCreate, AttendanceBulkCreate
)
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])

def build_attendance_out(att: Attendance) -> AttendanceOut:
    out = AttendanceOut.from_orm(att)
    if att.employee:
        out.employee_name = f"{att.employee.first_name} {att.employee.last_name}"
        out.employee_code = att.employee.employee_code
        out.department_name = att.employee.department.name if att.employee.department else None
    return out

@router.get("", response_model=List[AttendanceOut])
def list_attendance(
    target_date: Optional[date] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Attendance).join(Employee)
    
    # If role is employee, restrict to own attendance
    if current_user.role == "employee":
        if not current_user.employee_id:
            return []
        query = query.filter(Attendance.employee_id == current_user.employee_id)
    elif employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
        
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if target_date:
        query = query.filter(Attendance.date == target_date)
    if month:
        query = query.filter(extract('month', Attendance.date) == month)
    if year:
        query = query.filter(extract('year', Attendance.date) == year)
        
    records = query.order_by(Attendance.date.desc(), Attendance.id.desc()).all()
    return [build_attendance_out(r) for r in records]

@router.post("", response_model=AttendanceOut)
def record_attendance(
    req: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    # Check if record for employee on this date already exists
    existing = db.query(Attendance).filter(
        Attendance.employee_id == req.employee_id,
        Attendance.date == req.date
    ).first()
    
    if existing:
        existing.status = req.status
        existing.clock_in = req.clock_in
        existing.clock_out = req.clock_out
        existing.overtime_hours = req.overtime_hours
        existing.remarks = req.remarks
        att = existing
    else:
        att = Attendance(
            employee_id=req.employee_id,
            date=req.date,
            status=req.status,
            clock_in=req.clock_in,
            clock_out=req.clock_out,
            overtime_hours=req.overtime_hours,
            remarks=req.remarks
        )
        db.add(att)
        
    db.commit()
    db.refresh(att)
    return build_attendance_out(att)

@router.post("/bulk")
def record_bulk_attendance(
    req: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    count = 0
    for item in req.records:
        existing = db.query(Attendance).filter(
            Attendance.employee_id == item.employee_id,
            Attendance.date == req.date
        ).first()
        
        if existing:
            existing.status = item.status
            existing.clock_in = item.clock_in
            existing.clock_out = item.clock_out
            existing.overtime_hours = item.overtime_hours
            existing.remarks = item.remarks
        else:
            att = Attendance(
                employee_id=item.employee_id,
                date=req.date,
                status=item.status,
                clock_in=item.clock_in,
                clock_out=item.clock_out,
                overtime_hours=item.overtime_hours,
                remarks=item.remarks
            )
            db.add(att)
        count += 1
        
    db.commit()
    log_activity(db, action="ATTENDANCE_BULK_RECORDED", module="ATTENDANCE", user=current_user, details=f"Bulk logged attendance for {count} employees on {req.date}")
    return {"message": f"Successfully recorded attendance for {count} employees on {req.date}"}

@router.get("/summary/{employee_id}")
def get_employee_monthly_summary(
    employee_id: int,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee" and current_user.employee_id != employee_id:
        raise HTTPException(status_code=403, detail="Access denied to other employee attendance")
        
    days_in_month = calendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)
    
    attendances = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()
    
    summary = {
        "month": month,
        "year": year,
        "days_in_month": days_in_month,
        "present": sum(1 for a in attendances if a.status == "present"),
        "absent": sum(1 for a in attendances if a.status == "absent"),
        "half_day": sum(1 for a in attendances if a.status == "half_day"),
        "paid_leave": sum(1 for a in attendances if a.status == "paid_leave"),
        "unpaid_leave": sum(1 for a in attendances if a.status == "unpaid_leave"),
        "holiday": sum(1 for a in attendances if a.status == "holiday"),
        "week_off": sum(1 for a in attendances if a.status == "week_off"),
        "overtime_hours": sum(a.overtime_hours or 0.0 for a in attendances)
    }
    return summary
