from ..config import MainConfig

class StatConfig:
    INCLUDE_GENERAL: bool = MainConfig.INCLUDE_GENERAL
    LANGUAGES = [*MainConfig.LANGUAGES]
    COMMON_COLUMNS = {
        'Задачи': 'first',
        'Дата': 'max'
    }