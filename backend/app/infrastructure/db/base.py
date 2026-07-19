"""SQLAlchemy declarative base shared by all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by Fridgital persistence models."""
