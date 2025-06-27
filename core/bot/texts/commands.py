class CommandTexts:
    COMMANDS_LIST = (
        "/user <ник> - информация о пользователе\n"
        "/task <номер> - статистика по задаче\n"
        "/help - справка по командам"
    )
    
    HELP = f"Вот что я умею:\n{COMMANDS_LIST}"
    START = f"Привет! Я бот для анализа данных. \n{HELP}"