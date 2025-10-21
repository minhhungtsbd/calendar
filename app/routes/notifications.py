from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.note import Note
from app.services.notification_service import NotificationService
from app.services.session_service import SessionService
import logging
from app.models.notification_schedule import NotificationSchedule
from datetime import date, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)
session_service = SessionService()


@router.get("/notifications", response_class=HTMLResponse)
async def notifications_list(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all notification schedules"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's notification schedules
    schedules = db.query(NotificationSchedule).join(Note).filter(
        Note.user_id == current_user.id
    ).order_by(NotificationSchedule.is_completed, Note.solar_date.desc()).all()
    
    context = {
        "request": request,
        "current_user": current_user,
        "schedules": schedules,
        "today": date.today(),
        "timedelta": timedelta  # For template calculations
    }
    
    return templates.TemplateResponse("notifications.html", context)


@router.get("/notifications/stats")
async def notification_schedule_stats(request: Request, db: Session = Depends(get_db)):
    """Get notification schedule statistics"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return {"error": "Authentication required"}
    
    notification_service = NotificationService()
    stats = notification_service.get_schedule_statistics(db, current_user.id)
    
    return {
        "stats": stats,
        "user_id": current_user.id
    }






