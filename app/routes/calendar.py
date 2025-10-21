from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import Optional
from app.database import get_db
from app.services.lunar_calendar import LunarCalendarService
from app.services.feng_shui_service import FengShuiService
from app.services.google_calendar_service import google_calendar_service
from app.services.session_service import session_service
from app.models.note import Note

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def calendar_view(
    request: Request,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    focus_date: Optional[str] = Query(None),  # Add focus date parameter
    db: Session = Depends(get_db)
):
    """Main calendar view"""
    # Use current date if not specified
    today = date.today()
    
    # Handle focus date for navigation
    if focus_date:
        try:
            focus_date_obj = datetime.strptime(focus_date, '%Y-%m-%d').date()
            current_year = year or focus_date_obj.year
            current_month = month or focus_date_obj.month
            today = focus_date_obj  # Update 'today' to be the focused date
        except ValueError:
            current_year = year or today.year
            current_month = month or today.month
    else:
        current_year = year or today.year
        current_month = month or today.month
    
    # Get calendar data with focused date
    calendar_weeks = LunarCalendarService.get_month_calendar(current_year, current_month, today)
    
    # Get current user first
    current_user = session_service.get_current_user(request, db)
    
    # Add feng shui information to each day (personalized if user has birth_date)
    for week in calendar_weeks:
        for day_info in week:
            day_date = day_info["date"]
            if current_user and current_user.birth_date:
                # Get personalized feng shui summary
                method = getattr(current_user, 'menh_calculation_method', 'can_chi')
                personal_feng_shui = FengShuiService.get_personal_feng_shui_advice(
                    current_user.birth_date, day_date, method
                )
                # Create a compact summary for calendar display
                compatibility_score = personal_feng_shui["compatibility"]["score"]
                if compatibility_score >= 80:
                    feng_shui_summary = f"🟢 Rất tốt ({compatibility_score}/100)"
                elif compatibility_score >= 60:
                    feng_shui_summary = f"🔵 Tốt ({compatibility_score}/100)"
                elif compatibility_score >= 40:
                    feng_shui_summary = f"🟡 Trung bình ({compatibility_score}/100)"
                else:
                    feng_shui_summary = f"🔴 Cần cẩn thận ({compatibility_score}/100)"
            else:
                # Get general feng shui summary for non-logged in users or users without birth_date
                feng_shui_summary = FengShuiService.get_feng_shui_summary(day_date)
            
            day_info["feng_shui_summary"] = feng_shui_summary
    
    # Get notes for the month (filtered by user if logged in)
    first_day = date(current_year, current_month, 1)
    if current_month == 12:
        last_day = date(current_year + 1, 1, 1)
    else:
        last_day = date(current_year, current_month + 1, 1)
    
    notes_query = db.query(Note).filter(
        Note.solar_date >= first_day,
        Note.solar_date < last_day,
        Note.is_active == True
    )
    
    # Filter by user if logged in
    if current_user:
        notes_query = notes_query.filter(Note.user_id == current_user.id)
    else:
        # No notes for guest users
        notes_query = notes_query.filter(Note.user_id == -1)  # No results
    
    notes = notes_query.all()
    
    # Create notes dictionary by date
    notes_by_date = {}
    for note in notes:
        date_str = note.solar_date.strftime('%Y-%m-%d')
        if date_str not in notes_by_date:
            notes_by_date[date_str] = []
        notes_by_date[date_str].append(note)
    
    # Get lunar holidays
    lunar_holidays = LunarCalendarService.get_lunar_holidays(current_year)
    
    # Get Google Calendar holidays for the month
    google_holidays = google_calendar_service.get_holidays_for_month(current_year, current_month)
    
    # Create holidays dictionary by date (combine lunar and Google holidays)
    holidays_by_date = {}
    
    # Add lunar holidays
    for holiday in lunar_holidays:
        date_str = holiday["solar_date"].strftime('%Y-%m-%d')
        if date_str not in holidays_by_date:
            holidays_by_date[date_str] = []
        holidays_by_date[date_str].append({
            'name': holiday['name'],
            'type': 'lunar',
            'description': f"Ngày {holiday['lunar_date']}"
        })
    
    # Add Google Calendar holidays
    for holiday in google_holidays:
        date_str = holiday["date_str"]
        if date_str not in holidays_by_date:
            holidays_by_date[date_str] = []
        holidays_by_date[date_str].append({
            'name': holiday['name'],
            'type': 'national',
            'description': holiday.get('description', '')
        })
    
    # Navigation dates
    if current_month == 1:
        prev_year, prev_month = current_year - 1, 12
    else:
        prev_year, prev_month = current_year, current_month - 1
    
    if current_month == 12:
        next_year, next_month = current_year + 1, 1
    else:
        next_year, next_month = current_year, current_month + 1
    
    # Store real today for comparison
    real_today = date.today()
    
    # Get feng shui for sidebar
    personal_feng_shui_today = None
    general_feng_shui_today = None
    
    if current_user and current_user.birth_date:
        # Personal feng shui for logged in users with birth_date
        method = getattr(current_user, 'menh_calculation_method', 'can_chi')
        personal_feng_shui_today = FengShuiService.get_personal_feng_shui_advice(
            current_user.birth_date, today, method
        )
    else:
        # General feng shui for users without birth_date or not logged in
        general_feng_shui_today = FengShuiService.get_daily_feng_shui_analysis(today)
    
    context = {
        "request": request,
        "current_user": current_user,
        "current_year": current_year,
        "current_month": current_month,
        "calendar_weeks": calendar_weeks,
        "notes_by_date": notes_by_date,
        "lunar_holidays": lunar_holidays,
        "holidays_by_date": holidays_by_date,
        "google_calendar_configured": google_calendar_service.is_configured(),
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "today": today,
        "real_today": real_today,
        "personal_feng_shui_today": personal_feng_shui_today,
        "general_feng_shui_today": general_feng_shui_today,
        "timedelta": timedelta,
        "LunarCalendarService": LunarCalendarService,
        "FengShuiService": FengShuiService,
        "month_names": [
            "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
            "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
        ],
        "weekday_names": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    }
    
    return templates.TemplateResponse("calendar.html", context)


