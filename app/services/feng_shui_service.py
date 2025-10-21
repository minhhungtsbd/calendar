from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional
from enum import Enum


class Element(Enum):
    """Ngũ hành - Five Elements"""
    WOOD = "Mộc"      # Wood
    FIRE = "Hỏa"      # Fire  
    EARTH = "Thổ"     # Earth
    METAL = "Kim"     # Metal
    WATER = "Thủy"    # Water


class FengShuiService:
    """Service for feng shui calculations based on Can Chi system"""
    
    # Thiên Can (Heavenly Stems) - 10 stems
    THIEN_CAN = [
        ("Giáp", Element.WOOD),   # 甲
        ("Ất", Element.WOOD),     # 乙
        ("Bính", Element.FIRE),   # 丙
        ("Đinh", Element.FIRE),   # 丁
        ("Mậu", Element.EARTH),   # 戊
        ("Kỷ", Element.EARTH),    # 己
        ("Canh", Element.METAL),  # 庚
        ("Tân", Element.METAL),   # 辛
        ("Nhâm", Element.WATER),  # 壬
        ("Quý", Element.WATER)    # 癸
    ]
    
    # Địa Chi (Earthly Branches) - 12 branches
    DIA_CHI = [
        ("Tý", Element.WATER, "Chuột"),    # 子
        ("Sửu", Element.EARTH, "Trâu"),    # 丑
        ("Dần", Element.WOOD, "Hổ"),      # 寅
        ("Mão", Element.WOOD, "Mèo"),     # 卯
        ("Thìn", Element.EARTH, "Rồng"),  # 辰
        ("Tỵ", Element.FIRE, "Rắn"),      # 巳
        ("Ngọ", Element.FIRE, "Ngựa"),    # 午
        ("Mùi", Element.EARTH, "Dê"),     # 未
        ("Thân", Element.METAL, "Khỉ"),   # 申
        ("Dậu", Element.METAL, "Gà"),     # 酉
        ("Tuất", Element.EARTH, "Chó"),   # 戌
        ("Hợi", Element.WATER, "Heo")     # 亥
    ]
    
    # Giờ hoàng đạo theo Địa Chi
    LUCKY_HOURS = {
        "Tý": ["Tý", "Sửu", "Mão", "Ngọ", "Thân", "Dậu"],
        "Sửu": ["Tý", "Sửu", "Thìn", "Mùi", "Dậu", "Tuất"],
        "Dần": ["Sửu", "Dần", "Tỵ", "Thân", "Tuất", "Hợi"],
        "Mão": ["Dần", "Mão", "Ngọ", "Dậu", "Hợi", "Tý"],
        "Thìn": ["Mão", "Thìn", "Mùi", "Tuất", "Tý", "Sửu"],
        "Tỵ": ["Thìn", "Tỵ", "Thân", "Hợi", "Sửu", "Dần"],
        "Ngọ": ["Tỵ", "Ngọ", "Dậu", "Tý", "Dần", "Mão"],
        "Mùi": ["Ngọ", "Mùi", "Tuất", "Sửu", "Mão", "Thìn"],
        "Thân": ["Mùi", "Thân", "Hợi", "Dần", "Thìn", "Tỵ"],
        "Dậu": ["Thân", "Dậu", "Tý", "Mão", "Tỵ", "Ngọ"],
        "Tuất": ["Dậu", "Tuất", "Sửu", "Thìn", "Ngọ", "Mùi"],
        "Hợi": ["Tuất", "Hợi", "Dần", "Tỵ", "Mùi", "Thân"]
    }
    
    # Màu sắc may mắn theo ngũ hành
    ELEMENT_COLORS = {
        Element.WOOD: ["Xanh lá", "Xanh lục"],
        Element.FIRE: ["Đỏ", "Cam", "Hồng"],
        Element.EARTH: ["Vàng", "Nâu", "Be"],
        Element.METAL: ["Trắng", "Bạc", "Xám"],
        Element.WATER: ["Đen", "Xanh dương", "Xanh navy"]
    }
    
    # Hướng may mắn theo Thiên Can
    THIEN_CAN_DIRECTIONS = {
        "Giáp": "Đông",
        "Ất": "Đông Nam", 
        "Bính": "Nam",
        "Đinh": "Nam",
        "Mậu": "Trung ương",
        "Kỷ": "Trung ương",
        "Canh": "Tây",
        "Tân": "Tây Nam",
        "Nhâm": "Bắc",
        "Quý": "Bắc Đông"
    }
    
    # Baseline date for Can Chi calculation (1/1/1900 = Kỷ Hợi)
    BASELINE_DATE = date(1900, 1, 1)
    BASELINE_THIEN_CAN_INDEX = 5  # Kỷ (index 5 in THIEN_CAN)
    BASELINE_DIA_CHI_INDEX = 11   # Hợi (index 11 in DIA_CHI)
    
    @staticmethod
    def calculate_can_chi(target_date: date) -> Tuple[str, str, Element, Element]:
        """
        Tính Can Chi cho một ngày cụ thể
        Returns: (thiên_can, địa_chi, thiên_can_element, địa_chi_element)
        """
        # Tính số ngày từ baseline
        days_diff = (target_date - FengShuiService.BASELINE_DATE).days
        
        # Tính Thiên Can (chu kỳ 10 ngày)
        thien_can_index = (FengShuiService.BASELINE_THIEN_CAN_INDEX + days_diff) % 10
        thien_can_name, thien_can_element = FengShuiService.THIEN_CAN[thien_can_index]
        
        # Tính Địa Chi (chu kỳ 12 ngày)
        dia_chi_index = (FengShuiService.BASELINE_DIA_CHI_INDEX + days_diff) % 12
        dia_chi_name, dia_chi_element, zodiac = FengShuiService.DIA_CHI[dia_chi_index]
        
        return thien_can_name, dia_chi_name, thien_can_element, dia_chi_element
    
    @staticmethod
    def get_birth_year_element(birth_date: date) -> Tuple[Element, str]:
        """
        Tính ngũ hành năm sinh (Nạp Âm)
        Returns: (element, description)
        """
        year = birth_date.year
        
        # Bảng Nạp Âm chính xác theo phong thủy truyền thống
        # Mỗi cặp Can Chi có cùng mệnh, chu kỳ 60 năm
        nap_am_table = {
            # 1924-1925: Giáp Tý, Ất Sửu
            1924: (Element.METAL, "Kim hải trung"),
            1925: (Element.METAL, "Kim hải trung"),
            # 1926-1927: Bính Dần, Đinh Mão  
            1926: (Element.FIRE, "Hỏa lư trung"),
            1927: (Element.FIRE, "Hỏa lư trung"),
            # 1928-1929: Mậu Thìn, Kỷ Tỵ
            1928: (Element.EARTH, "Thổ thành đầu"),
            1929: (Element.EARTH, "Thổ thành đầu"),
            # 1930-1931: Canh Ngọ, Tân Mùi
            1930: (Element.METAL, "Kim bạch lạp"),
            1931: (Element.METAL, "Kim bạch lạp"),
            # 1932-1933: Nhâm Thân, Quý Dậu
            1932: (Element.WATER, "Thủy dương liễu"),
            1933: (Element.WATER, "Thủy dương liễu"),
            # 1934-1935: Giáp Tuất, Ất Hợi
            1934: (Element.FIRE, "Hỏa sơn đầu"),
            1935: (Element.FIRE, "Hỏa sơn đầu"),
            # 1936-1937: Bính Tý, Đinh Sửu
            1936: (Element.EARTH, "Thổ ốc trung"),
            1937: (Element.EARTH, "Thổ ốc trung"),
            # 1938-1939: Mậu Dần, Kỷ Mão
            1938: (Element.METAL, "Kim sa trung"),
            1939: (Element.METAL, "Kim sa trung"),
            # 1940-1941: Canh Thìn, Tân Tỵ
            1940: (Element.EARTH, "Thổ lộ bàng"),
            1941: (Element.EARTH, "Thổ lộ bàng"),
            # 1942-1943: Nhâm Ngọ, Quý Mùi
            1942: (Element.METAL, "Kim kim bạc"),
            1943: (Element.METAL, "Kim kim bạc"),
            # 1944-1945: Giáp Thân, Ất Dậu
            1944: (Element.WATER, "Thủy tuyền trung"),
            1945: (Element.WATER, "Thủy tuyền trung"),
            # 1946-1947: Bính Tuất, Đinh Hợi
            1946: (Element.FIRE, "Hỏa sơn hạ"),
            1947: (Element.FIRE, "Hỏa sơn hạ"),
            # 1948-1949: Mậu Tý, Kỷ Sửu
            1948: (Element.EARTH, "Thổ tích lịch"),
            1949: (Element.EARTH, "Thổ tích lịch"),
            # 1950-1951: Canh Dần, Tân Mão
            1950: (Element.WOOD, "Mộc thành đầu"),
            1951: (Element.WOOD, "Mộc thành đầu"),
            # 1952-1953: Nhâm Thìn, Quý Tỵ
            1952: (Element.WATER, "Thủy trường lưu"),
            1953: (Element.WATER, "Thủy trường lưu"),
            # 1954-1955: Giáp Ngọ, Ất Mùi
            1954: (Element.FIRE, "Hỏa sa trung"),
            1955: (Element.FIRE, "Hỏa sa trung"),
            # 1956-1957: Bính Thân, Đinh Dậu
            1956: (Element.FIRE, "Hỏa sơn hạ"),
            1957: (Element.FIRE, "Hỏa sơn hạ"),
            # 1958-1959: Mậu Tuất, Kỷ Hợi
            1958: (Element.WOOD, "Mộc bình địa"),
            1959: (Element.WOOD, "Mộc bình địa"),
            # 1960-1961: Canh Tý, Tân Sửu
            1960: (Element.EARTH, "Thổ tích lịch"),
            1961: (Element.EARTH, "Thổ tích lịch"),
            # 1962-1963: Nhâm Dần, Quý Mão
            1962: (Element.METAL, "Kim kim bạc"),
            1963: (Element.METAL, "Kim kim bạc"),
            # 1964-1965: Giáp Thìn, Ất Tỵ
            1964: (Element.FIRE, "Hỏa phúc đăng"),
            1965: (Element.FIRE, "Hỏa phúc đăng"),
            # 1966-1967: Bính Ngọ, Đinh Mùi
            1966: (Element.WATER, "Thủy thiên hà"),
            1967: (Element.WATER, "Thủy thiên hà"),
            # 1968-1969: Mậu Thân, Kỷ Dậu
            1968: (Element.EARTH, "Thổ đại trạch"),
            1969: (Element.EARTH, "Thổ đại trạch"),
            # 1970-1971: Canh Tuất, Tân Hợi
            1970: (Element.METAL, "Kim thoa xuyến"),
            1971: (Element.METAL, "Kim thoa xuyến"),
            # 1972-1973: Nhâm Tý, Quý Sửu
            1972: (Element.WOOD, "Mộc tang đố"),
            1973: (Element.WOOD, "Mộc tang đố"),
            # 1974-1975: Giáp Dần, Ất Mão
            1974: (Element.WATER, "Thủy đại khê"),
            1975: (Element.WATER, "Thủy đại khê"),
            # 1976-1977: Bính Thìn, Đinh Tỵ
            1976: (Element.EARTH, "Thổ sa trung"),
            1977: (Element.EARTH, "Thổ sa trung"),
            # 1978-1979: Mậu Ngọ, Kỷ Mùi
            1978: (Element.FIRE, "Hỏa thiên thượng"),
            1979: (Element.FIRE, "Hỏa thiên thượng"),
            # 1980-1981: Canh Thân, Tân Dậu
            1980: (Element.WOOD, "Mộc thạch lựu"),
            1981: (Element.WOOD, "Mộc thạch lựu"),
            # 1982-1983: Nhâm Tuất, Quý Hợi
            1982: (Element.WATER, "Thủy đại hải"),
            1983: (Element.WATER, "Thủy đại hải"),
            # 1984-1985: Giáp Tý, Ất Sửu (chu kỳ mới)
            1984: (Element.METAL, "Kim hải trung"),
            1985: (Element.METAL, "Kim hải trung"),
            # 1986-1987: Bính Dần, Đinh Mão
            1986: (Element.FIRE, "Hỏa lư trung"),
            1987: (Element.FIRE, "Hỏa lư trung"),
            # 1988-1989: Mậu Thìn, Kỷ Tỵ
            1988: (Element.EARTH, "Thổ thành đầu"),
            1989: (Element.EARTH, "Thổ thành đầu"),
            # 1990-1991: Canh Ngọ, Tân Mùi
            1990: (Element.METAL, "Kim bạch lạp"),
            1991: (Element.METAL, "Kim bạch lạp"),
            # 1992-1993: Nhâm Thân, Quý Dậu - QUAN TRỌNG!
            1992: (Element.METAL, "Kim kiếm phong"),
            1993: (Element.METAL, "Kim kiếm phong"),
            # 1994-1995: Giáp Tuất, Ất Hợi
            1994: (Element.FIRE, "Hỏa sơn đầu"),
            1995: (Element.FIRE, "Hỏa sơn đầu"),
            # 1996-1997: Bính Tý, Đinh Sửu
            1996: (Element.EARTH, "Thổ ốc trung"),
            1997: (Element.EARTH, "Thổ ốc trung"),
            # 1998-1999: Mậu Dần, Kỷ Mão
            1998: (Element.METAL, "Kim sa trung"),
            1999: (Element.METAL, "Kim sa trung"),
            # 2000-2001: Canh Thìn, Tân Tỵ
            2000: (Element.EARTH, "Thổ lộ bàng"),
            2001: (Element.EARTH, "Thổ lộ bàng"),
            # 2002-2003: Nhâm Ngọ, Quý Mùi
            2002: (Element.METAL, "Kim kim bạc"),
            2003: (Element.METAL, "Kim kim bạc"),
            # 2004-2005: Giáp Thân, Ất Dậu
            2004: (Element.WATER, "Thủy tuyền trung"),
            2005: (Element.WATER, "Thủy tuyền trung"),
            # 2006-2007: Bính Tuất, Đinh Hợi
            2006: (Element.FIRE, "Hỏa sơn hạ"),
            2007: (Element.FIRE, "Hỏa sơn hạ"),
            # 2008-2009: Mậu Tý, Kỷ Sửu
            2008: (Element.EARTH, "Thổ tích lịch"),
            2009: (Element.EARTH, "Thổ tích lịch"),
            # 2010-2011: Canh Dần, Tân Mão
            2010: (Element.WOOD, "Mộc thành đầu"),
            2011: (Element.WOOD, "Mộc thành đầu"),
            # 2012-2013: Nhâm Thìn, Quý Tỵ
            2012: (Element.WATER, "Thủy trường lưu"),
            2013: (Element.WATER, "Thủy trường lưu"),
            # 2014-2015: Giáp Ngọ, Ất Mùi
            2014: (Element.FIRE, "Hỏa sa trung"),
            2015: (Element.FIRE, "Hỏa sa trung"),
            # 2016-2017: Bính Thân, Đinh Dậu
            2016: (Element.FIRE, "Hỏa sơn hạ"),
            2017: (Element.FIRE, "Hỏa sơn hạ"),
            # 2018-2019: Mậu Tuất, Kỷ Hợi
            2018: (Element.WOOD, "Mộc bình địa"),
            2019: (Element.WOOD, "Mộc bình địa"),
            # 2020-2021: Canh Tý, Tân Sửu
            2020: (Element.EARTH, "Thổ tích lịch"),
            2021: (Element.EARTH, "Thổ tích lịch"),
            # 2022-2023: Nhâm Dần, Quý Mão
            2022: (Element.METAL, "Kim kim bạc"),
            2023: (Element.METAL, "Kim kim bạc"),
            # 2024-2025: Giáp Thìn, Ất Tỵ
            2024: (Element.FIRE, "Hỏa phúc đăng"),
            2025: (Element.FIRE, "Hỏa phúc đăng"),
        }
        
        # Tra bảng trực tiếp
        if year in nap_am_table:
            return nap_am_table[year]
        
        # Nếu không có trong bảng, tính theo chu kỳ 60 năm
        cycle_year = ((year - 1924) % 60) + 1924
        if cycle_year in nap_am_table:
            return nap_am_table[cycle_year]
        
        # Fallback
        return (Element.EARTH, "Thổ")
    
    @staticmethod
    def get_birth_zodiac(birth_date: date) -> Tuple[str, Element]:
        """
        Lấy con giáp và ngũ hành năm sinh
        Returns: (zodiac_name, zodiac_element)
        """
        year = birth_date.year
        
        # Tính con giáp (chu kỳ 12 năm, bắt đầu từ Tý = 1900)
        zodiac_index = (year - 1900) % 12
        _, zodiac_element, zodiac_name = FengShuiService.DIA_CHI[zodiac_index]
        
        return zodiac_name, zodiac_element
    
    @staticmethod
    def calculate_compatibility_score(user_birth_date: date, target_date: date, method: str = "can_chi") -> Dict:
        """
        Tính điểm tương thích giữa ngày sinh user và ngày cụ thể
        Args:
            user_birth_date: Ngày sinh user
            target_date: Ngày cần xem
            method: Phương pháp tính mệnh ("can_chi" hoặc "nap_am")
        Returns: compatibility analysis
        """
        # Lấy mệnh năm sinh của user theo phương pháp được chọn
        user_year_element, user_year_desc = FengShuiService.get_birth_year_element_by_method(user_birth_date, method)
        user_zodiac, user_zodiac_element = FengShuiService.get_birth_zodiac(user_birth_date)
        
        # Lấy ngũ hành ngày cần xem
        day_element = FengShuiService.get_daily_element(target_date)
        day_thien_can, day_dia_chi, _, day_dia_chi_element = FengShuiService.calculate_can_chi(target_date)
        
        # Tính tương thích giữa ngũ hành năm sinh và ngày
        year_day_relationships = FengShuiService.get_element_relationships(user_year_element)
        
        # Điểm tương thích cơ bản
        compatibility_score = 50  # Điểm trung bình
        compatibility_level = "Trung bình"
        
        if day_element in year_day_relationships["harmonious"]:
            compatibility_score += 30
            compatibility_level = "Tốt"
        elif day_element in year_day_relationships["conflicting"]:
            compatibility_score -= 20
            compatibility_level = "Kém"
        
        # Bonus nếu ngũ hành ngày sinh ra ngũ hành năm sinh (được hỗ trợ)
        if day_element in year_day_relationships["generated_by"]:
            compatibility_score += 20
            compatibility_level = "Rất tốt"
        
        # Penalty nếu ngũ hành ngày khắc ngũ hành năm sinh
        if day_element in year_day_relationships["destroyed_by"]:
            compatibility_score -= 30
            compatibility_level = "Rất kém"
        
        # Giới hạn điểm từ 0-100
        compatibility_score = max(0, min(100, compatibility_score))
        
        return {
            "score": compatibility_score,
            "level": compatibility_level,
            "user_year_element": user_year_element.value,
            "user_year_desc": user_year_desc,
            "user_zodiac": user_zodiac,
            "day_element": day_element.value,
            "day_can_chi": f"{day_thien_can} {day_dia_chi}",
            "analysis": FengShuiService._get_compatibility_analysis(
                user_year_element, day_element, compatibility_score
            )
        }
    
    @staticmethod
    def _get_compatibility_analysis(user_element: Element, day_element: Element, score: int) -> str:
        """Phân tích chi tiết về tương thích"""
        if score >= 80:
            return f"Ngày rất phù hợp với mệnh {user_element.value}. Đây là thời điểm tuyệt vời để thực hiện các kế hoạch quan trọng."
        elif score >= 60:
            return f"Ngày khá tốt cho mệnh {user_element.value}. Có thể tiến hành các công việc thông thường một cách thuận lợi."
        elif score >= 40:
            return f"Ngày trung bình với mệnh {user_element.value}. Nên thận trọng và cân nhắc kỹ trước khi hành động."
        else:
            return f"Ngày không thuận lợi cho mệnh {user_element.value}. Nên tránh các quyết định quan trọng và tập trung vào nghỉ ngơi."
    
    @staticmethod
    def get_personal_feng_shui_advice(user_birth_date: date, target_date: date, method: str = "can_chi") -> Dict:
        """
        Lấy lời khuyên phong thủy cá nhân cho user vào ngày cụ thể
        Args:
            user_birth_date: Ngày sinh user
            target_date: Ngày cần xem
            method: Phương pháp tính mệnh ("can_chi" hoặc "nap_am")
        """
        # Tính tương thích
        compatibility = FengShuiService.calculate_compatibility_score(user_birth_date, target_date, method)
        
        # Lấy thông tin cơ bản
        user_year_element, user_year_desc = FengShuiService.get_birth_year_element_by_method(user_birth_date, method)
        user_zodiac, user_zodiac_element = FengShuiService.get_birth_zodiac(user_birth_date)
        
        # Lấy thông tin ngày
        day_analysis = FengShuiService.get_daily_feng_shui_analysis(target_date)
        
        # Lời khuyên cá nhân hóa
        personal_activities = FengShuiService._get_personal_activities(
            user_year_element, day_analysis["element"], compatibility["score"]
        )
        
        personal_colors = FengShuiService._get_personal_colors(user_year_element, day_analysis["element"])
        
        # Kiểm tra sinh nhật
        is_birthday = (user_birth_date.month == target_date.month and 
                      user_birth_date.day == target_date.day)
        
        birthday_reminder = None
        if is_birthday:
            age = target_date.year - user_birth_date.year
            birthday_reminder = {
                "message": f"🎉 Chúc mừng sinh nhật lần thứ {age}!",
                "advice": "Đây là ngày đặc biệt của bạn. Hãy tận hưởng và làm những điều mang lại niềm vui!"
            }
        
        return {
            "compatibility": compatibility,
            "user_info": {
                "birth_year_element": user_year_element.value,
                "birth_year_desc": user_year_desc,
                "zodiac": user_zodiac,
                "zodiac_element": user_zodiac_element.value
            },
            "day_info": day_analysis,
            "personal_advice": {
                "activities": personal_activities,
                "colors": personal_colors,
                "overall_advice": FengShuiService._get_overall_advice(compatibility["score"])
            },
            "birthday_reminder": birthday_reminder
        }
    
    @staticmethod
    def _get_personal_activities(user_element: Element, day_element: Element, score: int) -> Dict:
        """Lấy hoạt động cá nhân hóa dựa trên mệnh và điểm tương thích"""
        base_activities = FengShuiService.get_lucky_activities(day_element)
        base_avoid = FengShuiService.get_unlucky_activities(day_element)
        
        # Điều chỉnh dựa trên mệnh cá nhân
        user_relationships = FengShuiService.get_element_relationships(user_element)
        
        recommended = []
        avoid = []
        
        if score >= 60:
            # Ngày tốt - khuyến khích hoạt động tích cực
            recommended.extend(base_activities[:3])
            if day_element in user_relationships["harmonious"]:
                recommended.extend([
                    "Thực hiện các kế hoạch dài hạn",
                    "Gặp gỡ người quan trọng",
                    "Đầu tư tài chính"
                ])
        else:
            # Ngày kém - nên thận trọng
            recommended.extend([
                "Nghỉ ngơi, thư giãn",
                "Ôn tập kiến thức cũ",
                "Dọn dẹp, sắp xếp"
            ])
            avoid.extend(base_avoid[:2])
            avoid.extend([
                "Ký hợp đồng quan trọng",
                "Bắt đầu dự án mới",
                "Đầu tư lớn"
            ])
        
        return {
            "recommended": recommended,
            "avoid": avoid
        }
    
    @staticmethod
    def _get_personal_colors(user_element: Element, day_element: Element) -> List[str]:
        """Lấy màu sắc may mắn cá nhân"""
        user_colors = FengShuiService.ELEMENT_COLORS[user_element]
        day_colors = FengShuiService.ELEMENT_COLORS[day_element]
        
        # Kết hợp màu của mệnh cá nhân và ngày
        personal_colors = list(set(user_colors + day_colors))
        
        return personal_colors[:4]  # Giới hạn 4 màu
    
    @staticmethod
    def _get_overall_advice(score: int) -> str:
        """Lời khuyên tổng quan dựa trên điểm tương thích"""
        if score >= 80:
            return "Đây là ngày tuyệt vời cho bạn! Hãy tận dụng cơ hội và thực hiện những kế hoạch quan trọng."
        elif score >= 60:
            return "Ngày khá thuận lợi. Bạn có thể tiến hành các công việc thông thường một cách tự tin."
        elif score >= 40:
            return "Ngày bình thường. Hãy thận trọng và cân nhắc kỹ trước khi đưa ra quyết định quan trọng."
        else:
            return "Ngày không thuận lợi. Nên tập trung vào nghỉ ngơi và tránh các quyết định quan trọng."
    
    @staticmethod
    def get_daily_element(target_date: date) -> Element:
        """Lấy ngũ hành chính của ngày (dựa trên Thiên Can)"""
        thien_can, _, thien_can_element, _ = FengShuiService.calculate_can_chi(target_date)
        return thien_can_element
    
    @staticmethod
    def get_element_relationships(element: Element) -> Dict[str, List[Element]]:
        """
        Lấy mối quan hệ tương sinh và tương khắc của một ngũ hành
        """
        # Chu trình tương sinh: Mộc → Hỏa → Thổ → Kim → Thủy → Mộc
        generation_cycle = [Element.WOOD, Element.FIRE, Element.EARTH, Element.METAL, Element.WATER]
        
        # Chu trình tương khắc: Mộc → Thổ → Thủy → Hỏa → Kim → Mộc  
        destruction_cycle = [Element.WOOD, Element.EARTH, Element.WATER, Element.FIRE, Element.METAL]
        
        current_index = generation_cycle.index(element)
        
        # Tương sinh: element sinh ra gì, gì sinh ra element
        generates = generation_cycle[(current_index + 1) % 5]  # Element sinh ra
        generated_by = generation_cycle[(current_index - 1) % 5]  # Gì sinh ra element
        
        # Tương khắc: element khắc gì, gì khắc element
        current_dest_index = destruction_cycle.index(element)
        destroys = destruction_cycle[(current_dest_index + 1) % 5]  # Element khắc gì
        destroyed_by = destruction_cycle[(current_dest_index - 1) % 5]  # Gì khắc element
        
        return {
            "generates": [generates],  # Tương sinh
            "generated_by": [generated_by],
            "destroys": [destroys],  # Tương khắc
            "destroyed_by": [destroyed_by],
            "harmonious": [generated_by, generates],  # Hài hòa
            "conflicting": [destroyed_by, destroys]  # Xung khắc
        }
    
    @staticmethod
    def get_lucky_activities(element: Element) -> List[str]:
        """Lấy các hoạt động may mắn theo ngũ hành của ngày"""
        activities = {
            Element.WOOD: [
                "Trồng cây, làm vườn",
                "Học tập, đọc sách", 
                "Khởi nghiệp, bắt đầu dự án mới",
                "Gặp gỡ bạn bè, mở rộng mối quan hệ",
                "Tập thể dục, yoga"
            ],
            Element.FIRE: [
                "Tổ chức sự kiện, tiệc tùng",
                "Thuyết trình, diễn thuyết",
                "Sáng tạo nghệ thuật",
                "Kết hôn, đính hôn", 
                "Quảng cáo, marketing"
            ],
            Element.EARTH: [
                "Mua bán bất động sản",
                "Xây dựng, sửa chữa nhà cửa",
                "Đầu tư tài chính",
                "Ký hợp đồng quan trọng",
                "Tích trữ, tiết kiệm"
            ],
            Element.METAL: [
                "Cắt tóc, làm đẹp",
                "Mua sắm trang sức, đồ kim loại",
                "Phẫu thuật, điều trị y tế",
                "Tổ chức, sắp xếp công việc",
                "Đàm phán, thương lượng"
            ],
            Element.WATER: [
                "Du lịch, khám phá",
                "Tắm biển, bơi lội",
                "Thiền định, tĩnh tâm",
                "Nghiên cứu, tìm hiểu sâu",
                "Làm từ thiện, giúp đỡ người khác"
            ]
        }
        return activities.get(element, [])
    
    @staticmethod
    def get_unlucky_activities(element: Element) -> List[str]:
        """Lấy các hoạt động nên tránh theo ngũ hành của ngày"""
        relationships = FengShuiService.get_element_relationships(element)
        conflicting_elements = relationships["conflicting"]
        
        # Hoạt động nên tránh dựa trên ngũ hành xung khắc
        avoid_activities = {
            Element.WOOD: [
                "Đốn cây, phá hoại cây xanh",
                "Sử dụng nhiều đồ kim loại sắc bén",
                "Cãi vã, tranh chấp",
                "Làm việc quá sức"
            ],
            Element.FIRE: [
                "Tiếp xúc với nước lạnh",
                "Ở nơi ẩm ướt",
                "Tránh các hoạt động tĩnh lặng",
                "Không nên quá khiêm tốn"
            ],
            Element.EARTH: [
                "Trồng cây trong nhà",
                "Hoạt động ngoài trời khi có gió lớn",
                "Thay đổi đột ngột",
                "Quyết định vội vàng"
            ],
            Element.METAL: [
                "Tiếp xúc với lửa mạnh",
                "Hoạt động thể chất quá mức",
                "Cãi vã, xung đột",
                "Ăn uống cay nóng"
            ],
            Element.WATER: [
                "Ở nơi khô hanh",
                "Hoạt động dưới ánh nắng gắt",
                "Vội vàng, nóng nảy",
                "Tiêu xài hoang phí"
            ]
        }
        return avoid_activities.get(element, [])
    
    @staticmethod
    def get_lucky_hours(target_date: date) -> List[Dict]:
        """Lấy các giờ hoàng đạo trong ngày"""
        _, dia_chi, _, _ = FengShuiService.calculate_can_chi(target_date)
        lucky_hours_list = FengShuiService.LUCKY_HOURS.get(dia_chi, [])
        
        # Chuyển đổi sang giờ cụ thể
        hour_mapping = {
            "Tý": (23, 1), "Sửu": (1, 3), "Dần": (3, 5), "Mão": (5, 7),
            "Thìn": (7, 9), "Tỵ": (9, 11), "Ngọ": (11, 13), "Mùi": (13, 15),
            "Thân": (15, 17), "Dậu": (17, 19), "Tuất": (19, 21), "Hợi": (21, 23)
        }
        
        lucky_hours = []
        for hour_name in lucky_hours_list:
            start_hour, end_hour = hour_mapping[hour_name]
            lucky_hours.append({
                "name": hour_name,
                "time_range": f"{start_hour:02d}:00 - {end_hour:02d}:00",
                "description": f"Giờ {hour_name}"
            })
        
        return lucky_hours
    
    @staticmethod
    def get_conflicting_zodiacs(target_date: date) -> List[str]:
        """Lấy các con giáp xung khắc trong ngày"""
        _, dia_chi, _, _ = FengShuiService.calculate_can_chi(target_date)
        
        # Bảng xung khắc 12 con giáp
        conflict_map = {
            "Tý": ["Ngọ"],      # Chuột xung Ngựa
            "Sửu": ["Mùi"],     # Trâu xung Dê  
            "Dần": ["Thân"],    # Hổ xung Khỉ
            "Mão": ["Dậu"],     # Mèo xung Gà
            "Thìn": ["Tuất"],   # Rồng xung Chó
            "Tỵ": ["Hợi"],      # Rắn xung Heo
            "Ngọ": ["Tý"],      # Ngựa xung Chuột
            "Mùi": ["Sửu"],     # Dê xung Trâu
            "Thân": ["Dần"],    # Khỉ xung Hổ
            "Dậu": ["Mão"],     # Gà xung Mèo
            "Tuất": ["Thìn"],   # Chó xung Rồng
            "Hợi": ["Tỵ"]       # Heo xung Rắn
        }
        
        # Lấy con giáp từ Địa Chi
        zodiac_map = {chi[0]: chi[2] for chi in FengShuiService.DIA_CHI}
        conflicting_chi = conflict_map.get(dia_chi, [])
        
        return [zodiac_map[chi] for chi in conflicting_chi]
    
    @staticmethod
    def get_daily_feng_shui_analysis(target_date: date) -> Dict:
        """Phân tích phong thủy tổng quan cho một ngày"""
        thien_can, dia_chi, thien_can_element, dia_chi_element = FengShuiService.calculate_can_chi(target_date)
        
        # Lấy thông tin chi tiết
        lucky_activities = FengShuiService.get_lucky_activities(thien_can_element)
        unlucky_activities = FengShuiService.get_unlucky_activities(thien_can_element)
        lucky_hours = FengShuiService.get_lucky_hours(target_date)
        conflicting_zodiacs = FengShuiService.get_conflicting_zodiacs(target_date)
        lucky_colors = FengShuiService.ELEMENT_COLORS[thien_can_element]
        lucky_direction = FengShuiService.THIEN_CAN_DIRECTIONS.get(thien_can, "Trung ương")
        
        return {
            "date": target_date,
            "can_chi": f"{thien_can} {dia_chi}",
            "thien_can": thien_can,
            "dia_chi": dia_chi,
            "element": thien_can_element,
            "dia_chi_element": dia_chi_element,
            "lucky_activities": lucky_activities,
            "unlucky_activities": unlucky_activities,
            "lucky_hours": lucky_hours,
            "conflicting_zodiacs": conflicting_zodiacs,
            "lucky_colors": lucky_colors,
            "lucky_direction": lucky_direction
        }
    
    @staticmethod
    def get_feng_shui_summary(target_date: date) -> str:
        """Lấy tóm tắt phong thủy cho ngày (dùng cho calendar view)"""
        thien_can, dia_chi, element, _ = FengShuiService.calculate_can_chi(target_date)
        
        # Tạo summary ngắn gọn
        element_desc = {
            Element.WOOD: "Mộc - Tốt cho học tập",
            Element.FIRE: "Hỏa - Tốt cho sự kiện", 
            Element.EARTH: "Thổ - Tốt cho đầu tư",
            Element.METAL: "Kim - Tốt cho làm đẹp",
            Element.WATER: "Thủy - Tốt cho du lịch"
        }
        
        return f"{thien_can} {dia_chi} - {element_desc.get(element, element.value)}"
    
    @staticmethod
    def get_birth_year_element_by_can_chi(birth_date: date) -> Tuple[Element, str]:
        """
        Tính mệnh năm sinh theo Thiên Can (cách truyền thống)
        Can Chi năm sinh quyết định mệnh chính
        Returns: (element, description)
        """
        year = birth_date.year
        
        # Tính Can Chi của năm sinh
        # Năm 1900 = Canh Tý (Can Canh = index 6, Chi Tý = index 0)
        year_diff = year - 1900
        can_index = (6 + year_diff) % 10  # Canh = index 6 trong THIEN_CAN
        chi_index = year_diff % 12        # Tý = index 0 trong DIA_CHI
        
        can_name, can_element = FengShuiService.THIEN_CAN[can_index]
        chi_name, chi_element, zodiac = FengShuiService.DIA_CHI[chi_index]
        
        # Mệnh chính theo Thiên Can
        can_chi_name = f"{can_name} {chi_name}"
        
        # Mô tả chi tiết
        description = f"Mệnh {can_element.value} ({can_chi_name})"
        
        return can_element, description
    
    @staticmethod
    def compare_birth_year_methods(birth_date: date) -> Dict:
        """
        So sánh 2 cách tính mệnh năm sinh
        Returns: comparison of both methods
        """
        year = birth_date.year
        
        # Cách 1: Theo Can Chi (truyền thống)
        can_chi_element, can_chi_desc = FengShuiService.get_birth_year_element_by_can_chi(birth_date)
        
        # Cách 2: Theo Nạp Âm
        nap_am_element, nap_am_desc = FengShuiService.get_birth_year_element(birth_date)
        
        # Lấy thông tin Can Chi năm sinh
        year_diff = year - 1900
        can_index = (6 + year_diff) % 10
        chi_index = year_diff % 12
        can_name, _ = FengShuiService.THIEN_CAN[can_index]
        chi_name, _, zodiac = FengShuiService.DIA_CHI[chi_index]
        
        return {
            "year": year,
            "can_chi": f"{can_name} {chi_name}",
            "zodiac": zodiac,
            "method_1_can_chi": {
                "element": can_chi_element.value,
                "description": can_chi_desc,
                "explanation": f"Theo Thiên Can '{can_name}' - cách truyền thống"
            },
            "method_2_nap_am": {
                "element": nap_am_element.value, 
                "description": nap_am_desc,
                "explanation": "Theo bảng Nạp Âm 60 năm"
            },
            "recommendation": "Phong thủy truyền thống thường dùng mệnh theo Thiên Can (method_1)"
        }
    
    @staticmethod
    def get_birth_year_element_by_method(birth_date: date, method: str = "can_chi") -> Tuple[Element, str]:
        """
        Lấy mệnh năm sinh theo phương pháp được chọn
        Args:
            birth_date: Ngày sinh
            method: "can_chi" (truyền thống) hoặc "nap_am" (60 năm chu kỳ)
        Returns: (element, description)
        """
        if method == "nap_am":
            return FengShuiService.get_birth_year_element(birth_date)
        else:  # default to can_chi
            return FengShuiService.get_birth_year_element_by_can_chi(birth_date) 