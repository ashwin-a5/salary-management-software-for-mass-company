from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.seed import seed_database

# Routers
from app.routers import (
    auth_router,
    users_router,
    departments_router,
    designations_router,
    employees_router,
    salary_router,
    attendance_router,
    leaves_router,
    bonuses_router,
    deductions_router,
    payroll_router,
    payslips_router,
    reports_router,
    audit_logs_router,
    dashboard_router
)

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Salary, Payroll & Attendance Management System API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        seed_database()
    except Exception as e:
        print(f"Seed info/warning: {e}")

# Include routers
api_prefix = settings.API_V1_STR
app.include_router(auth_router.router, prefix=api_prefix)
app.include_router(users_router.router, prefix=api_prefix)
app.include_router(departments_router.router, prefix=api_prefix)
app.include_router(designations_router.router, prefix=api_prefix)
app.include_router(employees_router.router, prefix=api_prefix)
app.include_router(salary_router.router, prefix=api_prefix)
app.include_router(attendance_router.router, prefix=api_prefix)
app.include_router(leaves_router.router, prefix=api_prefix)
app.include_router(bonuses_router.router, prefix=api_prefix)
app.include_router(deductions_router.router, prefix=api_prefix)
app.include_router(payroll_router.router, prefix=api_prefix)
app.include_router(payslips_router.router, prefix=api_prefix)
app.include_router(reports_router.router, prefix=api_prefix)
app.include_router(audit_logs_router.router, prefix=api_prefix)
app.include_router(dashboard_router.router, prefix=api_prefix)

# Also expose under /api for convenient frontend proxy
app.include_router(auth_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(departments_router.router, prefix="/api")
app.include_router(designations_router.router, prefix="/api")
app.include_router(employees_router.router, prefix="/api")
app.include_router(salary_router.router, prefix="/api")
app.include_router(attendance_router.router, prefix="/api")
app.include_router(leaves_router.router, prefix="/api")
app.include_router(bonuses_router.router, prefix="/api")
app.include_router(deductions_router.router, prefix="/api")
app.include_router(payroll_router.router, prefix="/api")
app.include_router(payslips_router.router, prefix="/api")
app.include_router(reports_router.router, prefix="/api")
app.include_router(audit_logs_router.router, prefix="/api")
app.include_router(dashboard_router.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
