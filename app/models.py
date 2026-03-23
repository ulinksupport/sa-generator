from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .db import Base

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Matter(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")
    messages = relationship("Message", back_populates="matter", cascade="all, delete-orphan")
    answers = relationship("MatterAnswer", back_populates="matter", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    sender_name = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    matter = relationship("Matter", back_populates="messages")

class MatterAnswer(Base):
    __tablename__ = "matter_answers"
    id = Column(Integer, primary_key=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    field_key = Column(String(100), nullable=False)
    field_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    matter = relationship("Matter", back_populates="answers")

    __table_args__ = (
        UniqueConstraint("matter_id", "field_key", name="uq_matter_field_key"),
    )