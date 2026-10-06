import calendar
import json
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_, or_

from app.config import settings
from app.models import (
    Employee, Payroll, PayrollItem, Attendance, Leave, Bonus, Deduction, Department, Payslip
)

def round_money(val: float) -> float:
    d = Decimal(str(val))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def get_days_in_month(year: int, month: int) -> int:
    _, num_days = calendar.monthrange(year, month)
    return num_days

def calculate_employee_payroll(
    db: Session,
    employee: Employee,
    month: int,
    year: int
) -> Dict[str, Any]:
    days_in_month = get_days_in_month(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)
    
    # 1. Fetch Attendance records
    attendances = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()
    
    present_days = 0.0
    absent_days = 0.0
    half_days = 0.0
    paid_leave_days = 0.0
    unpaid_leave_days = 0.0
    holidays = 0.0
    week_offs = 0.0
    overtime_hours = 0.0
    
    for att in attendances:
        st = att.status.lower()
        if st == "present":
            present_days += 1.0
        elif st == "absent":
            absent_days += 1.0
        elif st == "half_day":
            half_days += 1.0
        elif st == "paid_leave":
            paid_leave_days += 1.0
        elif st == "unpaid_leave":
            unpaid_leave_days += 1.0
        elif st == "holiday":
            holidays += 1.0
        elif st == "week_off":
            week_offs += 1.0
        
        if att.overtime_hours:
            overtime_hours += float(att.overtime_hours)
            
    # Also integrate approved Leave records that overlap
    leaves = db.query(Leave).filter(
        Leave.employee_id == employee.id,
        Leave.status == "approved",
        Leave.start_date <= end_date,
        Leave.end_date >= start_date
    ).all()
    
    # If no attendance records logged for the entire month, default to full attendance
    total_logged_days = present_days + absent_days + half_days + paid_leave_days + unpaid_leave_days + holidays + week_offs
    if total_logged_days == 0:
        present_days = float(days_in_month)
    
    # Unpaid penalty days
    unpaid_days = unpaid_leave_days + absent_days + (half_days * 0.5)
    
    # 2. Earnings calculation
    basic_salary = round_money(employee.basic_salary or 0.0)
    hra = round_money(employee.hra or 0.0)
    da = round_money(employee.da or 0.0)
    conveyance = round_money(employee.conveyance_allowance or 0.0)
    medical = round_money(employee.medical_allowance or 0.0)
    special = round_money(employee.special_allowance or 0.0)
    perf_bonus = round_money(employee.performance_bonus or 0.0)
    
    # Overtime pay
    ot_rate = employee.overtime_rate_per_hour
    if not ot_rate or ot_rate <= 0:
        # standard 1.5x hourly rate: (Basic / (days_in_month * 8)) * 1.5
        hourly_rate = (basic_salary / (days_in_month * 8.0)) if days_in_month > 0 else 0.0
        ot_rate = hourly_rate * 1.5
    overtime_pay = round_money(overtime_hours * ot_rate)
    
    # Bonuses from Bonus table
    bonuses = db.query(Bonus).filter(
        Bonus.employee_id == employee.id,
        Bonus.month == month,
        Bonus.year == year,
        Bonus.status.in_(["approved", "paid"])
    ).all()
    
    incentives = 0.0
    other_earnings = 0.0
    for b in bonuses:
        if b.bonus_type in ["incentive", "performance"]:
            incentives += b.amount
        else:
            other_earnings += b.amount
            
    incentives = round_money(incentives)
    other_earnings = round_money(other_earnings)
    
    # Custom allowances JSON
    custom_allowances = {}
    try:
        if employee.custom_allowances_json:
            custom_allowances = json.loads(employee.custom_allowances_json)
            for k, v in custom_allowances.items():
                other_earnings += round_money(float(v))
    except Exception:
        pass
    
    # Fixed monthly gross before unpaid leave deduction
    base_gross = basic_salary + hra + da + conveyance + medical + special + perf_bonus
    
    # 3. Deductions calculation
    # Unpaid leave deduction
    per_day_salary = (base_gross / float(days_in_month)) if days_in_month > 0 else 0.0
    unpaid_leave_deduction = round_money(unpaid_days * per_day_salary)
    
    gross_salary = round_money(base_gross + overtime_pay + incentives + other_earnings)
    
    # EPF calculation (12% of basic, standard statutory)
    epf_employee = 0.0
    epf_employer = 0.0
    if employee.epf_enabled:
        epf_base = min(basic_salary, settings.EPF_WAGE_CEILING) if basic_salary > settings.EPF_WAGE_CEILING else basic_salary
        # Standard 12%
        epf_employee = round_money(epf_base * (settings.EPF_EMPLOYEE_PERCENT / 100.0))
        epf_employer = round_money(epf_base * (settings.EPF_EMPLOYER_PERCENT / 100.0))
        
    # ESI calculation (0.75% employee, 3.25% employer if Gross <= 21000)
    esi_employee = 0.0
    esi_employer = 0.0
    if employee.esi_enabled and gross_salary <= settings.ESI_WAGE_CEILING:
        esi_employee = round_money(gross_salary * (settings.ESI_EMPLOYEE_PERCENT / 100.0))
        esi_employer = round_money(gross_salary * (settings.ESI_EMPLOYER_PERCENT / 100.0))
        
    professional_tax = round_money(employee.professional_tax or 0.0)
    tds = round_money(employee.tds_amount or 0.0)
    
    # Deductions from Deduction table
    deductions = db.query(Deduction).filter(
        Deduction.employee_id == employee.id,
        Deduction.month == month,
        Deduction.year == year,
        Deduction.status.in_(["approved", "applied"])
    ).all()
    
    loan_advance_deduction = 0.0
    late_penalty_deduction = 0.0
    other_deductions = 0.0
    for d in deductions:
        if d.deduction_type == "loan_advance":
            loan_advance_deduction += d.amount
        elif d.deduction_type == "late_penalty":
            late_penalty_deduction += d.amount
        else:
            other_deductions += d.amount
            
    loan_advance_deduction = round_money(loan_advance_deduction)
    late_penalty_deduction = round_money(late_penalty_deduction)
    other_deductions = round_money(other_deductions)
    
    # Custom deductions JSON
    try:
        if employee.custom_deductions_json:
            custom_ded = json.loads(employee.custom_deductions_json)
            for k, v in custom_ded.items():
                other_deductions += round_money(float(v))
    except Exception:
        pass
        
    total_deductions = round_money(
        epf_employee + esi_employee + professional_tax + tds + 
        unpaid_leave_deduction + loan_advance_deduction + 
        late_penalty_deduction + other_deductions
    )
    
    net_salary = round_money(max(0.0, gross_salary - total_deductions))
    
    breakdown = {
        "days_in_month": days_in_month,
        "unpaid_days": unpaid_days,
        "per_day_salary": round_money(per_day_salary),
        "earnings": {
            "basic_salary": basic_salary,
            "hra": hra,
            "da": da,
            "conveyance": conveyance,
            "medical": medical,
            "special": special,
            "perf_bonus": perf_bonus,
            "overtime_pay": overtime_pay,
            "incentives": incentives,
            "other_earnings": other_earnings,
            "gross_salary": gross_salary,
        },
        "deductions": {
            "epf_employee": epf_employee,
            "esi_employee": esi_employee,
            "professional_tax": professional_tax,
            "tds": tds,
            "unpaid_leave_deduction": unpaid_leave_deduction,
            "loan_advance_deduction": loan_advance_deduction,
            "late_penalty_deduction": late_penalty_deduction,
            "other_deductions": other_deductions,
            "total_deductions": total_deductions,
        },
        "employer_contributions": {
            "epf_employer": epf_employer,
            "esi_employer": esi_employer,
        },
        "net_salary": net_salary
    }
    
    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_code,
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "department_name": employee.department.name if employee.department else "Unassigned",
        "designation_name": employee.designation.title if employee.designation else "Unassigned",
        "bank_account_no": employee.bank_account_no or "N/A",
        "bank_name": employee.bank_name or "N/A",
        "pan_number": employee.pan_number or "N/A",
        
        "total_working_days": float(days_in_month),
        "present_days": present_days,
        "absent_days": absent_days,
        "half_days": half_days,
        "paid_leave_days": paid_leave_days,
        "unpaid_leave_days": unpaid_leave_days,
        "holidays": holidays,
        "week_offs": week_offs,
        "overtime_hours": overtime_hours,
        
        "basic_salary": basic_salary,
        "hra": hra,
        "da": da,
        "conveyance_allowance": conveyance,
        "medical_allowance": medical,
        "special_allowance": special,
        "performance_bonus": perf_bonus,
        "overtime_pay": overtime_pay,
        "incentives": incentives,
        "other_earnings": other_earnings,
        "gross_salary": gross_salary,
        
        "epf_employee": epf_employee,
        "esi_employee": esi_employee,
        "professional_tax": professional_tax,
        "tds": tds,
        "loan_advance_deduction": loan_advance_deduction,
        "unpaid_leave_deduction": unpaid_leave_deduction,
        "late_penalty_deduction": late_penalty_deduction,
        "other_deductions": other_deductions,
        "total_deductions": total_deductions,
        
        "epf_employer": epf_employer,
        "esi_employer": esi_employer,
        "net_salary": net_salary,
        "breakdown_json": json.dumps(breakdown)
    }

