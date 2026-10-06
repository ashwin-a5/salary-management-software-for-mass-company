import calendar
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_

from app.database import get_db
from app.models import (
    Payroll, PayrollItem, Employee, Department, Designation, Bonus, Deduction, Attendance, User
)
from app.auth import get_current_user, require_hr_or_admin
from app.services.export_service import export_to_excel, export_to_csv

router = APIRouter(prefix="/reports", tags=["Payroll Reports"])

@router.get("/monthly")
def get_monthly_payroll_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000, le=2100),
    department_id: Optional[int] = None,
    format: Optional[str] = Query(None, regex="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    query = db.query(PayrollItem).join(Payroll).filter(
        Payroll.month == month,
        Payroll.year == year
    )
    if department_id:
        query = query.filter(Payroll.department_id == department_id)
        
    items = query.all()
    
    data = []
    for itm in items:
        data.append({
            "Employee Code": itm.employee_code,
            "Employee Name": itm.employee_name,
            "Department": itm.department_name or "N/A",
            "Designation": itm.designation_name or "N/A",
            "Bank Account": itm.bank_account_no or "N/A",
            "Working Days": itm.total_working_days,
            "Present Days": itm.present_days,
            "Unpaid Days": itm.unpaid_leave_days + itm.absent_days,
            "Basic Salary": itm.basic_salary,
            "HRA": itm.hra,
            "DA": itm.da,
            "Allowances": itm.conveyance_allowance + itm.medical_allowance + itm.special_allowance,
            "Bonus/Incentive": itm.performance_bonus + itm.incentives + itm.other_earnings,
            "Overtime Pay": itm.overtime_pay,
            "Gross Salary": itm.gross_salary,
            "EPF (Employee)": itm.epf_employee,
            "ESI (Employee)": itm.esi_employee,
            "Prof. Tax": itm.professional_tax,
            "TDS (Tax)": itm.tds,
            "Leave Deductions": itm.unpaid_leave_deduction,
            "Other Deductions": itm.loan_advance_deduction + itm.late_penalty_deduction + itm.other_deductions,
            "Total Deductions": itm.total_deductions,
            "Net Take Home": itm.net_salary,
            "Status": itm.payment_status.upper()
        })
        
    if format == "excel":
        excel_bytes = export_to_excel(data, sheet_name=f"Payroll_{month}_{year}")
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Payroll_Report_{calendar.month_name[month]}_{year}.xlsx"}
        )
    elif format == "csv":
        csv_bytes = export_to_csv(data)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=Payroll_Report_{calendar.month_name[month]}_{year}.csv"}
        )
        
    return {
        "month": month,
        "month_name": calendar.month_name[month],
        "year": year,
        "total_records": len(data),
        "total_gross": sum(d["Gross Salary"] for d in data),
        "total_deductions": sum(d["Total Deductions"] for d in data),
        "total_net": sum(d["Net Take Home"] for d in data),
        "records": data
    }

@router.get("/annual")
def get_annual_payroll_report(
    year: int = Query(..., ge=2000, le=2100),
    format: Optional[str] = Query(None, regex="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    payrolls = db.query(Payroll).filter(Payroll.year == year, Payroll.status.in_(["approved", "paid"])).order_by(Payroll.month.asc()).all()
    
    monthly_data = []
    for p in payrolls:
        monthly_data.append({
            "Month": calendar.month_name[p.month],
            "Month Number": p.month,
            "Total Employees": p.total_employees,
            "Gross Salary Expense": p.total_gross_pay,
            "Total Deductions": p.total_deductions,
            "Net Salary Paid": p.total_net_pay,
            "Employer PF Expense": p.total_employer_pf,
            "Employer ESI Expense": p.total_employer_esi,
            "Total Company Cost": p.total_gross_pay + p.total_employer_pf + p.total_employer_esi,
            "Status": p.status.upper()
        })
        
    if format == "excel":
        excel_bytes = export_to_excel(monthly_data, sheet_name=f"Annual_{year}")
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Annual_Payroll_Report_{year}.xlsx"}
        )
    elif format == "csv":
        csv_bytes = export_to_csv(monthly_data)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=Annual_Payroll_Report_{year}.csv"}
        )
        
    return {
        "year": year,
        "total_gross": sum(m["Gross Salary Expense"] for m in monthly_data),
        "total_net": sum(m["Net Salary Paid"] for m in monthly_data),
        "total_pf": sum(m["Employer PF Expense"] for m in monthly_data),
        "total_esi": sum(m["Employer ESI Expense"] for m in monthly_data),
        "total_company_cost": sum(m["Total Company Cost"] for m in monthly_data),
        "records": monthly_data
    }

