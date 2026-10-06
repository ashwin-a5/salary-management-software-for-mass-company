from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

# ----------------- Auth & Users -----------------
class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserOut"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "employee"
    is_active: bool = True
    employee_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ----------------- Departments -----------------
class DepartmentBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    manager_name: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    manager_name: Optional[str] = None

class DepartmentOut(DepartmentBase):
    id: int
    created_at: datetime
    employee_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# ----------------- Designations -----------------
class DesignationBase(BaseModel):
    department_id: int
    title: str
    description: Optional[str] = None
    min_salary: float = 0.0
    max_salary: float = 0.0

class DesignationCreate(DesignationBase):
    pass

class DesignationUpdate(BaseModel):
    department_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None

class DesignationOut(DesignationBase):
    id: int
    created_at: datetime
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ----------------- Salary Structures -----------------
class SalaryComponentBase(BaseModel):
    name: str
    code: str
    component_type: str # earning, deduction
    calculation_type: str # fixed, percentage_of_basic, percentage_of_gross
    default_value: float = 0.0
    is_taxable: bool = True
    is_statutory: bool = False
    is_active: bool = True

class SalaryComponentCreate(SalaryComponentBase):
    pass

class SalaryComponentOut(SalaryComponentBase):
    id: int
    structure_id: int
    
    class Config:
        from_attributes = True

class SalaryStructureBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True

class SalaryStructureCreate(SalaryStructureBase):
    components: Optional[List[SalaryComponentCreate]] = []

class SalaryStructureUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SalaryStructureOut(SalaryStructureBase):
    id: int
    created_at: datetime
    components: List[SalaryComponentOut] = []
    
    class Config:
        from_attributes = True


# ----------------- Employees -----------------
class EmployeeBase(BaseModel):
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: Optional[date] = None
    gender: str = "other"
    profile_photo_url: Optional[str] = None
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "India"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Job
    department_id: Optional[int] = None
    designation_id: Optional[int] = None
    employment_type: str = "full_time"
    date_of_joining: date
    reporting_manager_id: Optional[int] = None
    status: str = "active"
    
    # Bank & Statutory
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    pan_number: Optional[str] = None
    uan_number: Optional[str] = None
    epf_number: Optional[str] = None
    esi_number: Optional[str] = None
    payment_mode: str = "bank_transfer"
    
    # Salary Settings
    basic_salary: float = 0.0
    salary_structure_id: Optional[int] = None
    hra: float = 0.0
    da: float = 0.0
    conveyance_allowance: float = 0.0
    medical_allowance: float = 0.0
    special_allowance: float = 0.0
    performance_bonus: float = 0.0
    overtime_rate_per_hour: float = 0.0
    epf_enabled: bool = True
    esi_enabled: bool = False
    professional_tax: float = 200.0
    tds_amount: float = 0.0
    custom_allowances_json: Optional[str] = "{}"
    custom_deductions_json: Optional[str] = "{}"

class EmployeeCreate(EmployeeBase):
    create_user_account: bool = True
    user_password: Optional[str] = "Employee@123"

class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    profile_photo_url: Optional[str] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    department_id: Optional[int] = None
    designation_id: Optional[int] = None
    employment_type: Optional[str] = None
    date_of_joining: Optional[date] = None
    reporting_manager_id: Optional[int] = None
    status: Optional[str] = None
    
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    pan_number: Optional[str] = None
    uan_number: Optional[str] = None
    epf_number: Optional[str] = None
    esi_number: Optional[str] = None
    payment_mode: Optional[str] = None
    
    basic_salary: Optional[float] = None
    salary_structure_id: Optional[int] = None
    hra: Optional[float] = None
    da: Optional[float] = None
    conveyance_allowance: Optional[float] = None
    medical_allowance: Optional[float] = None
    special_allowance: Optional[float] = None
    performance_bonus: Optional[float] = None
    overtime_rate_per_hour: Optional[float] = None
    epf_enabled: Optional[bool] = None
    esi_enabled: Optional[bool] = None
    professional_tax: Optional[float] = None
    tds_amount: Optional[float] = None
    custom_allowances_json: Optional[str] = None
    custom_deductions_json: Optional[str] = None
    salary_change_reason: Optional[str] = "Salary Revision / Update"

