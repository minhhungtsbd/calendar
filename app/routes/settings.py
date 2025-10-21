from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.session_service import session_service
from app.services.telegram_service import TelegramService
from app.services.feng_shui_service import FengShuiService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Settings page with notification preferences"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    context = {
        "request": request,
        "current_user": current_user
    }
    
    return templates.TemplateResponse("settings.html", context)


@router.post("/settings/notifications")
async def update_notification_settings(
    request: Request,
    email_notifications: bool = Form(False),
    telegram_notifications: bool = Form(False),
    telegram_chat_id: str = Form(""),
    db: Session = Depends(get_db)
):
    """Update user notification settings"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    # Update user settings
    current_user.email_notifications = email_notifications
    current_user.telegram_notifications = telegram_notifications
    
    # Clean telegram_chat_id
    if telegram_chat_id.strip():
        current_user.telegram_chat_id = telegram_chat_id.strip()
    else:
        current_user.telegram_chat_id = None
        current_user.telegram_notifications = False  # Disable if no chat ID
    
    db.commit()
    
    context = {
        "request": request,
        "success": True,
        "message": "✅ Đã cập nhật cài đặt thông báo thành công!"
    }
    
    return templates.TemplateResponse("components/notification_result.html", context)


@router.post("/settings/test-telegram")
async def test_telegram_settings(
    request: Request,
    db: Session = Depends(get_db)
):
    """Test Telegram notification"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    if not current_user.telegram_chat_id:
        context = {
            "request": request,
            "success": False,
            "message": "⚠️ Bạn chưa cài đặt Telegram Chat ID. Vui lòng cài đặt trước khi test."
        }
        return templates.TemplateResponse("components/notification_result.html", context)
    
    telegram_service = TelegramService()

    # Test connection
    connection_ok = await telegram_service.test_connection()
    if not connection_ok:
        context = {
            "request": request,
            "success": False,
            "message": "❌ Không thể kết nối với Telegram bot"
        }
        return templates.TemplateResponse("components/notification_result.html", context)

    # Send test message to user's chat
    success = await telegram_service.send_message(
        f"🎉 Test thành công!\n\nXin chào {current_user.name}!\nBot lịch âm dương đã hoạt động bình thường và sẵn sàng gửi thông báo cho bạn.",
        chat_id=current_user.telegram_chat_id
    )

    context = {
        "request": request,
        "success": success,
        "message": "✅ Gửi tin nhắn test thành công! Kiểm tra Telegram của bạn." if success else "❌ Không thể gửi tin nhắn test. Kiểm tra lại Chat ID."
    }

    return templates.TemplateResponse("components/notification_result.html", context)


@router.post("/settings/menh-method", response_class=HTMLResponse)
async def update_menh_method(
    request: Request,
    menh_method: str = Form(...),
    db: Session = Depends(get_db)
):
    """Cập nhật phương pháp tính mệnh"""
    # Require authentication
    try:
        current_user = session_service.require_auth(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    
    try:
        # Cập nhật phương pháp tính mệnh
        current_user.menh_calculation_method = menh_method
        db.commit()
        
        # Lấy thông tin so sánh để hiển thị
        if current_user.birth_date:
            comparison = FengShuiService.compare_birth_year_methods(current_user.birth_date)
            
            return HTMLResponse(f'''
            <div class="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    <span class="text-green-800 dark:text-green-200 font-semibold">
                        ✅ Đã cập nhật phương pháp tính mệnh thành công!
                    </span>
                </div>
                <div class="mt-3 text-sm text-green-700 dark:text-green-300">
                    <p><strong>Phương pháp hiện tại:</strong> 
                    {"🏛️ Cách truyền thống (Can Chi)" if menh_method == "can_chi" else "📜 Cách Nạp Âm (60 năm)"}</p>
                    <p><strong>Mệnh của bạn:</strong> 
                    {comparison["method_1_can_chi"]["element"] if menh_method == "can_chi" else comparison["method_2_nap_am"]["element"]} - 
                    {comparison["method_1_can_chi"]["description"] if menh_method == "can_chi" else comparison["method_2_nap_am"]["description"]}</p>
                </div>
            </div>
            ''')
        else:
            return HTMLResponse('''
            <div class="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-4">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    <span class="text-green-800 dark:text-green-200 font-semibold">
                        ✅ Đã cập nhật phương pháp tính mệnh thành công!
                    </span>
                </div>
            </div>
            ''')
            
    except Exception as e:
        return HTMLResponse(f'''
        <div class="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-4">
            <div class="flex items-center">
                <svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                <span class="text-red-800 dark:text-red-200 font-semibold">
                    ❌ Có lỗi xảy ra: {str(e)}
                </span>
            </div>
        </div>
        ''') 