from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.session_service import session_service
from app.logging_config import get_logger

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = get_logger('app.admin')


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    """Simple admin login form for testing"""
    
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - Lịch Âm Dương</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="min-h-screen flex items-center justify-center">
            <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Admin Login</h2>
                <form method="POST" action="/admin/login">
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-bold mb-2">
                            Email
                        </label>
                        <input type="email" name="email" value="admin@calendar.local" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-bold mb-2">
                            Password
                        </label>
                        <input type="password" name="password" value="admin123" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    </div>
                    <button type="submit" 
                            class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                        Login
                    </button>
                </form>
                <div class="mt-4 text-center">
                    <a href="/" class="text-blue-500 hover:text-blue-700">Back to Calendar</a>
                </div>
                <div class="mt-2 text-xs text-gray-500">
                    <p><strong>Default credentials:</strong></p>
                    <p>Email: admin@calendar.local</p>
                    <p>Password: admin123</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)


@router.post("/admin/login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Simple admin login (for testing)"""
    
    # Simple hardcoded admin check
    if email == "admin@calendar.local" and password == "admin123":
        # Get or create admin user
        admin_user = db.query(User).filter(User.email == email).first()
        
        if not admin_user:
            admin_user = User(
                google_id='admin_local',
                email=email,
                name='Calendar Admin',
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info(f"Created admin user: {email}")
        
        # Create session
        session_token = session_service.create_session_token(admin_user.id)
        
        # Redirect with session
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            secure=False  # Set to True in production with HTTPS
        )
        
        logger.info(f"Admin user {email} logged in successfully")
        return response
    
    else:
        # Invalid credentials
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Error</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div class="min-h-screen flex items-center justify-center">
                <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
                    <div class="text-center">
                        <h2 class="text-2xl font-bold text-red-600 mb-4">Login Failed</h2>
                        <p class="text-gray-600 mb-6">Invalid email or password</p>
                        <a href="/admin/login" 
                           class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                            Try Again
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """, status_code=401) 