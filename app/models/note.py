from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class CalendarType(enum.Enum):
    SOLAR = "solar"
    LUNAR = "lunar"


class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    
    # Date information
    solar_date = Column(Date, nullable=False)
    lunar_date = Column(Date)
    calendar_type = Column(Enum(CalendarType), default=CalendarType.SOLAR)
    
    # Notification settings
    enable_notification = Column(Boolean, default=True)
    notification_days_before = Column(Integer, default=3)  # Số ngày thông báo trước (VD: 5 = thông báo từ 5 ngày trước đến ngày sự kiện)
    yearly_repeat = Column(Boolean, default=False)  # Lặp lại hàng năm
    monthly_repeat = Column(Boolean, default=False)  # Lặp lại hàng tháng
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", backref="notes")
    
    def __repr__(self):
        return f"<Note(id={self.id}, user_id={self.user_id}, title='{self.title}', date={self.solar_date})>"
    

