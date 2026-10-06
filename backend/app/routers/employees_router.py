import json
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import (
    Employee, Department, Designation, SalaryStructure, User, SalaryHistory
)
from app.schemas import (
    EmployeeOut, EmployeeCreate, EmployeeUpdate
)
from app.auth import get_current_user, require_hr_or_admin, get_password_hash
from app.services.audit_service import log_activity

router = APIRouter(prefix="/employees", tags=["Employees"])

def build_employee_out(emp: Employee) -> EmployeeOut:
    out = EmployeeOut.from_orm(emp)
    out.full_name = f"{emp.first_name} {emp.last_name}"
    out.department_name = emp.department.name if emp.department else None
    out.designation_title = emp.designation.title if emp.designation else None
    out.reporting_manager_name = f"{emp.reporting_manager.first_name} {emp.reporting_manager.last_name}" if emp.reporting_manager else None
    return out

@router.get("", response_model=List[EmployeeOut])
def list_employees(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    designation_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Employee users can only see directory overview or own profile
    query = db.query(Employee)
    
    if current_user.role == "employee":
        # Allow employee to list teammates or return own
        pass # Employees can view directory with basic info, sensitive fields masked in frontend
        
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if designation_id:
        query = query.filter(Employee.designation_id == designation_id)
    if status:
        query = query.filter(Employee.status == status)
        
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Employee.employee_code.ilike(search_fmt),
                Employee.first_name.ilike(search_fmt),
                Employee.last_name.ilike(search_fmt),
                Employee.email.ilike(search_fmt),
                Employee.phone.ilike(search_fmt)
            )
        )
        
    employees = query.order_by(Employee.id.desc()).all()
    return [build_employee_out(e) for e in employees]

@router.get("/{emp_id}", response_model=EmployeeOut)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee" and current_user.employee_id != emp_id:
        raise HTTPException(status_code=403, detail="Access denied to other employee records")
        
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    return build_employee_out(emp)

