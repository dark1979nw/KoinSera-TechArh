from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Employee, User
from routers.auth import get_current_user
from schemas import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from fastapi import HTTPException

router = APIRouter(prefix="/employees", tags=["employees"])

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Employee).filter(Employee.user_id == current_user.user_id).all()

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_employee = Employee(
        full_name=employee.full_name,
        telegram_username=employee.telegram_username,
        telegram_user_id=employee.telegram_user_id,
        is_active=employee.is_active,
        is_external=employee.is_external,
        is_bot=employee.is_bot,
        user_id=current_user.user_id
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id, Employee.user_id == current_user.user_id).first()
    if not db_employee:
        return {"error": "Employee not found"}
    for field, value in employee.dict(exclude_unset=True).items():
        setattr(db_employee, field, value)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_employee = db.query(Employee).filter(Employee.employee_id == employee_id, Employee.user_id == current_user.user_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(db_employee)
    db.commit()
    return {"detail": "Employee deleted"} 