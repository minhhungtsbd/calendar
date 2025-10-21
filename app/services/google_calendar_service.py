from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, date
from typing import List, Dict, Optional
from app.config import settings
from app.logging_config import google_calendar_logger as logger


class GoogleCalendarService:
    """Service for integrating with Google Calendar API to fetch Vietnamese holidays"""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        self.calendar_id = settings.google_calendar_id
        self.service = None
        
        if self.api_key:
            try:
                self.service = build('calendar', 'v3', developerKey=self.api_key)
                logger.info("Google Calendar service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Calendar service: {e}")
    
    def get_holidays_for_month(self, year: int, month: int) -> List[Dict]:
        """
        Get Vietnamese holidays for a specific month from Google Calendar
        
        Args:
            year: Year to get holidays for
            month: Month to get holidays for (1-12)
            
        Returns:
            List of holiday dictionaries with name, date, and description
        """
        if not self.service or not self.api_key:
            logger.warning("Google Calendar service not configured properly")
            return []
        
        try:
            # Calculate time range for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Format dates for API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Call Google Calendar API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            holidays = []
            
            for event in events:
                holiday = self._parse_event_to_holiday(event)
                if holiday:
                    holidays.append(holiday)
            
            logger.info(f"Retrieved {len(holidays)} holidays for {month}/{year}")
            return holidays
            
        except HttpError as error:
            logger.error(f"An error occurred while fetching holidays: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching holidays: {e}")
            return []
    
    def get_holidays_for_year(self, year: int) -> List[Dict]:
        """
        Get Vietnamese holidays for the entire year
        
        Args:
            year: Year to get holidays for
            
        Returns:
            List of holiday dictionaries with name, date, and description
        """
        if not self.service or not self.api_key:
            logger.warning("Google Calendar service not configured properly")
            return []
        
        try:
            # Calculate time range for the year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            
            # Format dates for API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Call Google Calendar API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            holidays = []
            
            for event in events:
                holiday = self._parse_event_to_holiday(event)
                if holiday:
                    holidays.append(holiday)
            
            logger.info(f"Retrieved {len(holidays)} holidays for year {year}")
            return holidays
            
        except HttpError as error:
            logger.error(f"An error occurred while fetching holidays: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching holidays: {e}")
            return []
    
    def _parse_event_to_holiday(self, event: Dict) -> Optional[Dict]:
        """
        Parse Google Calendar event to holiday format
        
        Args:
            event: Google Calendar event dictionary
            
        Returns:
            Holiday dictionary or None if parsing fails
        """
        try:
            name = event.get('summary', 'Ngày lễ')
            description = event.get('description', '')
            
            # Handle both date and dateTime formats
            start = event.get('start', {})
            if 'date' in start:
                # All-day event
                event_date = datetime.strptime(start['date'], '%Y-%m-%d').date()
            elif 'dateTime' in start:
                # Timed event
                event_date = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00')).date()
            else:
                logger.warning(f"Could not parse date from event: {event}")
                return None
            
            return {
                'name': name,
                'date': event_date,
                'description': description,
                'type': 'google_calendar',
                'date_str': event_date.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Error parsing event to holiday: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Google Calendar service is properly configured"""
        return bool(self.service and self.api_key)


# Global instance
google_calendar_service = GoogleCalendarService() 