@router.get("/navigate-day/{date_str}", response_class=HTMLResponse)
async def navigate_day(
    request: Request,
    date_str: str,
    db: Session = Depends(get_db)
):
    """Navigate to a specific day without changing URL - HTMX endpoint"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()
    
    # Redirect to main calendar with focus date
    return await calendar_view(
        request=request,
        year=target_date.year,
        month=target_date.month,
        focus_date=date_str,
        db=db
    )


@router.get("/day/{date_str}", response_class=HTMLResponse)
async def day_view(
    request: Request,
    date_str: str,
    db: Session = Depends(get_db)
):
    """View for a specific day"""
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()
    
    # Get current user
    current_user = session_service.get_current_user(request, db)
    
    # Get lunar information
    lunar_info = LunarCalendarService.get_lunar_info(selected_date)
    
    # Get feng shui analysis - personalized if user has birth date
    feng_shui_analysis = None
    personal_feng_shui = None
    
    if current_user and current_user.birth_date:
        # Get personalized feng shui advice
        personal_feng_shui = FengShuiService.get_personal_feng_shui_advice(
            current_user.birth_date, selected_date
        )
    else:
        # Get general feng shui analysis
        feng_shui_analysis = FengShuiService.get_daily_feng_shui_analysis(selected_date)
    
    # Get notes for this day (filtered by user if logged in)
    notes_query = db.query(Note).filter(
        Note.solar_date == selected_date,
        Note.is_active == True
    )
    
    # Filter by user if logged in
    if current_user:
        notes_query = notes_query.filter(Note.user_id == current_user.id)
    else:
        # No notes for guest users
        notes_query = notes_query.filter(Note.user_id == -1)  # No results
    
    notes = notes_query.all()
    
    # Get holidays for this day
    date_str = selected_date.strftime('%Y-%m-%d')
    day_holidays = []
    
    # Get lunar holidays for the year
    lunar_holidays = LunarCalendarService.get_lunar_holidays(selected_date.year)
    for holiday in lunar_holidays:
        if holiday["solar_date"] == selected_date:
            day_holidays.append({
                'name': holiday['name'],
                'type': 'lunar',
                'description': f"Ngày {holiday['lunar_date']}"
            })
    
    # Get Google Calendar holidays for the month
    google_holidays = google_calendar_service.get_holidays_for_month(selected_date.year, selected_date.month)
    for holiday in google_holidays:
        if holiday["date_str"] == date_str:
            day_holidays.append({
                'name': holiday['name'],
                'type': 'national',
                'description': holiday.get('description', '')
            })
    
    context = {
        "request": request,
        "current_user": current_user,
        "selected_date": selected_date,
        "lunar_info": lunar_info,
        "feng_shui_analysis": feng_shui_analysis,
        "personal_feng_shui": personal_feng_shui,
        "notes": notes,
        "holidays": day_holidays,
        "google_calendar_configured": google_calendar_service.is_configured(),
        "timedelta": timedelta,
        "LunarCalendarService": LunarCalendarService,
        "FengShuiService": FengShuiService
    }
    
    return templates.TemplateResponse("day_view.html", context)


@router.get("/api/feng-shui/{date_str}")
async def get_feng_shui_api(
    request: Request,
    date_str: str,
    db: Session = Depends(get_db)
):
    """API endpoint to get feng shui information for a specific date"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return {"error": "Invalid date format"}
    
    # Get current user
    current_user = session_service.get_current_user(request, db)
    
    if current_user and current_user.birth_date:
        # Return personalized feng shui advice
        personal_feng_shui = FengShuiService.get_personal_feng_shui_advice(
            current_user.birth_date, target_date
        )
        
        # Convert date objects to strings for JSON serialization
        personal_feng_shui["day_info"]["date"] = personal_feng_shui["day_info"]["date"].strftime('%Y-%m-%d')
        
        return {
            "type": "personal",
            "data": personal_feng_shui
        }
    else:
        # Return general feng shui analysis
        feng_shui_analysis = FengShuiService.get_daily_feng_shui_analysis(target_date)
        
        # Convert date objects to strings for JSON serialization
        feng_shui_analysis["date"] = feng_shui_analysis["date"].strftime('%Y-%m-%d')
        
        return {
            "type": "general",
            "data": feng_shui_analysis
        }
