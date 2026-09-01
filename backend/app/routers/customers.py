from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Customer
from app.schemas.schemas import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CustomerOut])
def list_customers(search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Customer)
    if search:
        like = f"%{search}%"
        query = query.filter(Customer.company_name.ilike(like) | Customer.contact_name.ilike(like) | Customer.email.ilike(like))
    return query.order_by(Customer.company_name).all()


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: str, customer_in: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in customer_in.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.quotations:
        raise HTTPException(status_code=409, detail="Cannot delete a customer with existing quotations")
    db.delete(customer)
    db.commit()
