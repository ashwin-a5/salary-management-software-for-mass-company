from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Department, Designation, Employee, User
from app.schemas import DepartmentOut, DepartmentCreate, DepartmentUpdate
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deps = db.query(Department).order_by(Department.name.asc()).all()
    results = []
    for d in deps:
        count = db.query(Employee).filter(Employee.department_id == d.id).count()
        out = DepartmentOut.from_orm(d)
        out.employee_count = count
        results.append(out)
    return results

@router.post("", response_model=DepartmentOut)
def create_department(
    req: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    if db.query(Department).filter(Department.name == req.name).first():
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    if db.query(Department).filter(Department.code == req.code).first():
        raise HTTPException(status_code=400, detail="Department code already exists")
        
    dep = Department(
        code=req.code.upper(),
        name=req.name,
        description=req.description,
        manager_name=req.manager_name
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    
    log_activity(db, action="DEPARTMENT_CREATED", module="DEPARTMENT", user=current_user, record_id=str(dep.id), details=f"Created department {dep.name}")
    out = DepartmentOut.from_orm(dep)
    out.employee_count = 0
    return out

@router.put("/{dep_id}", response_model=DepartmentOut)
def update_department(
    dep_id: int,
    req: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    dep = db.query(Department).filter(Department.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
        
    if req.code:
        dep.code = req.code.upper()
    if req.name:
        dep.name = req.name
    if req.description is not None:
        dep.description = req.description
    if req.manager_name is not None:
        dep.manager_name = req.manager_name
        
    db.commit()
    db.refresh(dep)
    log_activity(db, action="DEPARTMENT_UPDATED", module="DEPARTMENT", user=current_user, record_id=str(dep.id), details=f"Updated department {dep.name}")
    count = db.query(Employee).filter(Employee.department_id == dep.id).count()
    out = DepartmentOut.from_orm(dep)
    out.employee_count = count
    return out

@router.delete("/{dep_id}")
def delete_department(
    dep_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    dep = db.query(Department).filter(Department.id == dep_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
        
    name = dep.name
    db.delete(dep)
    db.commit()
    log_activity(db, action="DEPARTMENT_DELETED", module="DEPARTMENT", user=current_user, record_id=str(dep_id), details=f"Deleted department {name}")
    return {"message": "Department deleted successfully"}
