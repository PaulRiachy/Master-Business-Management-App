from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import Customer, Role, Supplier, User
from app.schemas.schemas import CustomerCreate, CustomerOut, SupplierCreate, SupplierOut, UserOut

router = APIRouter()


@router.get("/customers", response_model=list[CustomerOut])
def customers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Customer).order_by(Customer.name)).all()


@router.post("/customers", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.SALES)),
):
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/suppliers", response_model=list[SupplierOut])
def suppliers(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.PROCUREMENT)),
):
    return db.scalars(select(Supplier).order_by(Supplier.name)).all()


@router.post("/suppliers", response_model=SupplierOut)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.ADMIN, Role.PROCUREMENT)),
):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(User).order_by(User.name)).all()
