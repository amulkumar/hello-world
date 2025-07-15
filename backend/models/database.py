from sqlalchemy import (
    Column, Integer, String, Decimal, DateTime, Date, Boolean, 
    Text, ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(Base, TimestampMixin):
    """User accounts and authentication"""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(100))
    role = Column(String(50), nullable=False)  # 'trader', 'risk_manager', 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    positions = relationship("Position", back_populates="trader")
    limit_breaches_created = relationship("LimitBreach", foreign_keys="LimitBreach.created_by_id", back_populates="created_by")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
    )


class Instrument(Base, TimestampMixin):
    """Financial instrument reference data"""
    __tablename__ = "instruments"
    
    id = Column(String(50), primary_key=True)  # ISIN, ticker, or internal ID
    instrument_type = Column(String(20), nullable=False)  # 'equity', 'bond', 'fx', 'commodity'
    name = Column(String(255), nullable=False)
    currency = Column(String(3), nullable=False)
    sector = Column(String(50))
    country = Column(String(3))
    exchange = Column(String(50))
    bloomberg_id = Column(String(50))
    reuters_id = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    market_data = relationship("MarketData", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")
    
    __table_args__ = (
        Index('idx_instruments_type', 'instrument_type'),
        Index('idx_instruments_currency', 'currency'),
        Index('idx_instruments_sector', 'sector'),
    )


class MarketData(Base, TimestampMixin):
    """Market data time series"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(String(50), ForeignKey('instruments.id'), nullable=False)
    data_type = Column(String(20), nullable=False)  # 'price', 'rate', 'volatility', 'dividend_yield'
    business_date = Column(Date, nullable=False)
    value = Column(Decimal(15, 8), nullable=False)
    currency = Column(String(3))
    source = Column(String(50), nullable=False)  # 'bloomberg', 'reuters', 'manual'
    
    # Relationships
    instrument = relationship("Instrument", back_populates="market_data")
    
    __table_args__ = (
        UniqueConstraint('instrument_id', 'data_type', 'business_date', name='uq_market_data'),
        Index('idx_market_data_date', 'business_date'),
        Index('idx_market_data_instrument_date', 'instrument_id', 'business_date'),
        Index('idx_market_data_type_date', 'data_type', 'business_date'),
    )


class Portfolio(Base, TimestampMixin):
    """Portfolio definitions"""
    __tablename__ = "portfolios"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    desk = Column(String(100), nullable=False)
    business_line = Column(String(100))
    currency = Column(String(3), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    positions = relationship("Position", back_populates="portfolio")
    risk_calculations = relationship("RiskCalculation", back_populates="portfolio")
    risk_limits = relationship("RiskLimit", back_populates="portfolio")


class Position(Base, TimestampMixin):
    """Portfolio positions"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), ForeignKey('portfolios.id'), nullable=False)
    instrument_id = Column(String(50), ForeignKey('instruments.id'), nullable=False)
    business_date = Column(Date, nullable=False)
    quantity = Column(Decimal(15, 2), nullable=False)
    market_value = Column(Decimal(15, 2))
    currency = Column(String(3), nullable=False)
    trader_id = Column(String(50), ForeignKey('users.id'))
    cost_basis = Column(Decimal(15, 2))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    trader = relationship("User", back_populates="positions")
    
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'instrument_id', 'business_date', name='uq_positions'),
        Index('idx_positions_date', 'business_date'),
        Index('idx_positions_portfolio_date', 'portfolio_id', 'business_date'),
        Index('idx_positions_trader', 'trader_id'),
    )


class RiskCalculation(Base, TimestampMixin):
    """Risk calculation results"""
    __tablename__ = "risk_calculations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(50), ForeignKey('portfolios.id'), nullable=False)
    business_date = Column(Date, nullable=False)
    calculation_type = Column(String(20), nullable=False)  # 'var', 'es', 'stress', 'irc'
    methodology = Column(String(20))  # 'historical', 'monte_carlo', 'parametric'
    confidence_level = Column(Decimal(4, 3))
    holding_period = Column(Integer)
    risk_value = Column(Decimal(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    scenario_name = Column(String(100))  # For stress tests
    calculation_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='completed', nullable=False)
    model_version = Column(String(20))
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="risk_calculations")
    
    __table_args__ = (
        Index('idx_risk_calc_portfolio_date', 'portfolio_id', 'business_date'),
        Index('idx_risk_calc_type', 'calculation_type'),
        Index('idx_risk_calc_date', 'business_date'),
        CheckConstraint('risk_value IS NOT NULL', name='chk_risk_value_not_null'),
    )


