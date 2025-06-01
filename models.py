"""
Database models for bet-intel application
SQLAlchemy models matching Supabase database schema
"""
from sqlalchemy import Column, String, Text, TIMESTAMP, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Profile(Base):
    """
    User profile model matching Supabase public.profiles table
    This table stores additional user information beyond what's in auth.users
    """
    __tablename__ = "profiles"
    
    # Primary key matching auth.users.id (UUID as string)
    id = Column(String, primary_key=True)
    
    # User information
    email = Column(Text, nullable=True)
    role = Column(Text, default="free", nullable=False)
    subscription_status = Column(Text, default="none", nullable=False)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=text("NOW()"), onupdate=text("NOW()"))
    
    # Optional profile fields
    display_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    def __repr__(self):
        return f"<Profile(id={self.id}, email={self.email}, role={self.role})>" 