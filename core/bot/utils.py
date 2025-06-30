from datetime import datetime
import numpy as np
from .config import BotConfig

def format_date(dt) -> str:
    """Форматирует дату в строку по заданному формату.
    
    Поддерживает:
    - datetime.datetime
    - numpy.datetime64
    - pandas.Timestamp
    
    Args:
        dt: Объект даты/времени
        
    Returns:
        Строка с датой в формате BotConfig.DATETIME_FORMAT
        или сообщение об ошибке.
    """
    if dt is None:
        return "неизвестно"
    
    try:
        # Преобразуем numpy.datetime64 в datetime
        if isinstance(dt, np.datetime64):
            dt = dt.astype(datetime)
        
        # Проверяем, что объект поддерживает strftime
        if hasattr(dt, 'strftime'):
            return dt.strftime(BotConfig.DATETIME_FORMAT)
        else:
            return f"Неподдерживаемый тип даты: {type(dt)}"
            
    except Exception as e:
        return f"Ошибка форматирования: {str(e)}"