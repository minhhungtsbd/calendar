from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.models.user import User
from app.logging_config import get_logger
import secrets

logger = get_logger('app.auth')


class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/user.birthday.read'
        ]
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL
        
        Returns:
            Tuple of (authorization_url, state)
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        # Create flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        # Generate state for security
        state = secrets.token_urlsafe(32)
        
        # Get authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        logger.info("Generated Google OAuth authorization URL")
        return authorization_url, state
    
    def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code from Google
            state: State parameter for security
            
        Returns:
            User information dictionary
        """
        try:
            # Create flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for token
            flow.fetch_token(code=code, include_granted_scopes=True)
            
            # Get user info from OAuth2 API
            credentials = flow.credentials
            oauth_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth_service.userinfo().get().execute()
            
            # Get birthday from People API
            try:
                people_service = build('people', 'v1', credentials=credentials)
                profile = people_service.people().get(
                    resourceName='people/me',
                    personFields='birthdays'
                ).execute()
                
                # Extract birthday information
                birth_date = None
                birthdays = profile.get('birthdays', [])
                for birthday in birthdays:
                    # Look for the primary birthday (from account)
                    if birthday.get('metadata', {}).get('primary', False):
                        date_info = birthday.get('date', {})
                        if all(key in date_info for key in ['year', 'month', 'day']):
                            try:
                                birth_date = date(
                                    year=date_info['year'],
                                    month=date_info['month'],
                                    day=date_info['day']
                                )
                                break
                            except ValueError:
                                logger.warning(f"Invalid birth date from Google: {date_info}")
                
                if birth_date:
                    user_info['birth_date'] = birth_date
                    logger.info(f"Retrieved birth date for user: {user_info.get('email')}")
                else:
                    logger.info(f"No birth date available for user: {user_info.get('email')}")
                    
            except Exception as e:
                logger.warning(f"Could not retrieve birth date from People API: {e}")
            
            logger.info(f"Successfully authenticated user: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    def get_or_create_user(self, db: Session, user_info: Dict[str, Any]) -> User:
        """
        Get existing user or create new user from Google user info
        
        Args:
            db: Database session
            user_info: User information from Google
            
        Returns:
            User instance
        """
        google_id = user_info.get('id')
        email = user_info.get('email')
        
        if not google_id or not email:
            raise ValueError("Invalid user info from Google")
        
        # Try to find existing user
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Try to find by email (in case user re-authorized)
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Update google_id
                user.google_id = google_id
        
        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=user_info.get('name', ''),
                picture=user_info.get('picture'),
                birth_date=user_info.get('birth_date'),
                is_active=True,
                is_verified=True
            )
            db.add(user)
            logger.info(f"Created new user: {email}")
        else:
            # Update existing user info
            user.name = user_info.get('name', user.name)
            user.picture = user_info.get('picture', user.picture)
            
            # Update birth_date if available and not already set
            if user_info.get('birth_date') and not user.birth_date:
                user.birth_date = user_info.get('birth_date')
                logger.info(f"Updated birth date for user: {email}")
            
            user.is_active = True
            logger.info(f"Updated existing user: {email}")
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def is_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.client_id and self.client_secret and self.redirect_uri)


# Global instance
google_auth_service = GoogleAuthService() 