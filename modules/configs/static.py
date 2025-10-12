# Определение категорий для отчетов
REPORT_CATEGORIES = [
    ("Еда", "eat_category"),
    ("Тренировка", "training_category"),
    ("Замер", "checkout_category"),
    ("Анализ", "analyse_category"),
    ("Бады | Лекарства", "medicine_category"),
    ("Вредная привычка", "badtips_category"),
    ("Вода | Напитки", "drinks_category"),
    ("Режим сна", "sleep_category"),
]

# Словарь для маппинга внутренних ключей на внешние названия
CATEGORY_DISPLAY_NAMES = {key: name for name, key in REPORT_CATEGORIES}

# Количество отображаемых юзеров в /members
PAGE_SIZE = 10