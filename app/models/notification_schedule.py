from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NotificationSchedule(Base):
    """Track notification progress for each note"""
    __tablename__ = "notification_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    
    # Progress tracking
    total_notifications_needed = Column(Integer, nullable=False)  # Tổng số thông báo cần gửi
    notifications_sent = Column(Integer, default=0)  # Số thông báo đã gửi
    current_days_before = Column(Integer, nullable=False)  # Ngày hiện tại cần thông báo
    current_year = Column(Integer, nullable=False)  # Năm hiện tại của schedule (cho yearly repeat)
    
    # Status
    is_completed = Column(Boolean, default=False)  # Đã hoàn thành tất cả thông báo
    last_notification_sent = Column(DateTime(timezone=True))  # Lần gửi cuối
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    note = relationship("Note", backref="notification_schedule")
    
    def __repr__(self):
        return f"<NotificationSchedule(note_id={self.note_id}, sent={self.notifications_sent}/{self.total_notifications_needed}, year={self.current_year})>"
    
    @property
    def remaining_notifications(self):
        """Số thông báo còn lại"""
        return max(0, self.total_notifications_needed - self.notifications_sent)
    
    @property
    def progress_percentage(self):
        """Phần trăm hoàn thành"""
        if self.total_notifications_needed == 0:
            return 100
        return int((self.notifications_sent / self.total_notifications_needed) * 100) 