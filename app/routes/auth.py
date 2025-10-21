from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.database import get_db
from app.services.auth_service import google_auth_service
from app.services.session_service import session_service
from app.logging_config import get_logger

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = get_logger('app.auth')


class BirthDateUpdate(BaseModel):
    birth_date: str  # Format: YYYY-MM-DD


@router.get("/login")
async def login_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Display login page"""
    # Check if user is already logged in
    current_user = session_service.get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=302)
    
    # Check if Google OAuth is configured
    if not google_auth_service.is_configured():
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Google OAuth không được cấu hình. Vui lòng liên hệ quản trị viên."
            }
        )
    
    # Generate Google OAuth URL
    try:
        auth_url, state = google_auth_service.get_authorization_url()
        
        # Store state in session for security
        response = templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "auth_url": auth_url,
                "google_configured": True
            }
        )
        response.set_cookie(
            key="oauth_state",
            value=state,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        return response
        
    except Exception as e:
        logger.error(f"Error generating Google OAuth URL: {e}")
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Không thể kết nối với Google. Vui lòng thử lại sau."
            }
        )


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    
    # Check for OAuth error
    if error:
        logger.warning(f"Google OAuth error: {error}")
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Đăng nhập bị hủy hoặc có lỗi xảy ra."
            }
        )
    
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not state or not stored_state or state != stored_state:
        logger.warning("OAuth state mismatch")
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Phiên đăng nhập không hợp lệ. Vui lòng thử lại."
            }
        )
    
    # Verify code parameter
    if not code:
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Thiếu mã xác thực từ Google."
            }
        )
    
    try:
        # Exchange code for user info
        user_info = google_auth_service.exchange_code_for_tokens(code, state)
        
        # Get or create user
        user = google_auth_service.get_or_create_user(db, user_info)
        
        # Create session
        session_token = session_service.create_session_token(user.id)
        
        # Redirect to home page with session
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        
        # Clear OAuth state cookie
        response.delete_cookie("oauth_state")
        
        logger.info(f"User {user.email} logged in successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error during Google OAuth callback: {e}")
        return templates.TemplateResponse(
            "auth/login_error.html",
            {
                "request": request,
                "error": "Có lỗi xảy ra trong quá trình đăng nhập. Vui lòng thử lại."
            }
        )


@router.post("/auth/refresh-birth-date")
async def refresh_birth_date(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh birth date from Google account"""
    try:
        current_user = session_service.require_auth(request, db)
        
        # Get fresh user info from Google using stored credentials
        # Note: This would require storing refresh tokens, which is complex
        # For now, we'll return a message asking user to re-login
        
        return JSONResponse({
            "success": False,
            "message": "Để cập nhật ngày sinh từ Google, vui lòng đăng xuất và đăng nhập lại. Hệ thống sẽ tự động lấy thông tin mới nhất."
        })
        
    except HTTPException:
        return JSONResponse({
            "success": False,
            "message": "Bạn cần đăng nhập để sử dụng tính năng này"
        }, status_code=401)
    except Exception as e:
        logger.error(f"Error refreshing birth date: {e}")
        return JSONResponse({
            "success": False,
            "message": "Có lỗi xảy ra khi cập nhật ngày sinh"
        }, status_code=500)


@router.post("/auth/update-birth-date")
async def update_birth_date(
    birth_date_data: BirthDateUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update birth date manually"""
    try:
        current_user = session_service.require_auth(request, db)
        
        # Parse and validate birth date
        try:
            birth_date = datetime.strptime(birth_date_data.birth_date, '%Y-%m-%d').date()
        except ValueError:
            return JSONResponse({
                "success": False,
                "message": "Định dạng ngày sinh không hợp lệ"
            }, status_code=400)
        
        # Validate birth date is not in the future
        if birth_date > date.today():
            return JSONResponse({
                "success": False,
                "message": "Ngày sinh không thể là ngày trong tương lai"
            }, status_code=400)
        
        # Validate birth date is reasonable (not too old)
        if birth_date.year < 1900:
            return JSONResponse({
                "success": False,
                "message": "Ngày sinh không hợp lệ"
            }, status_code=400)
        
        # Update user's birth date
        current_user.birth_date = birth_date
        db.commit()
        
        logger.info(f"Updated birth date for user {current_user.email}: {birth_date}")
        
        return JSONResponse({
            "success": True,
            "message": "Cập nhật ngày sinh thành công"
        })
        
    except HTTPException:
        return JSONResponse({
            "success": False,
            "message": "Bạn cần đăng nhập để sử dụng tính năng này"
        }, status_code=401)
    except Exception as e:
        logger.error(f"Error updating birth date: {e}")
        return JSONResponse({
            "success": False,
            "message": "Có lỗi xảy ra khi cập nhật ngày sinh"
        }, status_code=500)


@router.get("/logout")
async def logout(request: Request):
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    
    logger.info("User logged out")
    return response


@router.get("/profile")
async def profile_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """Display user profile page"""
    try:
        current_user = session_service.require_auth(request, db)
        
        return templates.TemplateResponse(
            "auth/profile.html",
            {
                "request": request,
                "user": current_user,
                "current_user": current_user  # Add this for base template
            }
        )
        
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302) 