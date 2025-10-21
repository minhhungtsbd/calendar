from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import settings
from app.models.user import User
from app.logging_config import get_logger

logger = get_logger('app.session')


class SessionService:
    """Service for managing user sessions"""
    
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(settings.secret_key)
        self.session_timeout = 30 * 24 * 60 * 60  # 30 days in seconds
    
    def create_session_token(self, user_id: int) -> str:
        """
        Create session token for user
        
        Args:
            user_id: User ID
            
        Returns:
            Session token string
        """
        return self.serializer.dumps({'user_id': user_id})
    
    def verify_session_token(self, token: str) -> Optional[int]:
        """
        Verify session token and return user ID
        
        Args:
            token: Session token
            
        Returns:
            User ID if valid, None if invalid
        """
        try:
            data = self.serializer.loads(token, max_age=self.session_timeout)
            return data.get('user_id')
        except (BadSignature, SignatureExpired):
            return None
    
    def get_current_user(self, request: Request, db: Session) -> Optional[User]:
        """
        Get current user from request session
        
        Args:
            request: FastAPI request object
            db: Database session
            
        Returns:
            User instance if authenticated, None otherwise
        """
        # Try to get session token from cookie
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            return None
        
        # Verify token
        user_id = self.verify_session_token(session_token)
        if not user_id:
            return None
        
        # Get user from database
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
        
        return user
    
    def require_auth(self, request: Request, db: Session) -> User:
        """
        Require authentication and return user or raise exception
        
        Args:
            request: FastAPI request object
            db: Database session
            
        Returns:
            User instance
            
        Raises:
            HTTPException: If user not authenticated
        """
        user = self.get_current_user(request, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        return user
    
    def create_guest_session(self) -> str:
        """
        Create a guest session token
        
        Returns:
            Guest session token
        """
        return self.serializer.dumps({'guest': True})
    
    def is_guest_session(self, token: str) -> bool:
        """
        Check if session token is for guest user
        
        Args:
            token: Session token
            
        Returns:
            True if guest session, False otherwise
        """
        try:
            data = self.serializer.loads(token, max_age=self.session_timeout)
            return data.get('guest', False)
        except (BadSignature, SignatureExpired):
            return False


# Global instance
session_service = SessionService() 