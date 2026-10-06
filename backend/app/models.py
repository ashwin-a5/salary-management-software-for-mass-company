import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="employee", nullable=False) # admin, hr, employee
    is_active = Column(Boolean, default=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="user_account")
    audit_logs = relationship("AuditLog", back_populates="user")


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(150), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    manager_name = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    designations = relationship("Designation", back_populates="department", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="department")


class Designation(Base):
    __tablename__ = "designations"
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    min_salary = Column(Float, default=0.0)
    max_salary = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    department = relationship("Department", back_populates="designations")
    employees = relationship("Employee", back_populates="designation")


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    components = relationship("SalaryComponent", back_populates="structure", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="salary_structure")


class SalaryComponent(Base):
    __tablename__ = "salary_components"
    
    id = Column(Integer, primary_key=True, index=True)
    structure_id = Column(Integer, ForeignKey("salary_structures.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False)
    component_type = Column(String(20), nullable=False) # earning, deduction
    calculation_type = Column(String(30), nullable=False) # fixed, percentage_of_basic, percentage_of_gross
    default_value = Column(Float, default=0.0)
    is_taxable = Column(Boolean, default=True)
    is_statutory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    structure = relationship("SalaryStructure", back_populates="components")


class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), default="other")
    profile_photo_url = Column(String(500), nullable=True)
    
    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India")
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    
    # Job Information
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    designation_id = Column(Integer, ForeignKey("designations.id", ondelete="SET NULL"), nullable=True)
    employment_type = Column(String(50), default="full_time") # full_time, part_time, contract, intern
    date_of_joining = Column(Date, nullable=False)
    reporting_manager_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="active") # active, inactive, on_leave, terminated
    
    # Financial & Statutory
    bank_name = Column(String(150), nullable=True)
    bank_account_no = Column(String(100), nullable=True)
    bank_ifsc = Column(String(50), nullable=True)
    bank_branch = Column(String(150), nullable=True)
    pan_number = Column(String(50), nullable=True)
    uan_number = Column(String(50), nullable=True)
    epf_number = Column(String(50), nullable=True)
    esi_number = Column(String(50), nullable=True)
    payment_mode = Column(String(50), default="bank_transfer") # bank_transfer, cheque, cash
    
    # Salary Details
    basic_salary = Column(Float, default=0.0, nullable=False)
    salary_structure_id = Column(Integer, ForeignKey("salary_structures.id", ondelete="SET NULL"), nullable=True)
    hra = Column(Float, default=0.0)
    da = Column(Float, default=0.0)
    conveyance_allowance = Column(Float, default=0.0)
    medical_allowance = Column(Float, default=0.0)
    special_allowance = Column(Float, default=0.0)
    performance_bonus = Column(Float, default=0.0)
    overtime_rate_per_hour = Column(Float, default=0.0)
    epf_enabled = Column(Boolean, default=True)
    esi_enabled = Column(Boolean, default=False)
    professional_tax = Column(Float, default=200.0)
    tds_amount = Column(Float, default=0.0)
    custom_allowances_json = Column(Text, default="{}")
    custom_deductions_json = Column(Text, default="{}")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    designation = relationship("Designation", back_populates="employees")
    salary_structure = relationship("SalaryStructure", back_populates="employees")
    reporting_manager = relationship("Employee", remote_side=[id], foreign_keys=[reporting_manager_id])
    user_account = relationship("User", foreign_keys="User.employee_id", back_populates="employee", uselist=False)
    
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")
    bonuses = relationship("Bonus", back_populates="employee", cascade="all, delete-orphan")
    deductions = relationship("Deduction", back_populates="employee", cascade="all, delete-orphan")
    salary_histories = relationship("SalaryHistory", back_populates="employee", cascade="all, delete-orphan")
    payroll_items = relationship("PayrollItem", back_populates="employee")
    payslips = relationship("Payslip", back_populates="employee")


class SalaryHistory(Base):
    __tablename__ = "salary_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    previous_salary = Column(Float, nullable=False)
    new_salary = Column(Float, nullable=False)
    previous_structure_details = Column(Text, nullable=True) # JSON snapshot
    new_structure_details = Column(Text, nullable=True) # JSON snapshot
    effective_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    employee = relationship("Employee", back_populates="salary_histories")
    changed_by = relationship("User")


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(30), nullable=False) # present, absent, half_day, paid_leave, unpaid_leave, holiday, week_off
    clock_in = Column(String(20), nullable=True)
    clock_out = Column(String(20), nullable=True)
    overtime_hours = Column(Float, default=0.0)
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    employee = relationship("Employee", back_populates="attendances")


