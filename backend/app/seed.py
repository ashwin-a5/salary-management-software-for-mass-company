import json
import calendar
from datetime import date, datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import (
    User, Department, Designation, SalaryStructure, SalaryComponent,
    Employee, SalaryHistory, Attendance, Leave, Bonus, Deduction,
    Payroll, PayrollItem, Payslip, AuditLog
)
from app.auth import get_password_hash
from app.services.payroll_service import generate_monthly_payroll

def seed_database():
    print("Creating tables in database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(User).filter(User.username == "admin").first():
        print("Database already contains seed data.")
        db.close()
        return

    print("Seeding initial company data...")
    
    # 1. Create Core Users
    admin_user = User(
        username="admin",
        email="admin@apextechglobal.com",
        hashed_password=get_password_hash("Admin@123"),
        full_name="Alexander Vance (Admin)",
        role="admin",
        is_active=True
    )
    db.add(admin_user)
    
    hr_user = User(
        username="hr_sarah",
        email="sarah.jenkins@apextechglobal.com",
        hashed_password=get_password_hash("Hr@123"),
        full_name="Sarah Jenkins (HR Manager)",
        role="hr",
        is_active=True
    )
    db.add(hr_user)
    db.commit()
    
    # 2. Create Departments
    departments_data = [
        {"code": "ENG", "name": "Engineering & Technology", "description": "Core software development, architecture, cloud and DevOps infrastructure.", "manager_name": "Marcus Sterling"},
        {"code": "HR", "name": "Human Resources & Talent", "description": "People operations, talent acquisition, payroll, and organizational development.", "manager_name": "Sarah Jenkins"},
        {"code": "SALES", "name": "Sales & Business Development", "description": "Enterprise sales, client relations, growth and revenue generation.", "manager_name": "David Miller"},
        {"code": "FIN", "name": "Finance & Accounts", "description": "Financial planning, accounting, compliance, treasury and tax operations.", "manager_name": "Elena Rostova"},
        {"code": "PROD", "name": "Product & Design", "description": "Product strategy, UI/UX design, customer journey and user research.", "manager_name": "Priya Sharma"},
        {"code": "OPS", "name": "Global Operations", "description": "Daily enterprise operations, procurement, IT support and facility management.", "manager_name": "Michael Chen"}
    ]
    
    dept_objs = {}
    for d_data in departments_data:
        dep = Department(**d_data)
        db.add(dep)
        db.flush()
        dept_objs[dep.code] = dep
        
    db.commit()
    
    # 3. Create Designations
    designations_data = [
        {"dept_code": "ENG", "title": "Principal Software Architect", "min_salary": 140000, "max_salary": 220000, "description": "System architecture and technical leadership"},
        {"dept_code": "ENG", "title": "Senior Full-Stack Engineer", "min_salary": 85000, "max_salary": 140000, "description": "Full-stack feature engineering & backend services"},
        {"dept_code": "ENG", "title": "DevOps & Cloud Engineer", "min_salary": 75000, "max_salary": 130000, "description": "CI/CD pipelines, Kubernetes, AWS infrastructure"},
        {"dept_code": "ENG", "title": "QA Automation Lead", "min_salary": 65000, "max_salary": 110000, "description": "Test automation architecture & quality assurance"},
        {"dept_code": "HR", "title": "Senior HR Business Partner", "min_salary": 60000, "max_salary": 105000, "description": "HR policy, employee relations and performance management"},
        {"dept_code": "SALES", "title": "Enterprise Sales Director", "min_salary": 95000, "max_salary": 180000, "description": "Enterprise SaaS deal closure and partnership growth"},
        {"dept_code": "FIN", "title": "Senior Financial Analyst", "min_salary": 70000, "max_salary": 120000, "description": "Financial modeling, budgeting and tax compliance"},
        {"dept_code": "PROD", "title": "Lead Product Designer (UI/UX)", "min_salary": 80000, "max_salary": 135000, "description": "Design systems, usability research and UI UX flows"}
    ]
    
    desig_objs = {}
    for des_data in designations_data:
        dept = dept_objs[des_data["dept_code"]]
        des = Designation(
            department_id=dept.id,
            title=des_data["title"],
            description=des_data["description"],
            min_salary=des_data["min_salary"],
            max_salary=des_data["max_salary"]
        )
        db.add(des)
        db.flush()
        desig_objs[des.title] = des
        
    db.commit()
    
    # 4. Salary Structures
    struct1 = SalaryStructure(
        code="CORP-TECH-A",
        name="Corporate Technical Grade A",
        description="Comprehensive structure for Senior Tech, Architects, and Leads with PF & HRA allowances",
        is_active=True
    )
    struct2 = SalaryStructure(
        code="CORP-EXEC-B",
        name="Corporate Executive Grade B",
        description="Standard structure for Business, HR, and Operations roles",
        is_active=True
    )
    db.add(struct1)
    db.add(struct2)
    db.flush()
    
    components = [
        {"struct": struct1, "name": "Basic Salary", "code": "BASIC", "component_type": "earning", "calculation_type": "fixed", "default_value": 50000, "is_taxable": True, "is_statutory": True},
        {"struct": struct1, "name": "House Rent Allowance", "code": "HRA", "component_type": "earning", "calculation_type": "percentage_of_basic", "default_value": 40.0, "is_taxable": True, "is_statutory": False},
        {"struct": struct1, "name": "Dearness Allowance", "code": "DA", "component_type": "earning", "calculation_type": "percentage_of_basic", "default_value": 10.0, "is_taxable": True, "is_statutory": False},
        {"struct": struct1, "name": "Conveyance Allowance", "code": "CONVEY", "component_type": "earning", "calculation_type": "fixed", "default_value": 1600.0, "is_taxable": False, "is_statutory": False},
        {"struct": struct1, "name": "Medical Allowance", "code": "MED", "component_type": "earning", "calculation_type": "fixed", "default_value": 1250.0, "is_taxable": False, "is_statutory": False},
        {"struct": struct1, "name": "Special Allowance", "code": "SPECIAL", "component_type": "earning", "calculation_type": "fixed", "default_value": 15000.0, "is_taxable": True, "is_statutory": False},
        {"struct": struct1, "name": "Provident Fund (EPF)", "code": "EPF", "component_type": "deduction", "calculation_type": "percentage_of_basic", "default_value": 12.0, "is_taxable": False, "is_statutory": True},
        {"struct": struct1, "name": "Professional Tax", "code": "PTAX", "component_type": "deduction", "calculation_type": "fixed", "default_value": 200.0, "is_taxable": False, "is_statutory": True}
    ]
    for c in components:
        comp = SalaryComponent(
            structure_id=c["struct"].id,
            name=c["name"],
            code=c["code"],
            component_type=c["component_type"],
            calculation_type=c["calculation_type"],
            default_value=c["default_value"],
            is_taxable=c["is_taxable"],
            is_statutory=c["is_statutory"]
        )
        db.add(comp)
    db.commit()
    
    # 5. Employees Data
    employees_data = [
        {
            "code": "EMP-1001",
            "first_name": "Marcus",
            "last_name": "Sterling",
            "email": "marcus.sterling@apextechglobal.com",
            "phone": "+91 98450 11223",
            "dob": date(1987, 4, 15),
            "gender": "male",
            "dept": "ENG",
            "desig": "Principal Software Architect",
            "joining": date(2021, 3, 1),
            "basic": 110000.0,
            "hra": 44000.0,
            "da": 11000.0,
            "conveyance": 3000.0,
            "medical": 2500.0,
            "special": 18000.0,
            "perf_bonus": 10000.0,
            "ot_rate": 850.0,
            "tds": 14500.0,
            "bank_name": "HDFC Bank",
            "bank_acc": "50100239481923",
            "ifsc": "HDFC0000240",
            "pan": "ABCPS8291K",
            "uan": "100928374612",
            "city": "Bengaluru",
            "role": "employee",
            "struct_id": struct1.id
        },
        {
            "code": "EMP-1002",
            "first_name": "Aarav",
            "last_name": "Patel",
            "email": "aarav.patel@apextechglobal.com",
            "phone": "+91 97123 45678",
            "dob": date(1992, 8, 22),
            "gender": "male",
            "dept": "ENG",
            "desig": "Senior Full-Stack Engineer",
            "joining": date(2022, 5, 10),
            "basic": 75000.0,
            "hra": 30000.0,
            "da": 7500.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 12000.0,
            "perf_bonus": 5000.0,
            "ot_rate": 600.0,
            "tds": 7800.0,
            "bank_name": "ICICI Bank",
            "bank_acc": "002901592834",
            "ifsc": "ICIC0000029",
            "pan": "BPMPA4810M",
            "uan": "100938472911",
            "city": "Bengaluru",
            "role": "employee",
            "struct_id": struct1.id
        },
        {
            "code": "EMP-1003",
            "first_name": "Sarah",
            "last_name": "Jenkins",
            "email": "sarah.jenkins@apextechglobal.com",
            "phone": "+91 99001 88223",
            "dob": date(1989, 11, 5),
            "gender": "female",
            "dept": "HR",
            "desig": "Senior HR Business Partner",
            "joining": date(2021, 6, 15),
            "basic": 68000.0,
            "hra": 27200.0,
            "da": 6800.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 10000.0,
            "perf_bonus": 4000.0,
            "ot_rate": 500.0,
            "tds": 6200.0,
            "bank_name": "State Bank of India",
            "bank_acc": "38291048291",
            "ifsc": "SBIN0001823",
            "pan": "CPXPS9182L",
            "uan": "100847291038",
            "city": "Bengaluru",
            "role": "hr",
            "struct_id": struct2.id
        },
        {
            "code": "EMP-1004",
            "first_name": "David",
            "last_name": "Miller",
            "email": "david.miller@apextechglobal.com",
            "phone": "+91 98860 99112",
            "dob": date(1985, 2, 18),
            "gender": "male",
            "dept": "SALES",
            "desig": "Enterprise Sales Director",
            "joining": date(2021, 1, 10),
            "basic": 95000.0,
            "hra": 38000.0,
            "da": 9500.0,
            "conveyance": 3000.0,
            "medical": 2000.0,
            "special": 22000.0,
            "perf_bonus": 15000.0,
            "ot_rate": 750.0,
            "tds": 12500.0,
            "bank_name": "Axis Bank",
            "bank_acc": "91802004829102",
            "ifsc": "UTIB0000482",
            "pan": "DMMPM1092P",
            "uan": "100728192039",
            "city": "Mumbai",
            "role": "employee",
            "struct_id": struct2.id
        },
        {
            "code": "EMP-1005",
            "first_name": "Elena",
            "last_name": "Rostova",
            "email": "elena.rostova@apextechglobal.com",
            "phone": "+91 97410 33445",
            "dob": date(1991, 7, 30),
            "gender": "female",
            "dept": "FIN",
            "desig": "Senior Financial Analyst",
            "joining": date(2022, 2, 1),
            "basic": 72000.0,
            "hra": 28800.0,
            "da": 7200.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 11000.0,
            "perf_bonus": 4500.0,
            "ot_rate": 550.0,
            "tds": 6900.0,
            "bank_name": "Kotak Mahindra Bank",
            "bank_acc": "6810293847",
            "ifsc": "KKBK0000582",
            "pan": "ERMPR8372Q",
            "uan": "100619283746",
            "city": "Bengaluru",
            "role": "employee",
            "struct_id": struct2.id
        },
        {
            "code": "EMP-1006",
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "priya.sharma@apextechglobal.com",
            "phone": "+91 96200 44556",
            "dob": date(1993, 12, 14),
            "gender": "female",
            "dept": "PROD",
            "desig": "Lead Product Designer (UI/UX)",
            "joining": date(2022, 8, 1),
            "basic": 78000.0,
            "hra": 31200.0,
            "da": 7800.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 13000.0,
            "perf_bonus": 6000.0,
            "ot_rate": 600.0,
            "tds": 8200.0,
            "bank_name": "HDFC Bank",
            "bank_acc": "50100482910394",
            "ifsc": "HDFC0000240",
            "pan": "PSMPS4829R",
            "uan": "100529384710",
            "city": "Bengaluru",
            "role": "employee",
            "struct_id": struct1.id
        },
        {
            "code": "EMP-1007",
            "first_name": "Vikram",
            "last_name": "Rao",
            "email": "vikram.rao@apextechglobal.com",
            "phone": "+91 98455 66778",
            "dob": date(1994, 3, 19),
            "gender": "male",
            "dept": "ENG",
            "desig": "DevOps & Cloud Engineer",
            "joining": date(2023, 1, 16),
            "basic": 65000.0,
            "hra": 26000.0,
            "da": 6500.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 9500.0,
            "perf_bonus": 3500.0,
            "ot_rate": 500.0,
            "tds": 5400.0,
            "bank_name": "ICICI Bank",
            "bank_acc": "002901928374",
            "ifsc": "ICIC0000029",
            "pan": "VRMPR7192S",
            "uan": "100418273645",
            "city": "Hyderabad",
            "role": "employee",
            "struct_id": struct1.id
        },
        {
            "code": "EMP-1008",
            "first_name": "Neha",
            "last_name": "Gupta",
            "email": "neha.gupta@apextechglobal.com",
            "phone": "+91 97310 88990",
            "dob": date(1995, 9, 8),
            "gender": "female",
            "dept": "ENG",
            "desig": "QA Automation Lead",
            "joining": date(2023, 4, 3),
            "basic": 60000.0,
            "hra": 24000.0,
            "da": 6000.0,
            "conveyance": 2000.0,
            "medical": 1500.0,
            "special": 8500.0,
            "perf_bonus": 3000.0,
            "ot_rate": 450.0,
            "tds": 4800.0,
            "bank_name": "State Bank of India",
            "bank_acc": "39102938475",
            "ifsc": "SBIN0001823",
            "pan": "NGMPG6281T",
            "uan": "100319284756",
            "city": "Bengaluru",
            "role": "employee",
            "struct_id": struct1.id
        }
    ]
    
    created_employees = []
    for ed in employees_data:
        dept = dept_objs[ed["dept"]]
        desig = desig_objs[ed["desig"]]
        
        emp = Employee(
            employee_code=ed["code"],
            first_name=ed["first_name"],
            last_name=ed["last_name"],
            email=ed["email"],
            phone=ed["phone"],
            date_of_birth=ed["dob"],
            gender=ed["gender"],
            address=f"Flat {ed['code'][-3:]}, Prestige Residency, Silicon Park",
            city=ed["city"],
            state="Karnataka",
            postal_code="560100",
            country="India",
            emergency_contact_name=f"Family of {ed['first_name']}",
            emergency_contact_phone="+91 99887 76655",
            
            department_id=dept.id,
            designation_id=desig.id,
            employment_type="full_time",
            date_of_joining=ed["joining"],
            status="active",
            
            bank_name=ed["bank_name"],
            bank_account_no=ed["bank_acc"],
            bank_ifsc=ed["ifsc"],
            bank_branch="Tech Park Branch",
            pan_number=ed["pan"],
            uan_number=ed["uan"],
            epf_number=f"KN/BLR/{ed['uan'][:6]}/{ed['code'][-4:]}",
            payment_mode="bank_transfer",
            
            basic_salary=ed["basic"],
            salary_structure_id=ed["struct_id"],
            hra=ed["hra"],
            da=ed["da"],
            conveyance_allowance=ed["conveyance"],
            medical_allowance=ed["medical"],
            special_allowance=ed["special"],
            performance_bonus=ed["perf_bonus"],
            overtime_rate_per_hour=ed["ot_rate"],
            epf_enabled=True,
            esi_enabled=False,
            professional_tax=200.0,
            tds_amount=ed["tds"]
        )
        db.add(emp)
        db.flush()
        
        # Link to HR user or create employee login user
        if ed["email"] == "sarah.jenkins@apextechglobal.com":
            hr_user.employee_id = emp.id
            emp.user_id = hr_user.id
        else:
            uname = ed["email"].split("@")[0]
            emp_user = User(
                username=uname,
                email=ed["email"],
                hashed_password=get_password_hash("Employee@123"),
                full_name=f"{ed['first_name']} {ed['last_name']}",
                role="employee",
                is_active=True,
                employee_id=emp.id
            )
            db.add(emp_user)
            db.flush()
            emp.user_id = emp_user.id
            
        # Initial salary history record
        snapshot = {
            "basic_salary": ed["basic"],
            "hra": ed["hra"],
            "da": ed["da"],
            "conveyance": ed["conveyance"],
            "medical": ed["medical"],
            "special": ed["special"],
            "ptax": 200.0,
            "tds": ed["tds"]
        }
        hist = SalaryHistory(
            employee_id=emp.id,
            previous_salary=0.0,
            new_salary=ed["basic"],
            previous_structure_details="Initial Offer Structure",
            new_structure_details=json.dumps(snapshot),
            effective_date=ed["joining"],
            reason="Initial Joining Offer & Appointment",
            changed_by_user_id=admin_user.id
        )
        db.add(hist)
        created_employees.append(emp)
        
    db.commit()
    
    # 6. Seed Attendance and Leaves for Past 3 Months + Current Month
    today = date.today()
    cur_year = today.year
    cur_month = today.month
    
    # Months to generate: 3 previous months and current month
    past_months = []
    for offset in range(3, -1, -1):
        m = cur_month - offset
        y = cur_year
        if m <= 0:
            m += 12
            y -= 1
        past_months.append((y, m))
        
    for y, m in past_months:
        num_days = calendar.monthrange(y, m)[1]
        # For each employee, generate daily logs
        for idx, emp in enumerate(created_employees):
            # Give slight variety
            for day in range(1, num_days + 1):
                cur_date = date(y, m, day)
                weekday = cur_date.weekday() # 5=Sat, 6=Sun
                
                if weekday == 6: # Sunday
                    st = "week_off"
                    cin, cout = None, None
                    ot = 0.0
                elif weekday == 5 and day % 2 == 0: # Alternate Saturday off
                    st = "week_off"
                    cin, cout = None, None
                    ot = 0.0
                elif day == 15 and idx % 3 == 0:
                    st = "paid_leave"
                    cin, cout = None, None
                    ot = 0.0
                elif day == 22 and idx == 1:
                    st = "unpaid_leave"
                    cin, cout = None, None
                    ot = 0.0
                elif day == 10 and idx == 4:
                    st = "half_day"
                    cin, cout = "09:30", "13:30"
                    ot = 0.0
                else:
                    st = "present"
                    cin, cout = "09:15", "18:30"
                    ot = 2.0 if (day % 7 == 0 and idx % 2 == 0) else 0.0
                    
                att = Attendance(
                    employee_id=emp.id,
                    date=cur_date,
                    status=st,
                    clock_in=cin,
                    clock_out=cout,
                    overtime_hours=ot
                )
                db.add(att)
                
    db.commit()
    
    # 7. Add sample Bonuses & Deductions
    bonus1 = Bonus(
        employee_id=created_employees[1].id, # Aarav
        title="Q3 Innovation Award",
        bonus_type="spot_award",
        amount=15000.0,
        month=past_months[1][1],
        year=past_months[1][0],
        reason="Excellence in leading Kubernetes cloud migration with zero downtime.",
        status="approved",
        created_by_user_id=admin_user.id
    )
    db.add(bonus1)
    
    ded1 = Deduction(
        employee_id=created_employees[0].id, # Marcus
        title="Festival Laptop Loan Installment",
        deduction_type="loan_advance",
        amount=5000.0,
        month=past_months[1][1],
        year=past_months[1][0],
        reason="Monthly corporate tech equipment purchase repayment (1/4)",
        status="approved",
        created_by_user_id=hr_user.id
    )
    db.add(ded1)
    db.commit()
    
    # 8. Generate and Approve/Pay past payrolls
    for y, m in past_months[:-1]:
        payroll, _ = generate_monthly_payroll(db, month=m, year=y, user_id=admin_user.id)
        payroll.status = "paid"
        payroll.paid_date = date(y, m, calendar.monthrange(y, m)[1])
        payroll.approved_by_user_id = admin_user.id
        for itm in payroll.items:
            itm.payment_status = "paid"
        db.commit()
        
    # Current month payroll as 'draft' or 'approved'
    cur_y, cur_m = past_months[-1]
    cur_payroll, _ = generate_monthly_payroll(db, month=cur_m, year=cur_y, user_id=hr_user.id)
    cur_payroll.status = "approved"
    cur_payroll.approved_by_user_id = admin_user.id
    db.commit()
    
    # 9. Audit Logs
    log1 = AuditLog(
        user_id=admin_user.id,
        user_email=admin_user.email,
        role="admin",
        action="SYSTEM_INITIALIZATION",
        module="SYSTEM",
        details="System successfully seeded with core enterprise structure, employees, and historical payroll runs."
    )
    db.add(log1)
    db.commit()
    db.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
