"""
SQLAlchemy models for Supabase database tables
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from db import Base
import uuid


class Profile(Base):
    """
    User profile table that extends Supabase auth.users
    Links to Supabase auth via the id field
    """
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True, index=True)
    role = Column(String(50), nullable=False, default='free')  # 'free', 'subscriber', 'admin'
    subscription_status = Column(String(50), nullable=False, default='none')  # 'active', 'canceled', 'trial', 'none'
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Profile(id={self.id}, email={self.email}, role={self.role})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'email': self.email,
            'role': self.role,
            'subscription_status': self.subscription_status,
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(Base):
    """
    Audit log for tracking important system actions
    Useful for monitoring admin actions and user events
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Can be null for system actions
    action = Column(String(100), nullable=False)  # e.g., 'user_created', 'subscription_changed', 'admin_action'
    details = Column(Text, nullable=True)  # JSON string with additional details
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemMetrics(Base):
    """
    System metrics for monitoring application performance
    Can track API usage, refresh job status, etc.
    """
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)  # e.g., 'odds_refresh_duration', 'api_calls_per_hour'
    metric_value = Column(String(255), nullable=False)  # Store as string for flexibility
    metric_type = Column(String(50), nullable=False)  # 'duration', 'count', 'status', etc.
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For user-specific metrics
    additional_data = Column(Text, nullable=True)  # JSON string for extra context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(metric_name={self.metric_name}, value={self.metric_value})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'user_id': str(self.user_id) if self.user_id else None,
            'additional_data': self.additional_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 