class EmployeeOut(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None
    designation_title: Optional[str] = None
    reporting_manager_name: Optional[str] = None
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ----------------- Salary History -----------------
class SalaryHistoryOut(BaseModel):
    id: int
    employee_id: int
    previous_salary: float
    new_salary: float
    previous_structure_details: Optional[str] = None
    new_structure_details: Optional[str] = None
    effective_date: date
    reason: str
    changed_by_user_id: Optional[int] = None
    changed_by_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ----------------- Attendance -----------------
class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    status: str # present, absent, half_day, paid_leave, unpaid_leave, holiday, week_off
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    overtime_hours: float = 0.0
    remarks: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceBulkItem(BaseModel):
    employee_id: int
    status: str
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    overtime_hours: float = 0.0
    remarks: Optional[str] = None

class AttendanceBulkCreate(BaseModel):
    date: date
    records: List[AttendanceBulkItem]

class AttendanceOut(AttendanceBase):
    id: int
    created_at: datetime
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ----------------- Leaves -----------------
class LeaveBase(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    reason: str

class LeaveCreate(LeaveBase):
    pass

class LeaveStatusUpdate(BaseModel):
    status: str # approved, rejected
    rejection_reason: Optional[str] = None

class LeaveOut(LeaveBase):
    id: int
    status: str
    approved_by_user_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ----------------- Bonuses & Deductions -----------------
class BonusBase(BaseModel):
    employee_id: int
    title: str
    bonus_type: str = "performance"
    amount: float
    month: int
    year: int
    reason: Optional[str] = None
    is_taxable: bool = True
    status: str = "approved"

class BonusCreate(BonusBase):
    pass

class BonusOut(BonusBase):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeductionBase(BaseModel):
    employee_id: int
    title: str
    deduction_type: str = "other"
    amount: float
    month: int
    year: int
    reason: Optional[str] = None
    status: str = "approved"

class DeductionCreate(DeductionBase):
    pass

class DeductionOut(DeductionBase):
    id: int
    created_by_user_id: Optional[int] = None
    created_at: datetime
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ----------------- Payroll -----------------
class PayrollGenerateRequest(BaseModel):
    month: int
    year: int
    department_id: Optional[int] = None
    employee_ids: Optional[List[int]] = None
    remarks: Optional[str] = None

class PayrollStatusUpdate(BaseModel):
    status: str # processing, approved, paid, cancelled
    remarks: Optional[str] = None

class PayrollItemOut(BaseModel):
    id: int
    payroll_id: int
    employee_id: int
    employee_code: str
    employee_name: str
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_name: Optional[str] = None
    pan_number: Optional[str] = None
    
    total_working_days: float
    present_days: float
    absent_days: float
    half_days: float
    paid_leave_days: float
    unpaid_leave_days: float
    holidays: float
    week_offs: float
    overtime_hours: float
    
    basic_salary: float
    hra: float
    da: float
    conveyance_allowance: float
    medical_allowance: float
    special_allowance: float
    performance_bonus: float
    overtime_pay: float
    incentives: float
    other_earnings: float
    gross_salary: float
    
    epf_employee: float
    esi_employee: float
    professional_tax: float
    tds: float
    loan_advance_deduction: float
    unpaid_leave_deduction: float
    late_penalty_deduction: float
    other_deductions: float
    total_deductions: float
    
    epf_employer: float
    esi_employer: float
    net_salary: float
    payment_status: str
    payment_method: str
    transaction_ref: Optional[str] = None
    remarks: Optional[str] = None
    breakdown_json: Optional[str] = "{}"
    payslip_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class PayrollOut(BaseModel):
    id: int
    payroll_code: str
    month: int
    year: int
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    total_employees: int
    total_gross_pay: float
    total_deductions: float
    total_net_pay: float
    total_employer_pf: float
    total_employer_esi: float
    status: str
    generated_by_user_id: Optional[int] = None
    generated_by_name: Optional[str] = None
    approved_by_user_id: Optional[int] = None
    approved_by_name: Optional[str] = None
    paid_date: Optional[date] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: Optional[List[PayrollItemOut]] = []
    
    class Config:
        from_attributes = True


# ----------------- Audit Log -----------------
class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    action: str
    module: str
    record_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ----------------- Dashboard Summary -----------------
class DashboardStats(BaseModel):
    total_employees: int
    active_employees: int
    inactive_employees: int
    total_departments: int
    current_month_payroll_expense: float
    pending_payroll_count: int
    paid_payroll_count: int
    total_bonuses_distributed: float
    total_deductions_collected: float
    monthly_expense_chart: List[Dict[str, Any]]
    department_expense_chart: List[Dict[str, Any]]
    department_employee_chart: List[Dict[str, Any]]
    payroll_status_breakdown: List[Dict[str, Any]]
    recent_audit_logs: List[AuditLogOut]
