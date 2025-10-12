import re
from datetime import timedelta, datetime
from types import SimpleNamespace
from typing import Optional, List, Tuple, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from typing import Optional, List, Tuple, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import secrets
import string
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def inline_menu(**kwargs) -> InlineKeyboardMarkup:
    """
    Параметры:
    --------------------------------
    - message_markup (InlineKeyboardMarkup):
        Исходное меню сообщения, которое нужно модифицировать.
        Пример: message_markup=message.reply_markup

    - replace_text (Dict[str, str]):
        Замена подстрок в ТЕКСТЕ кнопок. Формат: {"старая_строка": "новая_строка"}
        Пример: replace_text={"🟥": "✅", "Отмена": "Закрыть"}

    - replace_data (Dict[str, str]):
        Замена подстрок в CALLBACK_DATA кнопок. Формат: {"старая_строка": "новая_строка"}
        Пример: replace_data={"show": "hide", "temp_": "perm_"}

    - remove_buttons (List[Dict[str, str]]):
        Правила для удаления кнопок. Каждое правило должно содержать ОДИН критерий:
        [
            {"text": "🚫"},                    # Точное совпадение текста
            {"callback_data": "block:"},       # callback_data начинается с...
            {"url": "https://example.com"}     # Точное совпадение URL
        ]
        Удаляются кнопки, соответствующие ЛЮБОМУ из правил.

    - line_{N} (List[Tuple[str, str]]):
        Добавляет новую строку с кнопками. Нумерация начинается с 1.
        Формат кнопки: (текст, данные), где данные - callback_data или URL.
        Пример:
        line_1=[("❤️", "like"), ("🔗", "https://example.com")]

    - width_{N} (int):
        Количество кнопок в строке для соответствующей line_{N}.
        Пример: width_1=2 → кнопки line_1 будут разделены на 2 колонки

    - merge_line_{N} (List[Tuple[str, str]]):
        Объединяет кнопки с существующей строкой номер N.
        Пример: merge_line_2=[("➕", "add")] добавит кнопки ко 2-й строке исходного меню

    - merge_width_{N} (int):
        Ширина объединенной строки после применения merge_line_{N}.
        По умолчанию: общее количество кнопок в строке.

    Возвращает:
    --------------------------------
    InlineKeyboardMarkup - модифицированную клавиатуру с объединенными элементами

    Примеры использования:
    --------------------------------
    1. Удаление кнопки и добавление новых:
    await inline_menu(
        message_markup=existing_markup,
        remove_buttons=[{"text": "⇣"}],
        line_1=[("🆕", "new_button")],
        width_1=2
    )

    2. Замена текста и данных:
    await inline_menu(
        message_markup=existing_markup,
        replace_text={"👀": "👁️"},
        replace_data={"view": "preview"},
        merge_line_1=[("✅", "confirm")],
        merge_width_1=3
    )

    3. Полная пересборка клавиатуры:
    await inline_menu(
        message_markup=existing_markup,
        remove_buttons=[{"callback_data": "old_cmd"}],
        replace_data={"edit_": "update_"},
        line_1=[("📝", "edit_text"), ("🖼", "edit_image")],
        width_1=2,
        line_2=[("🗑", "delete")],
        width_2=1
    )

    Особенности работы:
    --------------------------------
    4. Порядок обработки:
        - Удаление кнопок
        - Замена текста/данных
        - Объединение строк (merge_line)
        - Добавление новых строк (line_*)

    5. Для URL-кнопок:
        - Данные должны начинаться с http:// или https://
        - Не участвуют в замене callback_data

    6. Если исходное меню пустое или не передано:
        - Создается новая клавиатура только из line_* параметров
    """

    async def build_keyboard(buttons: List[Tuple[str, str]], row_width: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for text, data in buttons:
            if data.startswith(('http://', 'https://')):
                builder.button(text=text, url=data)
            else:
                builder.button(text=text, callback_data=data)
        builder.adjust(row_width)
        return builder.as_markup()

    replace_text = kwargs.pop('replace_text', {})
    replace_data = kwargs.pop('replace_data', {})
    remove_rules = kwargs.pop('remove_buttons', [])
    existing_markup = kwargs.pop('message_markup', None)
    combined_keyboard = []

    # Обработка существующего меню
    if existing_markup and isinstance(existing_markup, InlineKeyboardMarkup):
        for row in existing_markup.inline_keyboard:
            new_row = []
            for button in row:
                # Проверка на удаление: кнопка удаляется, только если ВСЕ критерии правила совпадают
                remove = False
                for rule in remove_rules:
                    rule_matches = True
                    if 'text' in rule and rule['text'] != button.text:
                        rule_matches = False
                    if 'callback_data' in rule and (not button.callback_data or not button.callback_data.startswith(rule['callback_data'])):
                        rule_matches = False
                    if 'url' in rule and rule['url'] != button.url:
                        rule_matches = False
                    if rule_matches:
                        remove = True
                        break
                if remove:
                    continue

                # Применяем замены
                new_text = button.text
                for old, new in replace_text.items():
                    new_text = new_text.replace(old, new)

                if button.callback_data:
                    new_data = button.callback_data
                    for old, new in replace_data.items():
                        new_data = new_data.replace(old, new)
                    new_button = InlineKeyboardButton(text=new_text, callback_data=new_data)
                elif button.url:
                    new_button = InlineKeyboardButton(text=new_text, url=button.url)
                else:
                    continue

                new_row.append(new_button)

            if new_row:
                combined_keyboard.append(new_row)

    # Добавление новых линий
    i = 1
    while True:
        line_key = f'line_{i}'
        width_key = f'width_{i}'
        buttons = kwargs.get(line_key)
        if not isinstance(buttons, list):
            break
        row_width = kwargs.get(width_key, 1)
        menu = await build_keyboard(buttons, row_width)
        combined_keyboard.extend(menu.inline_keyboard)
        i += 1

    return InlineKeyboardMarkup(inline_keyboard=combined_keyboard)


def generate_secure_uuid(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

async def hyperformula(link, capture, cap_type):
    if cap_type == 'text':
        return f'=HYPERLINK("{link}"; "{capture}")'
    elif cap_type == 'picture':
        return f'=HYPERLINK("{link}"; IMAGE("{capture}"; 2))'

def format_time(time_str):
    pattern = r'^(?:\d{2}:\d{2}|\d{4})$'
    if not re.match(pattern, time_str):
        return None

    if ':' in time_str:
        hours, minutes = map(int, time_str.split(':'))
    else:
        hours, minutes = int(time_str[:2]), int(time_str[2:])

    if 0 <= hours < 24 and 0 <= minutes < 60:
        return f"{hours:02d}:{minutes:02d}"

    return None


async def get_series(dates):
    date_objects = sorted(set(datetime.strptime(date, "%Y-%m-%d") for date in dates))
    max_streak = 1
    current_streak = 1
    for i in range(1, len(date_objects)):
        if date_objects[i] - date_objects[i - 1] == timedelta(days=1):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    dates_set = set(date_objects)
    current_day = today
    last_streak = 0
    if today in dates_set:
        while current_day in dates_set:
            last_streak += 1
            current_day -= timedelta(days=1)
    elif (today - timedelta(days=1)) in dates_set:
        current_day = today - timedelta(days=1)
        while current_day in dates_set:
            last_streak += 1
            current_day -= timedelta(days=1)
    else:
        last_streak = 0
    return SimpleNamespace(max_streak=max_streak, last_streak=last_streak)

async def keyboard_menu(**kwargs):

	#Пример
	#markup = await reply_menu(
    #line_1=(["Команда 1"], 1),
    #line_2=(["Команда 2"], 1),
    #line_3=(["Команда 3", "Команда 4", "Команда 5"], 3))

    keyboard = []

    for value in kwargs.values():
        if not isinstance(value, tuple) or len(value) != 2:
            continue
        commands, width = value

        # Разбиваем команды по ширине (width)
        for i in range(0, len(commands), width):
            row = [KeyboardButton(text=cmd) for cmd in commands[i:i + width]]
            keyboard.append(row)

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)