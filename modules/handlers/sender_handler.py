from aiogram import Router
from aiogram import F
from aiogram.types import Message
from modules.utils.messages_provider import send

router = Router()

@router.message(F.photo | F.document | F.audio | F.voice | F.video | F.video_note | F.text | F.sticker)
async def handle_media_or_text(message: Message):
    
    # Отправляем сообщение в тему пользователя или пользователю в бота из темы
    await send(user_id=message.from_user.id, message=message)