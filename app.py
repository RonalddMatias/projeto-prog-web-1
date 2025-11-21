from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends
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
    db_customer = db.query(models.Customer).filter(models.Customer.email == payload.email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_customer = models.Customer(**payload.dict())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.get("/customers", response_model=List[Customer])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[Customer]:
    return db.query(models.Customer).offset(skip).limit(limit).all()


@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int, db: Session = Depends(get_db)) -> Customer:
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
        
    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> None:
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    return None


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok"}
