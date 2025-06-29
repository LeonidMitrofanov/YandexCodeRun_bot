from ..config import MainConfig

class StatConfig:
    LANGUAGES = [*MainConfig.LANGUAGES, 'Общий']
    COMMON_COLUMNS = {
        'Задачи': 'first',
        'Дата': 'max'
    }