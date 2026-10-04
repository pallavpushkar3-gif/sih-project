from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(32))

    password_hash: Mapped[str | None] = mapped_column(String(240), nullable=True)
    disabled: Mapped[bool] = mapped_column(default=False, server_default="false")
    failed_logins: Mapped[int] = mapped_column(default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(nullable=True)