class RiskLimit(Base, TimestampMixin):
    """Risk limits configuration"""
    __tablename__ = "risk_limits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(20), nullable=False)  # 'portfolio', 'trader', 'desk'
    entity_id = Column(String(50), nullable=False)
    limit_type = Column(String(20), nullable=False)  # 'var', 'es', 'notional', 'concentration'
    limit_value = Column(Decimal(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(50), nullable=False)
    approved_by = Column(String(50))
    approval_date = Column(DateTime(timezone=True))
    
    # Relationships (for portfolio limits)
    portfolio = relationship("Portfolio", back_populates="risk_limits", 
                           primaryjoin="and_(RiskLimit.entity_id==Portfolio.id, RiskLimit.entity_type=='portfolio')",
                           foreign_keys=[entity_id])
    breaches = relationship("LimitBreach", back_populates="limit")
    
    __table_args__ = (
        Index('idx_risk_limits_entity', 'entity_type', 'entity_id'),
        Index('idx_risk_limits_type', 'limit_type'),
        Index('idx_risk_limits_active', 'is_active'),
        CheckConstraint('limit_value > 0', name='chk_limit_value_positive'),
    )


class LimitBreach(Base, TimestampMixin):
    """Limit breach tracking"""
    __tablename__ = "limit_breaches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    limit_id = Column(Integer, ForeignKey('risk_limits.id'), nullable=False)
    business_date = Column(Date, nullable=False)
    actual_value = Column(Decimal(15, 2), nullable=False)
    limit_value = Column(Decimal(15, 2), nullable=False)
    breach_percentage = Column(Decimal(5, 2))
    severity = Column(String(20), nullable=False)  # 'warning', 'breach', 'critical'
    status = Column(String(20), default='open', nullable=False)  # 'open', 'acknowledged', 'resolved'
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(255))
    resolution_comment = Column(Text)
    escalated = Column(Boolean, default=False)
    escalation_time = Column(DateTime(timezone=True))
    created_by_id = Column(String(50), ForeignKey('users.id'))
    
    # Relationships
    limit = relationship("RiskLimit", back_populates="breaches")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="limit_breaches_created")
    
    __table_args__ = (
        Index('idx_breach_date', 'business_date'),
        Index('idx_breach_status', 'status'),
        Index('idx_breach_severity', 'severity'),
        Index('idx_breach_limit', 'limit_id'),
    )


class Report(Base, TimestampMixin):
    """Report metadata and tracking"""
    __tablename__ = "reports"
    
    id = Column(String(50), primary_key=True)
    report_type = Column(String(50), nullable=False)  # 'daily_risk', 'regulatory', 'stress_test'
    business_date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_format = Column(String(10))  # 'pdf', 'xlsx', 'csv'
    status = Column(String(20), default='draft', nullable=False)  # 'draft', 'generated', 'signed_off'
    generated_by = Column(String(50), nullable=False)
    generation_time = Column(DateTime(timezone=True))
    
    # Relationships
    sign_offs = relationship("ReportSignOff", back_populates="report")
    
    __table_args__ = (
        Index('idx_reports_type_date', 'report_type', 'business_date'),
        Index('idx_reports_status', 'status'),
        Index('idx_reports_date', 'business_date'),
    )


class ReportSignOff(Base, TimestampMixin):
    """Report sign-off workflow"""
    __tablename__ = "report_sign_offs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(50), ForeignKey('reports.id'), nullable=False)
    sign_off_level = Column(Integer, nullable=False)  # 1=reviewer, 2=approver
    required_role = Column(String(50), nullable=False)
    assigned_to = Column(String(50))
    signed_off_by = Column(String(50))
    signed_off_at = Column(DateTime(timezone=True))
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'approved', 'rejected'
    comments = Column(Text)
    deadline = Column(DateTime(timezone=True))
    
    # Relationships
    report = relationship("Report", back_populates="sign_offs")
    
    __table_args__ = (
        Index('idx_signoff_report', 'report_id'),
        Index('idx_signoff_status', 'status'),
        Index('idx_signoff_assigned', 'assigned_to'),
    )


class AuditLog(Base):
    """Audit trail for all system operations"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
    )


class SystemParameter(Base, TimestampMixin):
    """System configuration parameters"""
    __tablename__ = "system_parameters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parameter_name = Column(String(100), unique=True, nullable=False)
    parameter_value = Column(Text, nullable=False)
    parameter_type = Column(String(20), nullable=False)  # 'string', 'number', 'boolean', 'json'
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_by = Column(String(50), nullable=False)
    
    __table_args__ = (
        Index('idx_system_params_name', 'parameter_name'),
        Index('idx_system_params_active', 'is_active'),
    )