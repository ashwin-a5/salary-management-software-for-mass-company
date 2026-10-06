import calendar
from datetime import date, datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import (
    Employee, Department, Payroll, PayrollItem, Bonus, Deduction, AuditLog, User
)
from app.schemas import DashboardStats, AuditLogOut
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    total_emp = db.query(Employee).count()
    active_emp = db.query(Employee).filter(Employee.status == "active").count()
    inactive_emp = total_emp - active_emp
    total_dept = db.query(Department).count()
    
    # Current month payroll stats
    current_payrolls = db.query(Payroll).filter(
        Payroll.month == current_month,
        Payroll.year == current_year
    ).all()
    
    current_expense = sum(p.total_net_pay for p in current_payrolls)
    
    pending_payrolls = db.query(Payroll).filter(Payroll.status.in_(["draft", "processing"])).count()
    paid_payrolls = db.query(Payroll).filter(Payroll.status == "paid").count()
    
    total_bonuses = db.query(func.sum(Bonus.amount)).filter(Bonus.status.in_(["approved", "paid"])).scalar() or 0.0
    total_deductions = db.query(func.sum(Deduction.amount)).filter(Deduction.status.in_(["approved", "applied"])).scalar() or 0.0
    
    # 1. Monthly Expense Chart (last 6 months or all months in current year)
    monthly_payrolls = db.query(
        Payroll.year,
        Payroll.month,
        func.sum(Payroll.total_gross_pay).label("gross"),
        func.sum(Payroll.total_net_pay).label("net"),
        func.sum(Payroll.total_deductions).label("deductions")
    ).group_by(Payroll.year, Payroll.month).order_by(Payroll.year.asc(), Payroll.month.asc()).all()
    
    monthly_chart = []
    for r in monthly_payrolls:
        monthly_chart.append({
            "name": f"{calendar.month_abbr[r.month]} {r.year}",
            "month": r.month,
            "year": r.year,
            "gross": round(float(r.gross or 0), 2),
            "net": round(float(r.net or 0), 2),
            "deductions": round(float(r.deductions or 0), 2)
        })
        
    # If empty, provide reasonable baseline
    if not monthly_chart:
        monthly_chart = [
            {"name": f"{calendar.month_abbr[current_month]} {current_year}", "month": current_month, "year": current_year, "gross": 0.0, "net": 0.0, "deductions": 0.0}
        ]
        
    # 2. Department-wise salary expense
    dept_expenses = db.query(
        PayrollItem.department_name,
        func.sum(PayrollItem.net_salary).label("total_net")
    ).group_by(PayrollItem.department_name).all()
    
    dept_expense_chart = []
    for d in dept_expenses:
        if d.department_name:
            dept_expense_chart.append({
                "name": d.department_name,
                "value": round(float(d.total_net or 0), 2)
            })
            
    # 3. Employee count by Department
    dept_employees = db.query(
        Department.name,
        func.count(Employee.id).label("emp_count")
    ).outerjoin(Employee, Department.id == Employee.department_id).group_by(Department.id).all()
    
    dept_employee_chart = []
    for de in dept_employees:
        dept_employee_chart.append({
            "name": de.name,
            "count": de.emp_count
        })
        
    # 4. Payroll status breakdown
    status_counts = db.query(
        Payroll.status,
        func.count(Payroll.id).label("cnt")
    ).group_by(Payroll.status).all()
    
    status_chart = []
    for sc in status_counts:
        status_chart.append({
            "status": sc.status.upper(),
            "count": sc.cnt
        })
        
    # 5. Recent audit logs
    recent_logs = db.query(AuditLog).order_by(desc(AuditLog.id)).limit(8).all()
    
    return {
        "total_employees": total_emp,
        "active_employees": active_emp,
        "inactive_employees": inactive_emp,
        "total_departments": total_dept,
        "current_month_payroll_expense": round(current_expense, 2),
        "pending_payroll_count": pending_payrolls,
        "paid_payroll_count": paid_payrolls,
        "total_bonuses_distributed": round(total_bonuses, 2),
        "total_deductions_collected": round(total_deductions, 2),
        "monthly_expense_chart": monthly_chart,
        "department_expense_chart": dept_expense_chart,
        "department_employee_chart": dept_employee_chart,
        "payroll_status_breakdown": status_chart,
        "recent_audit_logs": [AuditLogOut.from_orm(l) for l in recent_logs]
    }
