from datetime import datetime
from .config import BotConfig

def format_date(time):
    """Форматирует дату из строки ISO, datetime объекта или None"""
    if time is None:
        return "неизвестно"
        
    try:
        if isinstance(time, str):
            dt = datetime.strptime(time, BotConfig.DATETIME_FORMAT_FROM)
        elif isinstance(time, datetime):
            dt = time
        else:
            return str(time)
            
        return dt.strftime(BotConfig.DATETIME_FORMAT_TO)
    except Exception as e:
        return f"Ошибка формата даты: {str(e)}"
