from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Designation, Department, User
from app.schemas import DesignationOut, DesignationCreate, DesignationUpdate
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/designations", tags=["Designations"])

@router.get("", response_model=List[DesignationOut])
def list_designations(
    department_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Designation)
    if department_id:
        query = query.filter(Designation.department_id == department_id)
    designations = query.order_by(Designation.title.asc()).all()
    results = []
    for d in designations:
        out = DesignationOut.from_orm(d)
        out.department_name = d.department.name if d.department else None
        results.append(out)
    return results

@router.post("", response_model=DesignationOut)
def create_designation(
    req: DesignationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    dep = db.query(Department).filter(Department.id == req.department_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Department not found")
        
    des = Designation(
        department_id=req.department_id,
        title=req.title,
        description=req.description,
        min_salary=req.min_salary,
        max_salary=req.max_salary
    )
    db.add(des)
    db.commit()
    db.refresh(des)
    
    log_activity(db, action="DESIGNATION_CREATED", module="DESIGNATION", user=current_user, record_id=str(des.id), details=f"Created designation {des.title} in {dep.name}")
    out = DesignationOut.from_orm(des)
    out.department_name = dep.name
    return out

@router.put("/{des_id}", response_model=DesignationOut)
def update_designation(
    des_id: int,
    req: DesignationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    des = db.query(Designation).filter(Designation.id == des_id).first()
    if not des:
        raise HTTPException(status_code=404, detail="Designation not found")
        
    if req.department_id:
        dep = db.query(Department).filter(Department.id == req.department_id).first()
        if not dep:
            raise HTTPException(status_code=404, detail="Department not found")
        des.department_id = req.department_id
        
    if req.title:
        des.title = req.title
    if req.description is not None:
        des.description = req.description
    if req.min_salary is not None:
        des.min_salary = req.min_salary
    if req.max_salary is not None:
        des.max_salary = req.max_salary
        
    db.commit()
    db.refresh(des)
    log_activity(db, action="DESIGNATION_UPDATED", module="DESIGNATION", user=current_user, record_id=str(des.id), details=f"Updated designation {des.title}")
    out = DesignationOut.from_orm(des)
    out.department_name = des.department.name if des.department else None
    return out

@router.delete("/{des_id}")
def delete_designation(
    des_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    des = db.query(Designation).filter(Designation.id == des_id).first()
    if not des:
        raise HTTPException(status_code=404, detail="Designation not found")
        
    title = des.title
    db.delete(des)
    db.commit()
    log_activity(db, action="DESIGNATION_DELETED", module="DESIGNATION", user=current_user, record_id=str(des_id), details=f"Deleted designation {title}")
    return {"message": "Designation deleted successfully"}
