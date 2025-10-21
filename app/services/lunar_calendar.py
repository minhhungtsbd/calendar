from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
from lunardate import LunarDate
import calendar


class LunarCalendarService:
    """Service for handling lunar calendar conversions and operations"""
    
    @staticmethod
    def solar_to_lunar(solar_date: date) -> LunarDate:
        """Convert solar date to lunar date"""
        return LunarDate.fromSolarDate(solar_date.year, solar_date.month, solar_date.day)
    
    @staticmethod
    def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool = False) -> date:
        """Convert lunar date to solar date"""
        lunar_date = LunarDate(lunar_year, lunar_month, lunar_day, is_leap)
        return lunar_date.toSolarDate()
    
    @staticmethod
    def get_lunar_info(solar_date: date) -> Dict:
        """Get detailed lunar information for a solar date"""
        lunar_date = LunarCalendarService.solar_to_lunar(solar_date)
        
        return {
            "solar_date": solar_date,
            "lunar_year": lunar_date.year,
            "lunar_month": lunar_date.month,
            "lunar_day": lunar_date.day,
            "is_leap_month": lunar_date.isLeapMonth,
            "lunar_date_str": f"{lunar_date.day}/{lunar_date.month}/{lunar_date.year}",
            "lunar_date_vietnamese": LunarCalendarService.format_vietnamese_lunar_date(lunar_date)
        }
    
    @staticmethod
    def format_vietnamese_lunar_date(lunar_date: LunarDate) -> str:
        """Format lunar date in Vietnamese style"""
        day_str = f"ngày {lunar_date.day}"
        month_str = f"tháng {lunar_date.month}"
        if lunar_date.isLeapMonth:
            month_str = f"tháng nhuận {lunar_date.month}"
        year_str = f"năm {lunar_date.year}"
        
        return f"{day_str} {month_str} {year_str}"
    
    @staticmethod
    def get_month_calendar(year: int, month: int, focused_date: date = None) -> List[List[Dict]]:
        """Get calendar matrix for a month with both solar and lunar dates"""
        # Get first day of month and number of days
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get first Monday of the calendar view
        start_date = first_day - timedelta(days=first_day.weekday())
        
        # Use focused_date if provided, otherwise use today
        highlight_date = focused_date if focused_date else date.today()
        
        # Create 6 weeks calendar
        calendar_weeks = []
        current_date = start_date
        
        for week in range(6):
            week_days = []
            for day in range(7):
                lunar_info = LunarCalendarService.get_lunar_info(current_date)
                day_info = {
                    "date": current_date,
                    "day": current_date.day,
                    "is_current_month": current_date.month == month,
                    "is_today": current_date == date.today(),  # Real today for reference
                    "is_focused": current_date == highlight_date,  # Focused/highlighted date
                    "lunar_day": lunar_info["lunar_day"],
                    "lunar_month": lunar_info["lunar_month"],
                    "lunar_date_str": lunar_info["lunar_date_str"],
                    "is_leap_month": lunar_info["is_leap_month"]
                }
                week_days.append(day_info)
                current_date += timedelta(days=1)
            
            calendar_weeks.append(week_days)
            
            # Stop if we've passed the current month and have at least 4 weeks
            if week >= 3 and current_date > last_day:
                break
        
        return calendar_weeks
    
    @staticmethod
    def get_lunar_holidays(year: int) -> List[Dict]:
        """Get list of important lunar holidays for a year"""
        holidays = [
            {"name": "Tết Nguyên Đán", "lunar_month": 1, "lunar_day": 1},
            {"name": "Rằm tháng Giêng", "lunar_month": 1, "lunar_day": 15},
            {"name": "Tết Hàn Thực", "lunar_month": 3, "lunar_day": 3},
            {"name": "Phật Đản", "lunar_month": 4, "lunar_day": 8},
            {"name": "Tết Đoan Ngọ", "lunar_month": 5, "lunar_day": 5},
            {"name": "Vu Lan", "lunar_month": 7, "lunar_day": 15},
            {"name": "Tết Trung Thu", "lunar_month": 8, "lunar_day": 15},
            {"name": "Tết Trùng Cửu", "lunar_month": 9, "lunar_day": 9},
            {"name": "Tết Hạ Nguyên", "lunar_month": 10, "lunar_day": 15},
        ]
        
        result = []
        for holiday in holidays:
            try:
                solar_date = LunarCalendarService.lunar_to_solar(
                    year, holiday["lunar_month"], holiday["lunar_day"]
                )
                result.append({
                    "name": holiday["name"],
                    "solar_date": solar_date,
                    "lunar_date": f"{holiday['lunar_day']}/{holiday['lunar_month']}/{year}"
                })
            except:
                # Skip if conversion fails
                continue
        
        return result
