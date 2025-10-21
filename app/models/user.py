from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Google OAuth information
    google_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    picture = Column(String(500))  # URL to profile picture
    
    # User preferences
    locale = Column(String(10), default="vi")  # vi, en
    timezone = Column(String(50), default="Asia/Ho_Chi_Minh")
    birth_date = Column(Date, nullable=True)  # User's birth date from Google
    menh_calculation_method = Column(String(20), default="can_chi")  # can_chi hoặc nap_am
    
    # Notification settings
    email_notifications = Column(Boolean, default=True)
    telegram_notifications = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)  # Telegram user ID
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)  # Google accounts are pre-verified
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
    
    @property
    def first_name(self):
        """Get first name from full name"""
        return self.name.split()[0] if self.name else ""
    
    @property
    def display_name(self):
        """Get display name for UI"""
        return self.first_name or self.email.split('@')[0] 