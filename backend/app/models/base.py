"""SQLAlchemy Declarative Base."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models with standard timestamp and UUID helper."""
    pass


def generate_uuid() -> str:
    """Generates standard UUID4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)

