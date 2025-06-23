from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invitations = relationship("Invitation", back_populates="invited_by_user")

class Invitation(Base):
    __tablename__ = 'invitations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, nullable=False, index=True, unique=True)
    status = Column(String, default='pending')
    role = Column(String, default='visitante')
    invited_by = Column(UUID(as_uuid=True), nullable=True
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

    invited_by_user = relationship("User", back_populates="invitations", foreign_keys=[invited_by])