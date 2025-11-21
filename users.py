from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import get_db
from models import User as UserModel

router = APIRouter()


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
    _ensure_unique_user(db, email=payload.email, username=payload.username)

    new_user = UserModel(**payload.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=List[User])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> List[User]:
    return db.query(UserModel).offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    return _get_user_or_404(db, user_id)


@router.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = _get_user_or_404(db, user_id)

    update_data = payload.dict(exclude_unset=True)
    _ensure_unique_user(
        db,
        email=update_data.get("email"),
        username=update_data.get("username"),
        current_user_id=user_id,
    )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    db.delete(_get_user_or_404(db, user_id))
    db.commit()
    return None


def _get_user_or_404(db: Session, user_id: int) -> UserModel:
    """Return a user by id or raise a 404 if not found."""

    user = db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _ensure_unique_user(
    db: Session,
    *,
    email: Optional[str] = None,
    username: Optional[str] = None,
    current_user_id: Optional[int] = None,
) -> None:
    """Ensure user email and username are unique, ignoring the current user when provided."""

    if email:
        query = db.query(UserModel).filter(UserModel.email == email)
        if current_user_id is not None:
            query = query.filter(UserModel.id != current_user_id)
        if query.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if username:
        query = db.query(UserModel).filter(UserModel.username == username)
        if current_user_id is not None:
            query = query.filter(UserModel.id != current_user_id)
        if query.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
