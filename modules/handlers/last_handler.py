from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from modules.bot.bot import bot
from modules.utils import db
from modules.utils.bot_fn import inline_menu
from modules.configs.config import SUPER_GROUP_ID
from modules.utils.messages_provider import send
from modules.utils.topic_creator import create_topic

router = Router()

# Обработчик всех сообщений, которые не попали в другие обработчики
@router.message()
async def handle_all_messages(message: types.Message):
    
    user_id = message.from_user.id
    await send(user_id=user_id, message=message)