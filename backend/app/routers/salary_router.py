import json
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    SalaryStructure, SalaryComponent, Employee, SalaryHistory, User
)
from app.schemas import (
    SalaryStructureOut, SalaryStructureCreate, SalaryStructureUpdate,
    SalaryComponentOut, SalaryComponentCreate, SalaryHistoryOut
)
from app.auth import get_current_user, require_hr_or_admin
from app.services.audit_service import log_activity

router = APIRouter(prefix="/salary", tags=["Salary Structures & History"])

@router.get("/structures", response_model=List[SalaryStructureOut])
def list_structures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SalaryStructure).order_by(SalaryStructure.name.asc()).all()

@router.post("/structures", response_model=SalaryStructureOut)
def create_structure(
    req: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    if db.query(SalaryStructure).filter(SalaryStructure.code == req.code).first():
        raise HTTPException(status_code=400, detail="Salary structure code already exists")
        
    struct = SalaryStructure(
        code=req.code.upper(),
        name=req.name,
        description=req.description,
        is_active=req.is_active
    )
    db.add(struct)
    db.flush()
    
    if req.components:
        for c in req.components:
            comp = SalaryComponent(
                structure_id=struct.id,
                name=c.name,
                code=c.code.upper(),
                component_type=c.component_type,
                calculation_type=c.calculation_type,
                default_value=c.default_value,
                is_taxable=c.is_taxable,
                is_statutory=c.is_statutory,
                is_active=c.is_active
            )
            db.add(comp)
            
    db.commit()
    db.refresh(struct)
    log_activity(db, action="SALARY_STRUCTURE_CREATED", module="SALARY", user=current_user, record_id=str(struct.id), details=f"Created salary structure {struct.name}")
    return struct

@router.put("/structures/{struct_id}", response_model=SalaryStructureOut)
def update_structure(
    struct_id: int,
    req: SalaryStructureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    struct = db.query(SalaryStructure).filter(SalaryStructure.id == struct_id).first()
    if not struct:
        raise HTTPException(status_code=404, detail="Salary structure not found")
        
    if req.code:
        struct.code = req.code.upper()
    if req.name:
        struct.name = req.name
    if req.description is not None:
        struct.description = req.description
    if req.is_active is not None:
        struct.is_active = req.is_active
        
    db.commit()
    db.refresh(struct)
    log_activity(db, action="SALARY_STRUCTURE_UPDATED", module="SALARY", user=current_user, record_id=str(struct.id), details=f"Updated salary structure {struct.name}")
    return struct

@router.post("/structures/{struct_id}/components", response_model=SalaryComponentOut)
def add_component(
    struct_id: int,
    req: SalaryComponentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    struct = db.query(SalaryStructure).filter(SalaryStructure.id == struct_id).first()
    if not struct:
        raise HTTPException(status_code=404, detail="Salary structure not found")
        
    comp = SalaryComponent(
        structure_id=struct.id,
        name=req.name,
        code=req.code.upper(),
        component_type=req.component_type,
        calculation_type=req.calculation_type,
        default_value=req.default_value,
        is_taxable=req.is_taxable,
        is_statutory=req.is_statutory,
        is_active=req.is_active
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp

@router.delete("/components/{comp_id}")
def delete_component(
    comp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_or_admin)
):
    comp = db.query(SalaryComponent).filter(SalaryComponent.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")
    db.delete(comp)
    db.commit()
    return {"message": "Component deleted successfully"}

@router.get("/history/{employee_id}", response_model=List[SalaryHistoryOut])
def get_employee_salary_history(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If employee role, ensure can only view own history
    if current_user.role == "employee":
        if not current_user.employee_id or current_user.employee_id != employee_id:
            raise HTTPException(status_code=403, detail="Access denied to other employee salary history")
            
    histories = db.query(SalaryHistory).filter(SalaryHistory.employee_id == employee_id).order_by(SalaryHistory.id.desc()).all()
    results = []
    for h in histories:
        out = SalaryHistoryOut.from_orm(h)
        out.changed_by_name = h.changed_by.full_name if h.changed_by else "System"
        results.append(out)
    return results
