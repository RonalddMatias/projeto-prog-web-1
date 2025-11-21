from typing import List, Optional

from fastapi import Depends, FastAPI, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import engine, get_db
import models
from users import router as user_router
from utils.utils import ensure_unique, get_or_404

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Customer CRUD", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")


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
    ensure_unique(db, models.Customer, models.Customer.email, payload.email, detail="Email already registered")

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
    return get_or_404(db, models.Customer, customer_id, detail="Customer not found")


@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)) -> Customer:
    customer = get_or_404(db, models.Customer, customer_id, detail="Customer not found")

    update_data = payload.dict(exclude_unset=True)
    if "email" in update_data:
        ensure_unique(
            db,
            models.Customer,
            models.Customer.email,
            update_data["email"],
            exclude_id=customer_id,
            detail="Email already registered",
        )

    for key, value in update_data.items():
        setattr(customer, key, value)
        
    db.commit()
    db.refresh(customer)
    return customer


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)) -> None:
    customer = get_or_404(db, models.Customer, customer_id, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return None


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok"}