@router.get("/department")
def get_department_payroll_report(
    year: int = Query(..., ge=2000, le=2100),
    month: Optional[int] = None,
    format: Optional[str] = Query(None, regex="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    query = db.query(PayrollItem).join(Payroll).filter(Payroll.year == year)
    if month:
        query = query.filter(Payroll.month == month)
        
    items = query.all()
    
    dep_dict = {}
    for itm in items:
        dep_name = itm.department_name or "Unassigned"
        if dep_name not in dep_dict:
            dep_dict[dep_name] = {
                "Department": dep_name,
                "Employee Count": set(),
                "Gross Salary": 0.0,
                "Total Deductions": 0.0,
                "Net Salary": 0.0,
                "Employer PF": 0.0,
                "Employer ESI": 0.0
            }
        dep_dict[dep_name]["Employee Count"].add(itm.employee_id)
        dep_dict[dep_name]["Gross Salary"] += itm.gross_salary
        dep_dict[dep_name]["Total Deductions"] += itm.total_deductions
        dep_dict[dep_name]["Net Salary"] += itm.net_salary
        dep_dict[dep_name]["Employer PF"] += itm.epf_employer
        dep_dict[dep_name]["Employer ESI"] += itm.esi_employer

    records = []
    for dep, v in dep_dict.items():
        records.append({
            "Department": v["Department"],
            "Employees": len(v["Employee Count"]),
            "Gross Salary": round(v["Gross Salary"], 2),
            "Total Deductions": round(v["Total Deductions"], 2),
            "Net Salary": round(v["Net Salary"], 2),
            "Employer PF": round(v["Employer PF"], 2),
            "Employer ESI": round(v["Employer ESI"], 2),
            "Total Cost": round(v["Gross Salary"] + v["Employer PF"] + v["Employer ESI"], 2)
        })
        
    if format == "excel":
        excel_bytes = export_to_excel(records, sheet_name="Department_Report")
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Department_Payroll_Report_{year}.xlsx"}
        )
    elif format == "csv":
        csv_bytes = export_to_csv(records)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=Department_Payroll_Report_{year}.csv"}
        )
        
    return {"year": year, "month": month, "records": records}

@router.get("/tax")
def get_tax_tds_report(
    year: int = Query(..., ge=2000, le=2100),
    month: Optional[int] = None,
    format: Optional[str] = Query(None, regex="^(excel|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    query = db.query(PayrollItem).join(Payroll).filter(Payroll.year == year)
    if month:
        query = query.filter(Payroll.month == month)
        
    items = query.all()
    records = []
    for itm in items:
        records.append({
            "Employee Code": itm.employee_code,
            "Employee Name": itm.employee_name,
            "PAN Number": itm.pan_number or "N/A",
            "Gross Earnings": itm.gross_salary,
            "EPF (80C Deduction)": itm.epf_employee,
            "Professional Tax": itm.professional_tax,
            "TDS Tax Deducted": itm.tds,
            "Payment Status": itm.payment_status.upper()
        })
        
    if format == "excel":
        excel_bytes = export_to_excel(records, sheet_name="TDS_Report")
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Tax_TDS_Report_{year}.xlsx"}
        )
    elif format == "csv":
        csv_bytes = export_to_csv(records)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=Tax_TDS_Report_{year}.csv"}
        )
        
    return {
        "year": year,
        "month": month,
        "total_tds": sum(r["TDS Tax Deducted"] for r in records),
        "total_ptax": sum(r["Professional Tax"] for r in records),
        "records": records
    }