class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(String(50), nullable=False) # paid, unpaid, sick, casual, maternity, emergency
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), default="pending") # pending, approved, rejected
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    employee = relationship("Employee", back_populates="leaves")
    approved_by = relationship("User")


class Bonus(Base):
    __tablename__ = "bonuses"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    bonus_type = Column(String(50), default="performance") # performance, festival, incentive, referral, spot_award, other
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False) # 1-12
    year = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    is_taxable = Column(Boolean, default=True)
    status = Column(String(30), default="approved") # pending, approved, paid, cancelled
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    employee = relationship("Employee", back_populates="bonuses")
    created_by = relationship("User")


class Deduction(Base):
    __tablename__ = "deductions"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    deduction_type = Column(String(50), default="other") # loan_advance, leave_deduction, late_penalty, disciplinary, insurance, other
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False) # 1-12
    year = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(30), default="approved") # pending, approved, applied, cancelled
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    employee = relationship("Employee", back_populates="deductions")
    created_by = relationship("User")


class Payroll(Base):
    __tablename__ = "payrolls"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_code = Column(String(50), unique=True, index=True, nullable=False)
    month = Column(Integer, nullable=False) # 1-12
    year = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    total_employees = Column(Integer, default=0)
    total_gross_pay = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    total_net_pay = Column(Float, default=0.0)
    total_employer_pf = Column(Float, default=0.0)
    total_employer_esi = Column(Float, default=0.0)
    
    status = Column(String(30), default="draft") # draft, processing, approved, paid, cancelled
    generated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    paid_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    department = relationship("Department")
    generated_by = relationship("User", foreign_keys=[generated_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    items = relationship("PayrollItem", back_populates="payroll", cascade="all, delete-orphan")


class PayrollItem(Base):
    __tablename__ = "payroll_items"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot Info
    employee_code = Column(String(50), nullable=False)
    employee_name = Column(String(200), nullable=False)
    department_name = Column(String(150), nullable=True)
    designation_name = Column(String(150), nullable=True)
    bank_account_no = Column(String(100), nullable=True)
    bank_name = Column(String(150), nullable=True)
    pan_number = Column(String(50), nullable=True)
    
    # Attendance summary
    total_working_days = Column(Float, default=30.0)
    present_days = Column(Float, default=0.0)
    absent_days = Column(Float, default=0.0)
    half_days = Column(Float, default=0.0)
    paid_leave_days = Column(Float, default=0.0)
    unpaid_leave_days = Column(Float, default=0.0)
    holidays = Column(Float, default=0.0)
    week_offs = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    
    # Earnings breakdown
    basic_salary = Column(Float, default=0.0)
    hra = Column(Float, default=0.0)
    da = Column(Float, default=0.0)
    conveyance_allowance = Column(Float, default=0.0)
    medical_allowance = Column(Float, default=0.0)
    special_allowance = Column(Float, default=0.0)
    performance_bonus = Column(Float, default=0.0)
    overtime_pay = Column(Float, default=0.0)
    incentives = Column(Float, default=0.0)
    other_earnings = Column(Float, default=0.0)
    gross_salary = Column(Float, default=0.0)
    
    # Deductions breakdown
    epf_employee = Column(Float, default=0.0)
    esi_employee = Column(Float, default=0.0)
    professional_tax = Column(Float, default=0.0)
    tds = Column(Float, default=0.0)
    loan_advance_deduction = Column(Float, default=0.0)
    unpaid_leave_deduction = Column(Float, default=0.0)
    late_penalty_deduction = Column(Float, default=0.0)
    other_deductions = Column(Float, default=0.0)
    total_deductions = Column(Float, default=0.0)
    
    # Employer contributions
    epf_employer = Column(Float, default=0.0)
    esi_employer = Column(Float, default=0.0)
    
    # Final amounts
    net_salary = Column(Float, default=0.0)
    payment_status = Column(String(30), default="pending") # pending, paid, cancelled
    payment_method = Column(String(50), default="bank_transfer")
    transaction_ref = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    breakdown_json = Column(Text, default="{}") # Full calculations trace & breakdown
    
    payroll = relationship("Payroll", back_populates="items")
    employee = relationship("Employee", back_populates="payroll_items")
    payslip = relationship("Payslip", back_populates="payroll_item", uselist=False, cascade="all, delete-orphan")


class Payslip(Base):
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_item_id = Column(Integer, ForeignKey("payroll_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    payslip_number = Column(String(100), unique=True, index=True, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    payroll_item = relationship("PayrollItem", back_populates="payslip")
    employee = relationship("Employee", back_populates="payslips")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False) # e.g., EMPLOYEE_CREATED, PAYROLL_APPROVED, LOGIN
    module = Column(String(100), nullable=False) # e.g., AUTH, EMPLOYEE, PAYROLL, SALARY
    record_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")
