from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.session_service import session_service
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service(
    request: Request,
    db: Session = Depends(get_db)
):
    """Terms of Service page"""
    # Get current user if logged in
    current_user = session_service.get_current_user(request, db)
    
    context = {
        "request": request,
        "current_user": current_user
    }
    
    return templates.TemplateResponse("legal/terms.html", context)


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(
    request: Request,
    db: Session = Depends(get_db)
):
    """Privacy Policy page"""
    # Get current user if logged in
    current_user = session_service.get_current_user(request, db)
    
    context = {
        "request": request,
        "current_user": current_user
    }
    
    return templates.TemplateResponse("legal/privacy.html", context)


@router.get("/owner", response_class=HTMLResponse)
async def owner_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Owner information page for domain verification"""
    # Get current user if logged in
    current_user = session_service.get_current_user(request, db)
    
    context = {
        "request": request,
        "current_user": current_user,
        "owner_info": {
            "name": "Minh Hưng",
            "email": "minhhungtsbd@gmail.com",
            "domain": "calendar.minhhungtsbd.me",
            "company": "Minh Hưng Tech Solutions",
            "verified": True
        }
    }
    
    return templates.TemplateResponse("legal/owner.html", context)


@router.get("/domain-verification", response_class=HTMLResponse)
async def domain_verification(
    request: Request,
    db: Session = Depends(get_db)
):
    """Domain verification page for Google"""
    # Get current user if logged in
    current_user = session_service.get_current_user(request, db)
    
    context = {
        "request": request,
        "current_user": current_user,
        "verification_code": "google-site-verification=YOUR_VERIFICATION_CODE_HERE"
    }
    
    return templates.TemplateResponse("legal/domain_verification.html", context) 