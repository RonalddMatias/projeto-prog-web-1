from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import engine, get_db
import models
from users import router as user_router

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer CRUD", version="1.0.0")

app.include_router(user_router)


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr]
    phone: Optional[str] = Field(None, max_length=20)


class Customer(CustomerCreate):
    id: int

    class Config:
        orm_mode = True


@app.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    _ensure_unique_customer_email(db, payload.email)

    new_customer = models.Customer(**payload.dict())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.get("/customers", response_model=List[Customer])
def list_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> List[Customer]:
    return db.query(models.Customer).offset(skip).limit(limit).all()


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    return _get_customer_or_404(db, customer_id)


@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    customer = _get_customer_or_404(db, customer_id)

    update_data = payload.dict(exclude_unset=True)
    if "email" in update_data:
        _ensure_unique_customer_email(db, update_data["email"], customer_id)

    for key, value in update_data.items():
        setattr(customer, key, value)
        
    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> None:
    db.delete(_get_customer_or_404(db, customer_id))
    db.commit()
    return None


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok"}

def _get_customer_or_404(db: Session, customer_id: int) -> models.Customer:
    """Return a customer or raise a 404 if it does not exist."""

    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer

def _ensure_unique_customer_email(db: Session, email: str, customer_id: Optional[int] = None) -> None:
    """Ensure a customer email is unique, excluding the given customer id if provided."""

    query = db.query(models.Customer).filter(models.Customer.email == email)
    if customer_id is not None:
        query = query.filter(models.Customer.id != customer_id)
    existing_customer = query.first()
    if existing_customer:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
