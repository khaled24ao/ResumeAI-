"""Base model with common fields."""

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_base


class _BaseMixin:
    """Mixin with common columns for all models."""

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


# Create declarative base that includes common columns
Base = declarative_base(cls=_BaseMixin)
