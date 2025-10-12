import asyncio
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

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: Command):
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    source = command.args

    user_data = await db.get_one_generic_async(table='users', user_id=user_id)
    
    if not user_data:
        await db.insert_async(columns=['user_id', 'username', 'first_name', 'last_name', 'source'],
                            values=[user_id, username, first_name, last_name, source], table='users')
        
    await create_topic(user_id)
    
    await send(user_id=user_id, message=message, text=f"@{username} запустил бота\nИсточник: {source}")