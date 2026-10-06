# 💼 PayPulse - Enterprise Employee Salary & Payroll Management System

A complete, modern, production-grade **Employee Salary and Payroll Management System** built for real-world enterprise operations. PayPulse provides an end-to-end suite for managing employees, customizable multi-component salary structures, daily and bulk attendance tracking, leave workflows, bonuses and spot awards, automated monthly payroll calculations with statutory deductions (EPF, ESI, Professional Tax, TDS), server-side high-resolution PDF payslip generation, multi-format reporting (Excel, CSV), role-based access control, and complete audit logging.

---

## 🚀 Key Features

### 1. 👥 Multi-Role Access Control (RBAC)
- **Admin**: Full system governance, employee management, salary structures, payroll generation/approval, audit trail analysis, and user account management.
- **HR Manager**: Employee onboarding and directory management, daily/bulk attendance logging, leave approval/rejection, bonus/deduction awards, and monthly payroll processing.
- **Employee**: Personal self-service portal, profile overview, current salary and allowance breakdown, personal attendance matrix, leave requests, and downloadable PDF payslips.

### 2. 🗂️ Employee Management
- Complete profile directory with searchable & filterable table by Name, Employee Code, Department, Designation, and Employment Status.
- Multi-tab Onboarding modal:
  - Personal Information & Emergency Contact
  - Job Position, Department, Designation & Reporting Manager
  - Banking & Statutory Compliance (Bank Name, A/C No, IFSC, PAN, UAN, EPF ID, ESI ID)
  - Customizable Salary Component Setup (Basic, HRA, DA, Conveyance, Medical, Special Allowance, Overtime Hourly Rate, TDS, Professional Tax)
- Employee Profile Drawer showing Overview, Compensation Structure, Revision History Timeline, Attendance Log, and Generated Payslips.
- Instant Active/Inactive status toggle.

### 3. 💰 Flexible Salary Structures & Decimal Precision
- **Earnings**: Basic Salary, House Rent Allowance (HRA), Dearness Allowance (DA), Conveyance Allowance, Medical Allowance, Special Allowance, Performance Bonus, Overtime Pay (1.5x hourly rate), Spot Awards & Incentives.
- **Deductions**: Employee EPF (12%), Employee ESI (0.75%), Professional Tax (PT), Income Tax (TDS), Loss of Pay (LOP) Unpaid Leave Deductions, Loan / Advance Repayments, Late Penalties.
- **Employer Contributions**: Employer EPF Share (12%), Employer ESI Share (3.25%).
- **Immutable Salary History**: Every salary change creates an audited snapshot with effective date, previous vs new salary, and reason.

### 4. ⏱️ Attendance & Leave Management
- Daily time & attendance tracking (`Present`, `Absent`, `Half Day`, `Paid Leave`, `Unpaid Leave`, `Holiday`, `Week Off`).
- **1-Click Bulk Attendance Marker**: Fast-log attendance for the entire company or department.
- **Leave Management**: Employee application workflow with approval / rejection actions.
- Automatic Loss of Pay (LOP) calculation synced with the payroll engine.

### 5. ⚙️ Automated Monthly Payroll Processing
- Select Month, Year, and Department scope.
- Automated payroll calculation preventing duplicate generation for finalized cycles.
- Multi-state payroll batch lifecycle: `Draft` &rarr; `Processing` &rarr; `Approved` &rarr; `Paid` &rarr; `Cancelled`.
- Itemized batch drill-down with real-time gross, statutory deduction, and net take-home computations.

### 6. 📄 Server-Side PDF Payslips & Dual Reporting
- Pixel-perfect ReportLab server-side PDF generator featuring corporate header, company CIN/TAN, employee details, attendance summary, earnings vs deductions grid, net salary in words and figures, and authorized signature section.
- Client-side interactive payslip modal with print formatting.
- Multi-format Reports (Monthly, Annual, Department-wise, and Tax/TDS) with 1-click **Excel (.xlsx)** and **CSV (.csv)** export.

### 7. 🛡️ Security, Encryption & Audit Trails
- JWT (JSON Web Tokens) with 24-hour expiration.
- Native `bcrypt` password hashing.
- Comprehensive security audit log tracking logins, employee edits, payroll status changes, and downloads with user identity and IP tracking.

---

## 🔑 Demo Login Credentials

The system comes pre-populated with realistic company departments, employees, attendance logs, and past payroll records:

