from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import Optional
from app.database import get_db
from app.models.note import Note, CalendarType
from app.services.lunar_calendar import LunarCalendarService
from app.services.notification_service import NotificationService
from app.services.session_service import session_service
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


@router.get("/notes", response_class=HTMLResponse)
async def notes_list(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all notes"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's notes
    notes = db.query(Note).filter(
        Note.user_id == current_user.id,
        Note.is_active == True
    ).order_by(Note.solar_date.desc()).all()
    
    # Add lunar information to each note
    for note in notes:
        note.lunar_info = LunarCalendarService.get_lunar_info(note.solar_date)
    
    context = {
        "request": request,
        "current_user": current_user,
        "notes": notes,
        "today": date.today(),
        "LunarCalendarService": LunarCalendarService
    }
    
    return templates.TemplateResponse("notes.html", context)


@router.get("/notes/list", response_class=HTMLResponse)
async def notes_list_htmx(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get notes list for HTMX updates"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return HTMLResponse(content="<div>Authentication required</div>", status_code=401)
    
    # Get user's notes
    notes = db.query(Note).filter(
        Note.user_id == current_user.id,
        Note.is_active == True
    ).order_by(Note.solar_date.desc()).all()
    
    # Add lunar information to each note
    for note in notes:
        note.lunar_info = LunarCalendarService.get_lunar_info(note.solar_date)
    
    context = {
        "request": request,
        "current_user": current_user,
        "notes": notes,
        "today": date.today(),
        "LunarCalendarService": LunarCalendarService
    }
    
    return templates.TemplateResponse("components/notes_table.html", context)


@router.get("/notes/new", response_class=HTMLResponse)
async def new_note_form(
    request: Request,
    date_param: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db)
):
    """Show new note form"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Use provided date or today
        default_date = date_param if date_param else date.today().strftime('%Y-%m-%d')

        context = {
            "request": request,
            "current_user": current_user,
            "today": default_date
        }
        return templates.TemplateResponse("components/note_form.html", context)
    except Exception as e:
        logger.error(f"Error in new_note_form: {e}")
        # Return a simple error message for HTMX
        return HTMLResponse(
            content=f'<div class="p-4 bg-red-100 border border-red-400 text-red-700 rounded">Lỗi: {str(e)}</div>',
            status_code=500
        )


@router.post("/notes/new")
async def create_note(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    solar_date: str = Form(...),
    calendar_type: str = Form("solar"),
    enable_notification: bool = Form(False),
    notification_days: int = Form(3),
    yearly_repeat: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Create a new note"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Parse date
        note_date = datetime.strptime(solar_date, '%Y-%m-%d').date()
        
        # Create note
        note = Note(
            user_id=current_user.id,
            title=title,
            content=content,
            solar_date=note_date,
            calendar_type=CalendarType(calendar_type),
            enable_notification=enable_notification,
            notification_days_before=notification_days if enable_notification else 0,
            yearly_repeat=yearly_repeat if enable_notification else False
        )
        
        # If lunar calendar type, convert to solar date
        if calendar_type == "lunar":
            # For now, assume the input date is already solar
            # In a full implementation, you'd need lunar date inputs
            lunar_info = LunarCalendarService.get_lunar_info(note_date)
            note.lunar_date = note_date
        
        db.add(note)
        db.commit()
        db.refresh(note)
        
        # Create notification schedule if enabled
        if enable_notification:
            notification_service = NotificationService()
            notification_service.create_notification_schedule_for_note(db, note)
        
        # Check if request is from notes page (modal context)
        referer = request.headers.get("referer", "")
        is_htmx = request.headers.get("hx-request") == "true"
        hx_target = request.headers.get("hx-target", "")
        
        if is_htmx and "/notes" in referer and "modal" in hx_target:
            # HTMX request from notes page modal - return success message and trigger reload
            repeat_info = " (Lặp hàng năm)" if yearly_repeat else ""
            success_html = f"""
            <div class="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg mb-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    ✅ Đã tạo ghi chú '{note.title}' thành công!
                    {f" (Thông báo từ {notification_days} ngày trước{repeat_info})" if enable_notification else ""}
                </div>
            </div>
            <script>
                setTimeout(() => {{
                    // Reload notes list
                    htmx.ajax('GET', '/notes/list', {{target: '#notes-list', swap: 'innerHTML'}});
                    // Close modal if exists
                    if (window.closeModal) window.closeModal();
                    // Show success toast
                    if (window.showSuccess) {{
                        window.showSuccess("✅ Đã tạo ghi chú '{note.title}' thành công!");
                    }}
                }}, 100);
            </script>
            """
            return HTMLResponse(content=success_html, status_code=200)
        else:
            # Request from calendar or other pages - return redirect instruction
            success_html = f"""
            <div class="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg mb-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    ✅ Đã tạo ghi chú '{note.title}' thành công! Đang chuyển hướng...
                </div>
            </div>
            <script>
                setTimeout(() => {{
                    window.location.href = '/notes?success=created';
                }}, 1000);
            </script>
            """
            return HTMLResponse(content=success_html, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notes/{note_id}/edit", response_class=HTMLResponse)
async def edit_note_redirect(
    request: Request,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Redirect to notes page with edit modal"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get note and check ownership
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.is_active == True
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Redirect to notes page with edit parameter
    return RedirectResponse(url=f"/notes?edit={note_id}", status_code=302)


@router.get("/notes/{note_id}/edit-form", response_class=HTMLResponse)
async def edit_note_form_htmx(
    request: Request,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Load edit note form for HTMX"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return HTMLResponse(content="<div>Authentication required</div>", status_code=401)
    
    # Get note and check ownership
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.is_active == True
    ).first()
    if not note:
        return HTMLResponse(content="<div>Note not found</div>", status_code=404)
    
    context = {
        "request": request,
        "current_user": current_user,
        "note": note,
        "solar_date_str": note.solar_date.strftime('%Y-%m-%d')
    }
    
    return templates.TemplateResponse("components/note_form.html", context)


@router.post("/notes/{note_id}/edit")
async def update_note(
    request: Request,
    note_id: int,
    title: str = Form(...),
    content: str = Form(""),
    solar_date: str = Form(...),
    calendar_type: str = Form("solar"),
    enable_notification: bool = Form(False),
    notification_days: int = Form(3),
    yearly_repeat: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Update a note"""
    note = db.query(Note).filter(Note.id == note_id, Note.is_active == True).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    try:
        # Parse date
        note_date = datetime.strptime(solar_date, '%Y-%m-%d').date()
        
        # Update note
        note.title = title
        note.content = content
        note.solar_date = note_date
        note.calendar_type = CalendarType(calendar_type)
        note.enable_notification = enable_notification
        note.notification_days_before = notification_days if enable_notification else 0
        note.yearly_repeat = yearly_repeat if enable_notification else False
        
        db.commit()
        
        # Recreate notification schedule if enabled
        # First, delete existing schedule
        from app.models.notification_schedule import NotificationSchedule
        db.query(NotificationSchedule).filter(
            NotificationSchedule.note_id == note.id
        ).delete()
        
        if enable_notification:
            notification_service = NotificationService()
            notification_service.create_notification_schedule_for_note(db, note)
        
        # Return success message for HTMX and reload list
        success_html = f"""
        <div class="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg mb-4">
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                ✅ Đã cập nhật ghi chú '{note.title}' thành công!
                {f" (Thông báo từ {notification_days} ngày trước)" if enable_notification else ""}
            </div>
        </div>
        <script>
            setTimeout(() => {{
                // Reload notes list
                htmx.ajax('GET', '/notes/list', {{target: '#notes-list', swap: 'innerHTML'}});
                // Close modal if exists
                if (window.closeModal) window.closeModal();
                // Show success toast
                if (window.showSuccess) {{
                    window.showSuccess("✅ Đã cập nhật ghi chú '{note.title}' thành công!");
                }}
            }}, 100);
        </script>
        """
        
        return HTMLResponse(content=success_html, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_note(
    request: Request,
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a note (soft delete)"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get note and check ownership
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id,
        Note.is_active == True
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Store title for logging
    note_title = note.title
    
    # Soft delete
    note.is_active = False
    db.commit()
    
    # Delete notification schedule
    from app.models.notification_schedule import NotificationSchedule
    db.query(NotificationSchedule).filter(
        NotificationSchedule.note_id == note.id
    ).delete()
    db.commit()
    
    # Return empty response with 200 status - HTMX will handle deletion
    from fastapi.responses import Response
    return Response(status_code=200)
