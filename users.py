from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import get_db
from models import User as UserModel
from utils.utils import ensure_unique, get_or_404

router = APIRouter() # Uma formar de export as rotas deste arquivo para o arquivo app.py


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr]
    full_name: Optional[str] = Field(None, max_length=100)


class User(UserCreate):
    id: int

    class Config:
        orm_mode = True


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    ensure_unique(db, UserModel, UserModel.email, payload.email, detail="Email already registered")
    ensure_unique(db, UserModel, UserModel.username, payload.username, detail="Username already registered")

    new_user = UserModel(**payload.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=List[User])
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
) -> List[User]:
    return db.query(UserModel).offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    return get_or_404(db, UserModel, user_id, detail="User not found")


@router.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = get_or_404(db, UserModel, user_id, detail="User not found")

    update_data = payload.dict(exclude_unset=True)
    
    if "email" in update_data:
        ensure_unique(
            db,
            UserModel,
            UserModel.email,
            update_data["email"],
            exclude_id=user_id,
            detail="Email already registered",
        )
    
    if "username" in update_data:
        ensure_unique(
            db,
            UserModel,
            UserModel.username,
            update_data["username"],
            exclude_id=user_id,
            detail="Username already registered",
        )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    user = get_or_404(db, UserModel, user_id, detail="User not found")
    db.delete(user)
    db.commit()
    return None