| Role | Username / Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` *(or admin@apextechglobal.com)* | `Admin@123` | Full Administrative & User Control |
| **HR Manager** | `hr_sarah` *(or sarah.jenkins@apextechglobal.com)* | `Hr@123` | Employee & Payroll Operations |
| **Employee** | `marcus.sterling` *(or marcus.sterling@apextechglobal.com)* | `Employee@123` | Employee Self-Service & Payslips |

*(Quick-login buttons are also available on the Login screen for instant access.)*

---

## 🏗️ Architecture & Technology Stack

```
├── backend/
│   ├── app/
│   │   ├── config.py           # Application Settings & Defaults
│   │   ├── database.py         # SQLAlchemy Engine & Session
│   │   ├── models.py           # Relational ORM Entities (15+ Tables)
│   │   ├── schemas.py          # Pydantic Request/Response Validation
│   │   ├── auth.py             # JWT Auth, Bcrypt Hashing, RBAC
│   │   ├── seed.py             # Pre-populated Enterprise Demo Data
│   │   ├── main.py             # FastAPI App with CORS & Middleware
│   │   ├── services/
│   │   │   ├── payroll_service.py # Core Financial Calculation Algorithms
│   │   │   ├── pdf_service.py     # ReportLab High-Res PDF Generator
│   │   │   ├── export_service.py  # Pandas & OpenPyXL Excel/CSV Exporter
│   │   │   └── audit_service.py   # Security Activity Audit Logger
│   │   └── routers/            # Clean REST Endpoints
│   │       ├── auth_router.py
│   │       ├── employees_router.py
│   │       ├── payroll_router.py
│   │       ├── payslips_router.py
│   │       ├── attendance_router.py
│   │       ├── leaves_router.py
│   │       ├── salary_router.py
│   │       ├── bonuses_router.py
│   │       ├── deductions_router.py
│   │       ├── reports_router.py
│   │       ├── dashboard_router.py
│   │       ├── departments_router.py
│   │       ├── designations_router.py
│   │       ├── audit_logs_router.py
│   │       └── users_router.py
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── context/AuthContext.tsx  # Global Auth & Role State
    │   ├── services/api.ts          # Axios Client with Interceptors
    │   ├── types/index.ts           # TypeScript Domain Definitions
    │   ├── components/              # Reusable UI Library
    │   │   ├── layout/ (Sidebar, Header, Layout)
    │   │   ├── common/ (Modal, Button, Input, Select, Badge, Card, Tabs)
    │   │   └── payslip/ (PayslipModal)
    │   ├── pages/                   # Application Views
    │   │   ├── Login.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── Employees.tsx
    │   │   ├── EmployeeProfileModal.tsx
    │   │   ├── Attendance.tsx
    │   │   ├── Leaves.tsx
    │   │   ├── Payroll.tsx
    │   │   ├── PayrollDetail.tsx
    │   │   ├── SalaryStructures.tsx
    │   │   ├── BonusesDeductions.tsx
    │   │   ├── Payslips.tsx
    │   │   ├── Reports.tsx
    │   │   ├── Departments.tsx
    │   │   ├── AuditLogs.tsx
    │   │   └── Users.tsx
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.ts
```

---

## ⚡ Quick Start & Execution

### Option A: Using the Launcher Scripts
- On Windows PowerShell:
  ```powershell
  .\start.ps1
  ```
- On Windows Command Prompt:
  ```cmd
  start.bat
  ```

### Option B: Manual Terminal Execution

#### 1. Start the FastAPI Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI / Swagger Docs: `http://127.0.0.1:8000/docs`

#### 2. Start the Vite React Frontend
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 📊 Complete Payroll Workflow Verification

1. **Sign In**: Log in with `admin` / `Admin@123`.
2. **Review Dashboard**: Observe KPI metrics, salary expense area trends, department donut charts, and headcount bars.
3. **Employees**: View directory, click **Add New Employee**, fill in details, set basic salary and check auto-calculated HRA/DA.
4. **Time & Attendance**: Go to **Attendance**, click **Bulk Mark Attendance**, select today's date, preset **All Present**, and save.
5. **Bonuses & Deductions**: Under **Bonuses & Deductions**, grant a spot bonus or record a loan installment.
6. **Run Payroll**: Go to **Run Payroll**, click **Run Monthly Payroll**, select current month/year, and execute the batch calculation.
7. **Approve & Settle**: Click **Breakdown**, verify itemized deductions and gross pay, click **Approve Payroll**, then click **Pay Out**.
8. **Payslip & PDF**: Click **Payslip** on any employee row, inspect the modal, and click **Download PDF** to obtain the official document.
9. **Export Reports**: Open **Payroll Reports**, switch between Monthly/Annual/Tax tabs, and click **Export to Excel (.xlsx)** or **Export to CSV**.
10. **Audit Logs**: Open **Audit Trail** to view all recorded state transitions with timestamps and user references.

---

## 📝 License & Author
Built with modern enterprise practices using FastAPI, React, TypeScript, Tailwind CSS, ReportLab, and SQLite/PostgreSQL.