def generate_monthly_payroll(
    db: Session,
    month: int,
    year: int,
    department_id: Optional[int] = None,
    employee_ids: Optional[List[int]] = None,
    user_id: Optional[int] = None,
    remarks: Optional[str] = None
) -> Tuple[Payroll, List[str]]:
    warnings = []
    
    # 1. Check if payroll already exists for this month/year and department
    query = db.query(Payroll).filter(Payroll.month == month, Payroll.year == year)
    if department_id:
        query = query.filter(Payroll.department_id == department_id)
    existing = query.first()
    if existing and existing.status in ["approved", "paid"]:
        raise ValueError(f"Payroll for {calendar.month_name[month]} {year} has already been {existing.status.upper()}. Cannot regenerate.")
        
    # Query employees
    emp_query = db.query(Employee).filter(Employee.status == "active")
    if department_id:
        emp_query = emp_query.filter(Employee.department_id == department_id)
    if employee_ids and len(employee_ids) > 0:
        emp_query = emp_query.filter(Employee.id.in_(employee_ids))
        
    employees = emp_query.all()
    if not employees:
        raise ValueError("No active employees found matching the criteria.")
        
    # Generate unique payroll code
    month_str = f"{month:02d}"
    dep_tag = f"DEP{department_id}" if department_id else "ALL"
    payroll_code = f"PAY-{year}{month_str}-{dep_tag}"
    
    # If a draft already exists, reuse or delete its items
    payroll = existing
    if not payroll:
        payroll = Payroll(
            payroll_code=payroll_code,
            month=month,
            year=year,
            department_id=department_id,
            status="draft",
            generated_by_user_id=user_id,
            remarks=remarks
        )
        db.add(payroll)
        db.flush()
    else:
        payroll.status = "draft"
        payroll.remarks = remarks
        # Clear previous items
        db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll.id).delete()
        db.flush()
        
    total_gross = 0.0
    total_deductions = 0.0
    total_net = 0.0
    total_pf = 0.0
    total_esi = 0.0
    items = []
    
    for emp in employees:
        calc = calculate_employee_payroll(db, emp, month, year)
        
        item = PayrollItem(
            payroll_id=payroll.id,
            employee_id=emp.id,
            employee_code=calc["employee_code"],
            employee_name=calc["employee_name"],
            department_name=calc["department_name"],
            designation_name=calc["designation_name"],
            bank_account_no=calc["bank_account_no"],
            bank_name=calc["bank_name"],
            pan_number=calc["pan_number"],
            
            total_working_days=calc["total_working_days"],
            present_days=calc["present_days"],
            absent_days=calc["absent_days"],
            half_days=calc["half_days"],
            paid_leave_days=calc["paid_leave_days"],
            unpaid_leave_days=calc["unpaid_leave_days"],
            holidays=calc["holidays"],
            week_offs=calc["week_offs"],
            overtime_hours=calc["overtime_hours"],
            
            basic_salary=calc["basic_salary"],
            hra=calc["hra"],
            da=calc["da"],
            conveyance_allowance=calc["conveyance_allowance"],
            medical_allowance=calc["medical_allowance"],
            special_allowance=calc["special_allowance"],
            performance_bonus=calc["performance_bonus"],
            overtime_pay=calc["overtime_pay"],
            incentives=calc["incentives"],
            other_earnings=calc["other_earnings"],
            gross_salary=calc["gross_salary"],
            
            epf_employee=calc["epf_employee"],
            esi_employee=calc["esi_employee"],
            professional_tax=calc["professional_tax"],
            tds=calc["tds"],
            loan_advance_deduction=calc["loan_advance_deduction"],
            unpaid_leave_deduction=calc["unpaid_leave_deduction"],
            late_penalty_deduction=calc["late_penalty_deduction"],
            other_deductions=calc["other_deductions"],
            total_deductions=calc["total_deductions"],
            
            epf_employer=calc["epf_employer"],
            esi_employer=calc["esi_employer"],
            net_salary=calc["net_salary"],
            payment_status="pending",
            payment_method=emp.payment_mode or "bank_transfer",
            breakdown_json=calc["breakdown_json"]
        )
        db.add(item)
        db.flush()
        
        # Create Payslip entity automatically
        payslip_num = f"PS-{year}{month_str}-{emp.employee_code}"
        existing_ps = db.query(Payslip).filter(Payslip.payroll_item_id == item.id).first()
        if not existing_ps:
            # Check unique payslip number
            db.query(Payslip).filter(Payslip.payslip_number == payslip_num).delete()
            db.flush()
            payslip = Payslip(
                payroll_item_id=item.id,
                employee_id=emp.id,
                payslip_number=payslip_num,
                month=month,
                year=year
            )
            db.add(payslip)
            
        total_gross += calc["gross_salary"]
        total_deductions += calc["total_deductions"]
        total_net += calc["net_salary"]
        total_pf += (calc["epf_employee"] + calc["epf_employer"])
        total_esi += (calc["esi_employee"] + calc["esi_employer"])
        items.append(item)
        
    payroll.total_employees = len(employees)
    payroll.total_gross_pay = round_money(total_gross)
    payroll.total_deductions = round_money(total_deductions)
    payroll.total_net_pay = round_money(total_net)
    payroll.total_employer_pf = round_money(total_pf)
    payroll.total_employer_esi = round_money(total_esi)
    
    db.commit()
    db.refresh(payroll)
    return payroll, warnings
