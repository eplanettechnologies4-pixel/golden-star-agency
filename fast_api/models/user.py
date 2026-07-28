from sqlalchemy import Column, Integer, String, Boolean
from fast_api.database import Base

class User(Base):
    __tablename__ = "accounts_user"  # Django's default table name for app accounts, model User

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    role = Column(String(20), default="customer", nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User {self.username} (role={self.role})>"
