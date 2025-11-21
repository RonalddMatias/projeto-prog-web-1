from typing import Any, Optional, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

T = TypeVar("T")


def get_or_404(db: Session, model: Type[T], id: Any, detail: str = "Not found") -> T:
    """
    Get a record by ID or raise a 404 HTTPException.
    """
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj


def ensure_unique(
    db: Session,
    model: Type[T],
    attribute: Any,
    value: Any,
    exclude_id: Optional[int] = None,
    detail: str = "Already exists",
) -> None:
    """
    Ensure a record with the given attribute value is unique.
    If exclude_id is provided, the record with that ID is ignored (useful for updates).
    """
    query = db.query(model).filter(attribute == value)
    if exclude_id is not None:
        query = query.filter(model.id != exclude_id)
    
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
