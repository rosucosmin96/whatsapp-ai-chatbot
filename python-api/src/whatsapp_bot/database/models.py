from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    """User model for storing WhatsApp user information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    interactions = relationship("ChatInteraction", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone})>"

class ChatInteraction(Base):
    """Model for storing complete chat interactions"""
    __tablename__ = "chat_interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_message = Column(Text, nullable=False)
    response_message = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    
    def __repr__(self):
        return f"<ChatInteraction(id={self.id}, user_id={self.user_id})>"

class UsageLog(Base):
    """Log for tracking API usage and costs"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True)
    interaction_id = Column(Integer, ForeignKey("chat_interactions.id"), nullable=False)
    model = Column(String(50), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Integer, default=0)  # Cost in microdollars (actual cost * 1,000,000)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship
    interaction = relationship("ChatInteraction", backref="usage_log")
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, interaction_id={self.interaction_id}, tokens={self.total_tokens})>" 