@router.post("", response_model=EmployeeOut)
def create_employee(
    req: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    # Check duplicate code or email
    if db.query(Employee).filter(Employee.employee_code == req.employee_code).first():
        raise HTTPException(status_code=400, detail="Employee Code already exists")
    if db.query(Employee).filter(Employee.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
        
    # Auto calculate default HRA/DA if not set
    basic = req.basic_salary or 0.0
    hra = req.hra if req.hra > 0 else (basic * 0.40) # default 40% HRA
    da = req.da if req.da > 0 else (basic * 0.10)   # default 10% DA
    conveyance = req.conveyance_allowance if req.conveyance_allowance > 0 else 1600.0
    medical = req.medical_allowance if req.medical_allowance > 0 else 1250.0
    special = req.special_allowance if req.special_allowance > 0 else (basic * 0.15)
    
    emp = Employee(
        employee_code=req.employee_code,
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        phone=req.phone,
        date_of_birth=req.date_of_birth,
        gender=req.gender,
        profile_photo_url=req.profile_photo_url,
        
        address=req.address,
        city=req.city,
        state=req.state,
        postal_code=req.postal_code,
        country=req.country or "India",
        emergency_contact_name=req.emergency_contact_name,
        emergency_contact_phone=req.emergency_contact_phone,
        
        department_id=req.department_id,
        designation_id=req.designation_id,
        employment_type=req.employment_type,
        date_of_joining=req.date_of_joining,
        reporting_manager_id=req.reporting_manager_id,
        status=req.status or "active",
        
        bank_name=req.bank_name,
        bank_account_no=req.bank_account_no,
        bank_ifsc=req.bank_ifsc,
        bank_branch=req.bank_branch,
        pan_number=req.pan_number,
        uan_number=req.uan_number,
        epf_number=req.epf_number,
        esi_number=req.esi_number,
        payment_mode=req.payment_mode or "bank_transfer",
        
        basic_salary=basic,
        salary_structure_id=req.salary_structure_id,
        hra=hra,
        da=da,
        conveyance_allowance=conveyance,
        medical_allowance=medical,
        special_allowance=special,
        performance_bonus=req.performance_bonus,
        overtime_rate_per_hour=req.overtime_rate_per_hour,
        epf_enabled=req.epf_enabled,
        esi_enabled=req.esi_enabled,
        professional_tax=req.professional_tax,
        tds_amount=req.tds_amount,
        custom_allowances_json=req.custom_allowances_json or "{}",
        custom_deductions_json=req.custom_deductions_json or "{}"
    )
    db.add(emp)
    db.flush()
    
    # Optional create user login account
    if req.create_user_account:
        username = req.email.split("@")[0].lower()
        if db.query(User).filter(User.username == username).first():
            username = f"{username}_{emp.id}"
            
        new_user = User(
            username=username,
            email=req.email,
            hashed_password=get_password_hash(req.user_password or "Employee@123"),
            full_name=f"{emp.first_name} {emp.last_name}",
            role="employee",
            is_active=True,
            employee_id=emp.id
        )
        db.add(new_user)
        db.flush()
        emp.user_id = new_user.id
        
    # Record initial salary in SalaryHistory
    initial_struct = {
        "basic_salary": basic,
        "hra": hra,
        "da": da,
        "conveyance": conveyance,
        "medical": medical,
        "special": special,
        "ptax": req.professional_tax,
        "tds": req.tds_amount
    }
    history = SalaryHistory(
        employee_id=emp.id,
        previous_salary=0.0,
        new_salary=basic,
        previous_structure_details="Initial Joining Salary Structure",
        new_structure_details=json.dumps(initial_struct),
        effective_date=req.date_of_joining,
        reason="Initial Joining Offer & Salary Structure",
        changed_by_user_id=current_user.id
    )
    db.add(history)
    db.commit()
    db.refresh(emp)
    
    log_activity(db, action="EMPLOYEE_CREATED", module="EMPLOYEE", user=current_user, record_id=str(emp.id), details=f"Added employee {emp.first_name} {emp.last_name} ({emp.employee_code})")
    return build_employee_out(emp)

@router.put("/{emp_id}", response_model=EmployeeOut)
def update_employee(
    emp_id: int,
    req: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    old_basic = emp.basic_salary
    old_snapshot = {
        "basic_salary": emp.basic_salary,
        "hra": emp.hra,
        "da": emp.da,
        "conveyance": emp.conveyance_allowance,
        "medical": emp.medical_allowance,
        "special": emp.special_allowance,
        "ptax": emp.professional_tax,
        "tds": emp.tds_amount
    }
    
    # Update personal & job info
    if req.first_name is not None: emp.first_name = req.first_name
    if req.last_name is not None: emp.last_name = req.last_name
    if req.email is not None: emp.email = req.email
    if req.phone is not None: emp.phone = req.phone
    if req.date_of_birth is not None: emp.date_of_birth = req.date_of_birth
    if req.gender is not None: emp.gender = req.gender
    if req.profile_photo_url is not None: emp.profile_photo_url = req.profile_photo_url
    if req.address is not None: emp.address = req.address
    if req.city is not None: emp.city = req.city
    if req.state is not None: emp.state = req.state
    if req.postal_code is not None: emp.postal_code = req.postal_code
    if req.country is not None: emp.country = req.country
    if req.emergency_contact_name is not None: emp.emergency_contact_name = req.emergency_contact_name
    if req.emergency_contact_phone is not None: emp.emergency_contact_phone = req.emergency_contact_phone
    
    if req.department_id is not None: emp.department_id = req.department_id
    if req.designation_id is not None: emp.designation_id = req.designation_id
    if req.employment_type is not None: emp.employment_type = req.employment_type
    if req.date_of_joining is not None: emp.date_of_joining = req.date_of_joining
    if req.reporting_manager_id is not None: emp.reporting_manager_id = req.reporting_manager_id
    if req.status is not None: emp.status = req.status
    
    if req.bank_name is not None: emp.bank_name = req.bank_name
    if req.bank_account_no is not None: emp.bank_account_no = req.bank_account_no
    if req.bank_ifsc is not None: emp.bank_ifsc = req.bank_ifsc
    if req.bank_branch is not None: emp.bank_branch = req.bank_branch
    if req.pan_number is not None: emp.pan_number = req.pan_number
    if req.uan_number is not None: emp.uan_number = req.uan_number
    if req.epf_number is not None: emp.epf_number = req.epf_number
    if req.esi_number is not None: emp.esi_number = req.esi_number
    if req.payment_mode is not None: emp.payment_mode = req.payment_mode
    
    salary_changed = False
    if req.basic_salary is not None and req.basic_salary != emp.basic_salary:
        emp.basic_salary = req.basic_salary
        salary_changed = True
    if req.salary_structure_id is not None: emp.salary_structure_id = req.salary_structure_id
    if req.hra is not None: emp.hra = req.hra
    if req.da is not None: emp.da = req.da
    if req.conveyance_allowance is not None: emp.conveyance_allowance = req.conveyance_allowance
    if req.medical_allowance is not None: emp.medical_allowance = req.medical_allowance
    if req.special_allowance is not None: emp.special_allowance = req.special_allowance
    if req.performance_bonus is not None: emp.performance_bonus = req.performance_bonus
    if req.overtime_rate_per_hour is not None: emp.overtime_rate_per_hour = req.overtime_rate_per_hour
    if req.epf_enabled is not None: emp.epf_enabled = req.epf_enabled
    if req.esi_enabled is not None: emp.esi_enabled = req.esi_enabled
    if req.professional_tax is not None: emp.professional_tax = req.professional_tax
    if req.tds_amount is not None: emp.tds_amount = req.tds_amount
    if req.custom_allowances_json is not None: emp.custom_allowances_json = req.custom_allowances_json
    if req.custom_deductions_json is not None: emp.custom_deductions_json = req.custom_deductions_json
    
    # If salary was updated, record SalaryHistory
    if salary_changed or (req.hra is not None and req.hra != old_snapshot["hra"]):
        new_snapshot = {
            "basic_salary": emp.basic_salary,
            "hra": emp.hra,
            "da": emp.da,
            "conveyance": emp.conveyance_allowance,
            "medical": emp.medical_allowance,
            "special": emp.special_allowance,
            "ptax": emp.professional_tax,
            "tds": emp.tds_amount
        }
        history = SalaryHistory(
            employee_id=emp.id,
            previous_salary=old_basic,
            new_salary=emp.basic_salary,
            previous_structure_details=json.dumps(old_snapshot),
            new_structure_details=json.dumps(new_snapshot),
            effective_date=date.today(),
            reason=req.salary_change_reason or "Salary Structure Revision",
            changed_by_user_id=current_user.id
        )
        db.add(history)
        
    db.commit()
    db.refresh(emp)
    log_activity(db, action="EMPLOYEE_UPDATED", module="EMPLOYEE", user=current_user, record_id=str(emp.id), details=f"Updated employee {emp.first_name} {emp.last_name}")
    return build_employee_out(emp)

@router.patch("/{emp_id}/status")
def toggle_employee_status(
    emp_id: int,
    status: str = Query(..., regex="^(active|inactive|terminated|on_leave)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    emp.status = status
    if emp.user_account:
        emp.user_account.is_active = (status == "active")
        
    db.commit()
    log_activity(db, action="EMPLOYEE_STATUS_CHANGED", module="EMPLOYEE", user=current_user, record_id=str(emp.id), details=f"Changed status of {emp.first_name} to {status}")
    return {"message": f"Employee status updated to {status}"}

@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    name = f"{emp.first_name} {emp.last_name}"
    db.delete(emp)
    db.commit()
    log_activity(db, action="EMPLOYEE_DELETED", module="EMPLOYEE", user=current_user, record_id=str(emp_id), details=f"Deleted employee {name}")
    return {"message": "Employee deleted successfully"}
