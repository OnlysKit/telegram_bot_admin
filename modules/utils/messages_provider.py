import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from modules.bot.bot import bot
from modules.utils import db
from modules.configs.config import SUPER_GROUP_ID, USE_SUPER_GROUP, bot_id


async def safe_send_to_topic(bot, group_id, topic_id, text, user_id=None, fallback_to_user=True):
    """
    Безопасная отправка сообщения в тему с обработкой ошибок
    
    Args:
        bot: Экземпляр бота
        group_id: ID группы
        topic_id: ID темы (может быть None)
        text: Текст сообщения
        user_id: ID пользователя для fallback
        fallback_to_user: Отправлять ли сообщение пользователю при ошибке
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    try:
        if topic_id:
            await bot.send_message(chat_id=group_id, message_thread_id=topic_id, text=text)
        else:
            await bot.send_message(chat_id=group_id, text=text)
        return True
    except Exception as e:
        error_str = str(e)
        if "Forbidden" in error_str and "kicked" in error_str:
            print(f"Бот исключен из группы {group_id}.")
        else:
            print(f"Ошибка отправки сообщения в тему {topic_id} группы {group_id}: {error_str}, user_id: {user_id}")
        
        # Fallback к пользователю
        if fallback_to_user and user_id:
            try:
                await bot.send_message(chat_id=user_id, text=text)
                print(f"Сообщение отправлено пользователю {user_id} как fallback")
                return True
            except Exception as fallback_error:
                if "Forbidden" in str(fallback_error) and "blocked" in str(fallback_error):
                    print(f"Пользователь {user_id} заблокировал бота (fallback)")
                else:
                    print(f"Ошибка fallback отправки пользователю {user_id}: {fallback_error}")
        
        return False


async def get_user_topic_id(user_id):
    """
    Получает ID темы пользователя в супергруппе
    
    Args:
        user_id: ID пользователя
    
    Returns:
        int: ID темы или None если тема не найдена
    """
    if not USE_SUPER_GROUP:
        return None
        
    try:
        user_topic_info = await db.get_one_generic_async(table='users', user_id=user_id)
        return user_topic_info['topic_id'] if user_topic_info else None
    except Exception as e:
        print(f"Ошибка получения темы пользователя {user_id}: {e}")
        return None


async def check_supergroup_access():
    """
    Проверяет доступность супергруппы
    
    Returns:
        bool: True если супергруппа доступна, False иначе
    """
    if not USE_SUPER_GROUP:
        return False
        
    try:
        chat_info = await bot.get_chat(SUPER_GROUP_ID)
        return chat_info is not None
    except Exception as e:
        print(f"Супергруппа {SUPER_GROUP_ID} недоступна: {e}")
        return False


async def send_message_to_user_topic(user_id, text, parse_mode=None, reply_markup=None, entities=None):
    """
    Отправляет сообщение в тему пользователя в супергруппе
    
    Args:
        user_id: ID пользователя
        text: Текст сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
        reply_markup: Клавиатура для сообщения
        entities: Сущности для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    if not USE_SUPER_GROUP:
        # Если супергруппа не используется, отправляем напрямую пользователю
        try:
            await bot.send_message(
                chat_id=user_id, 
                text=text, 
                parse_mode=parse_mode,
                entities=entities,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
            return False
    
    # Проверяем доступность супергруппы
    if not await check_supergroup_access():
        print(f"Супергруппа недоступна, пропускаем отправку в супергруппу для пользователя {user_id}")
        return False
    
    topic_id = await get_user_topic_id(user_id)
    
    if not topic_id:
        print(f"Тема для пользователя {user_id} не найдена")
        return False
    
    try:
        await bot.send_message(
            chat_id=SUPER_GROUP_ID,
            message_thread_id=topic_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки сообщения в тему {topic_id}: {e}")
        return False


async def send_media_to_user_topic(user_id, media_type, file_id, caption=None, reply_markup=None, entities=None):
    """
    Отправляет медиа в тему пользователя в супергруппе
    
    Args:
        user_id: ID пользователя
        media_type: Тип медиа (photo, video, document, audio, voice, video_note, sticker)
        file_id: ID файла
        caption: Подпись к медиа
        reply_markup: Клавиатура для сообщения
        entities: Сущности для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    if not USE_SUPER_GROUP:
        # Если супергруппа не используется, отправляем напрямую пользователю
        try:
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'document':
                await bot.send_document(chat_id=user_id, document=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'audio':
                await bot.send_audio(chat_id=user_id, audio=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'voice':
                await bot.send_voice(chat_id=user_id, voice=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'video_note':
                await bot.send_video_note(chat_id=user_id, video_note=file_id, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            elif media_type == 'sticker':
                await bot.send_sticker(chat_id=user_id, sticker=file_id, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
            return True
        except Exception as e:
            print(f"Ошибка отправки медиа пользователю {user_id}: {e}")
            return False
    
    # Проверяем доступность супергруппы
    if not await check_supergroup_access():
        print(f"Супергруппа недоступна, пропускаем отправку медиа в супергруппу для пользователя {user_id}")
        return False
    
    topic_id = await get_user_topic_id(user_id)
    
    if not topic_id:
        print(f"Тема для пользователя {user_id} не найдена")
        return False
    
    try:
        if media_type == 'photo':
            await bot.send_photo(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, photo=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'video':
            await bot.send_video(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, video=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'document':
            await bot.send_document(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, document=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'audio':
            await bot.send_audio(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, audio=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'voice':
            await bot.send_voice(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, voice=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'video_note':
            await bot.send_video_note(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, video_note=file_id, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        elif media_type == 'sticker':
            await bot.send_sticker(chat_id=SUPER_GROUP_ID, message_thread_id=topic_id, sticker=file_id, reply_markup=reply_markup, caption_entities=entities, parse_mode=None)
        return True
    except Exception as e:
        print(f"Ошибка отправки медиа в тему {topic_id}: {e}")
        return False


async def send_media_group_to_user_topic(user_id, media_list, reply_markup=None):
    """
    Отправляет группу медиа в тему пользователя в супергруппе
    
    Args:
        user_id: ID пользователя
        media_list: Список медиа объектов (InputMediaPhoto, InputMediaVideo, etc.)
        reply_markup: Клавиатура для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    if not USE_SUPER_GROUP:
        # Если супергруппа не используется, отправляем напрямую пользователю
        try:
            await bot.send_media_group(chat_id=user_id, media=media_list, reply_markup=reply_markup)
            return True
        except Exception as e:
            print(f"Ошибка отправки медиагруппы пользователю {user_id}: {e}")
            return False
    
    # Проверяем доступность супергруппы
    if not await check_supergroup_access():
        print(f"Супергруппа недоступна, пропускаем отправку медиагруппы в супергруппу для пользователя {user_id}")
        return False
    
    topic_id = await get_user_topic_id(user_id)
    
    if not topic_id:
        print(f"Тема для пользователя {user_id} не найдена")
        return False
    
    try:
        await bot.send_media_group(
            chat_id=SUPER_GROUP_ID,
            message_thread_id=topic_id,
            media=media_list,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки медиагруппы в тему {topic_id}: {e}")
        return False


async def forward_message_to_user_topic(user_id, from_chat_id, message_id, reply_markup=None):
    """
    Пересылает сообщение в тему пользователя в супергруппе
    
    Args:
        user_id: ID пользователя
        from_chat_id: ID чата откуда пересылаем
        message_id: ID сообщения для пересылки
        reply_markup: Клавиатура для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    if not USE_SUPER_GROUP:
        # Если супергруппа не используется, отправляем напрямую пользователю
        try:
            await bot.forward_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id
            )
            return True
        except Exception as e:
            print(f"Ошибка пересылки сообщения пользователю {user_id}: {e}")
            return False
    
    # Проверяем доступность супергруппы
    if not await check_supergroup_access():
        print(f"Супергруппа недоступна, пропускаем пересылку в супергруппу для пользователя {user_id}")
        return False
    
    topic_id = await get_user_topic_id(user_id)
    
    if not topic_id:
        print(f"Тема для пользователя {user_id} не найдена")
        return False
    
    try:
        await bot.forward_message(
            chat_id=SUPER_GROUP_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
            message_thread_id=topic_id
        )
        return True
    except Exception as e:
        print(f"Ошибка пересылки сообщения в тему {topic_id}: {e}")
        return False


async def get_user_from_topic_id(topic_id):
    """
    Получает ID пользователя по ID темы
    
    Args:
        topic_id: ID темы
    
    Returns:
        int: ID пользователя или None если пользователь не найден
    """
    try:
        user_topic_info = await db.get_one_generic_async(table='users', topic_id=topic_id)
        if user_topic_info:
            return user_topic_info['user_id']
        else:
            print(f"Пользователь для темы {topic_id} не найден в базе данных")
            return None
    except Exception as e:
        print(f"Ошибка получения пользователя по теме {topic_id}: {e}")
        return None


async def send_message_from_topic_to_user(topic_id, text, parse_mode="HTML", reply_markup=None, entities=None):
    """
    Отправляет сообщение из темы пользователю (для обработки сообщений от админов в теме)
    
    Args:
        topic_id: ID темы
        text: Текст сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
        reply_markup: Клавиатура для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    user_id = await get_user_from_topic_id(topic_id)
    
    if not user_id:
        print(f"Пользователь для темы {topic_id} не найден")
        return False
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            reply_markup=reply_markup
        )
        print(f"Сообщение из темы {topic_id} отправлено пользователю {user_id}")
        return True
    except Exception as e:
        print(f"Ошибка отправки сообщения пользователю {user_id} из темы {topic_id}: {e}")
        return False


async def send_media_from_topic_to_user(topic_id, media_type, file_id, caption=None, reply_markup=None, entities=None):
    """
    Отправляет медиа из темы пользователю (для обработки медиа от админов в теме)
    
    Args:
        topic_id: ID темы
        media_type: Тип медиа (photo, video, document, audio, voice, video_note, sticker)
        file_id: ID файла
        caption: Подпись к медиа
        reply_markup: Клавиатура для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    user_id = await get_user_from_topic_id(topic_id)
    
    if not user_id:
        print(f"Пользователь для темы {topic_id} не найден")
        return False
    
    try:
        if media_type == 'photo':
            await bot.send_photo(chat_id=user_id, photo=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'video':
            await bot.send_video(chat_id=user_id, video=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'document':
            await bot.send_document(chat_id=user_id, document=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'audio':
            await bot.send_audio(chat_id=user_id, audio=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'voice':
            await bot.send_voice(chat_id=user_id, voice=file_id, caption=caption, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'video_note':
            await bot.send_video_note(chat_id=user_id, video_note=file_id, reply_markup=reply_markup, caption_entities=entities)
        elif media_type == 'sticker':
            await bot.send_sticker(chat_id=user_id, sticker=file_id, reply_markup=reply_markup, caption_entities=entities)
        return True
    except Exception as e:
        print(f"Ошибка отправки медиа пользователю {user_id} из темы {topic_id}: {e}")
        return False


async def send_from_bot(user_id, text=None, photo=None, video=None, document=None, audio=None, voice=None, video_note=None, sticker=None, reply_markup=None, parse_mode="HTML"):
    """
    Универсальная функция для отправки сообщений в тему пользователя
    
    Args:
        user_id: ID пользователя
        text: Текст сообщения (по умолчанию None)
        photo: ID фото или объект фото
        video: ID видео или объект видео
        document: ID документа или объект документа
        audio: ID аудио или объект аудио
        voice: ID голосового сообщения или объект голосового сообщения
        video_note: ID видеосообщения или объект видеосообщения
        sticker: ID стикера или объект стикера
        reply_markup: Клавиатура для сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    
    Examples:
        # Отправка текстового сообщения
        await send_from_bot(12345, "Привет! Добро пожаловать!")
        
        # Отправка фото с подписью
        await send_from_bot(12345, photo="BAADBAADrwADBREAAYag", text="Вот мое фото!")
        
        # Отправка видео без подписи
        await send_from_bot(12345, video="BAADBAADrwADBREAAYag")
        
        # Отправка документа с подписью
        await send_from_bot(12345, document="BAADBAADrwADBREAAYag", text="Важный документ")
        
        # Отправка аудио с подписью
        await send_from_bot(12345, audio="BAADBAADrwADBREAAYag", text="Голосовое сообщение")
        
        # Отправка стикера
        await send_from_bot(12345, sticker="CAADBAADrwADBREAAYag")
        
        # Отправка с клавиатурой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Кнопка", callback_data="button")]
        ])
        await send_from_bot(12345, text="Выберите действие:", reply_markup=keyboard)
    """
    # Определяем тип контента и соответствующий file_id
    media_type = None
    file_id = None
    caption = text
    
    if photo:
        media_type = 'photo'
        file_id = photo
    elif video:
        media_type = 'video'
        file_id = video
    elif document:
        media_type = 'document'
        file_id = document
    elif audio:
        media_type = 'audio'
        file_id = audio
    elif voice:
        media_type = 'voice'
        file_id = voice
    elif video_note:
        media_type = 'video_note'
        file_id = video_note
    elif sticker:
        media_type = 'sticker'
        file_id = sticker
    
    # Если есть медиа - отправляем медиа, иначе отправляем текст
    if media_type:
        return await send_media_to_user_topic(
            user_id=user_id,
            media_type=media_type,
            file_id=file_id,
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        return await send_message_to_user_topic(
            user_id=user_id,
            text=text or "",
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )


async def send_from_topic(user_id, text=None, photo=None, video=None, document=None, audio=None, voice=None, video_note=None, sticker=None, reply_markup=None, parse_mode="HTML"):
    """
    Универсальная функция для отправки сообщений из темы пользователю
    
    Args:
        user_id: ID пользователя
        text: Текст сообщения (по умолчанию None)
        photo: ID фото или объект фото
        video: ID видео или объект видео
        document: ID документа или объект документа
        audio: ID аудио или объект аудио
        voice: ID голосового сообщения или объект голосового сообщения
        video_note: ID видеосообщения или объект видеосообщения
        sticker: ID стикера или объект стикера
        reply_markup: Клавиатура для сообщения
        parse_mode: Режим парсинга (HTML, Markdown)
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    
    Examples:
        # Отправка текстового сообщения из темы
        await send_from_topic(123, "Ответ от поддержки")
        
        # Отправка фото из темы с подписью
        await send_from_topic(123, photo="BAADBAADrwADBREAAYag", text="Вот ответ на твой вопрос")
        
        # Отправка видео из темы
        await send_from_topic(123, video="BAADBAADrwADBREAAYag")
        
        # Отправка документа из темы с подписью
        await send_from_topic(123, document="BAADBAADrwADBREAAYag", text="Инструкция по использованию")
        
        # Отправка аудио из темы
        await send_from_topic(123, audio="BAADBAADrwADBREAAYag", text="Голосовое объяснение")
        
        # Отправка стикера из темы
        await send_from_topic(123, sticker="CAADBAADrwADBREAAYag")
        
        # Отправка с клавиатурой из темы
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Понятно", callback_data="understood")]
        ])
        await send_from_topic(123, text="Понятно ли объяснение?", reply_markup=keyboard)
    """
    # Определяем тип контента и соответствующий file_id
    media_type = None
    file_id = None
    caption = text
    
    user_info = await db.get_one_generic_async(table='users', user_id=user_id)
    topic_id = user_info['topic_id']
    
    if photo:
        media_type = 'photo'
        file_id = photo
    elif video:
        media_type = 'video'
        file_id = video
    elif document:
        media_type = 'document'
        file_id = document
    elif audio:
        media_type = 'audio'
        file_id = audio
    elif voice:
        media_type = 'voice'
        file_id = voice
    elif video_note:
        media_type = 'video_note'
        file_id = video_note
    elif sticker:
        media_type = 'sticker'
        file_id = sticker
    
    # Если есть медиа - отправляем медиа, иначе отправляем текст
    if media_type:
        return await send_media_from_topic_to_user(
            topic_id=topic_id,
            media_type=media_type,
            file_id=file_id,
            caption=caption,
            reply_markup=reply_markup
        )
    else:
        return await send_message_from_topic_to_user(
            topic_id=topic_id,
            text=text or "",
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )


async def send_to_supergroup(user_id, text, reply_markup=None, entities=None):
    """
    Отправляет сообщение в супергруппу (в тему пользователя)
    
    Args:
        user_id: ID пользователя
        text: Текст сообщения
        reply_markup: Клавиатура для сообщения
        entities: Сущности для сообщения
    
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    """
    return await send_message_to_user_topic(
        user_id=user_id,
        text=text,
        entities=entities,
        reply_markup=reply_markup
    )


async def send(user_id, message, text=None, reply_markup=None, entities=None):
    """
    Универсальная функция для проксирования сообщений между ботом и темой пользователя
    Автоматически определяет источник сообщения и направляет его в нужное место
    
    Args:
        user_id: ID пользователя
        message: Объект сообщения (Message) или строка с текстом
        reply_markup: Клавиатура для сообщения
        entities: Сущности для сообщения
    Returns:
        bool: True если сообщение отправлено успешно, False иначе
    
    Logic:
        - Если сообщение из группы (supergroup) -> отправляем пользователю в бота
        - Если сообщение от пользователя -> отправляем в его тему в группе
    
    Examples:
        # Отправка текстового сообщения
        await send(12345, "Привет!")
        
        # Отправка объекта сообщения (автоматически определит источник и тип)
        await send(12345, message_object)
        
        # Отправка с клавиатурой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Кнопка", callback_data="button")]
        ])
        await send(12345, "Выберите действие:", reply_markup=keyboard)
    """
    
    if user_id == bot_id:
        return
    
    # Если передан объект Message
    if hasattr(message, 'content_type'):
        content_type = message.content_type
        entities = message.entities
        
        if not text:
            text = message.caption if message.caption else message.text
        
        # Определяем источник сообщения
        is_from_group = message.chat.type == "supergroup"
        
        if content_type == 'text':
            if is_from_group:
                # Сообщение из группы -> отправляем пользователю
                return await send_message_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    text=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                # Сообщение от пользователя -> отправляем в тему
                return await send_message_to_user_topic(
                    user_id=user_id,
                    text=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'photo':
            file_id = message.photo[-1].file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='photo',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='photo',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'video':
            file_id = message.video.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='video',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='video',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'document':
            file_id = message.document.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='document',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='document',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'audio':
            file_id = message.audio.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='audio',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='audio',
                    file_id=file_id,
                    caption=text,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'voice':
            file_id = message.voice.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='voice',
                    file_id=file_id,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='voice',
                    file_id=file_id,
                    caption=text,
                    reply_markup=reply_markup
                )
        elif content_type == 'video_note':
            file_id = message.video_note.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='video_note',
                    file_id=file_id,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='video_note',
                    file_id=file_id,
                    entities=entities,
                    reply_markup=reply_markup
                )
        elif content_type == 'sticker':
            file_id = message.sticker.file_id
            if is_from_group:
                return await send_media_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    media_type='sticker',
                    file_id=file_id,
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_media_to_user_topic(
                    user_id=user_id,
                    media_type='sticker',
                    file_id=file_id,
                    entities=entities,
                    reply_markup=reply_markup
                )
        else:
            # Для неизвестных типов отправляем как текст
            if is_from_group:
                return await send_message_from_topic_to_user(
                    topic_id=message.message_thread_id,
                    text=text or "Неподдерживаемый тип сообщения",
                    entities=entities,
                    reply_markup=reply_markup
                )
            else:
                return await send_message_to_user_topic(
                    user_id=user_id,
                    text=text or "Неподдерживаемый тип сообщения",
                    entities=entities,
                    reply_markup=reply_markup
                )
    
    # Если передана строка - всегда отправляем в тему пользователя
    elif isinstance(message, str):
        return await send_message_to_user_topic(
            user_id=user_id,
            text=message,
            entities=entities,
            reply_markup=reply_markup
        )
    
    else:
        print(f"Неподдерживаемый тип сообщения: {type(message)}")
        return False
