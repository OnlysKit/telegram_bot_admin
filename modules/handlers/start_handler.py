import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, menu_button, FSInputFile
from modules.bot.bot import bot
from modules.utils import db
from modules.utils.bot_fn import inline_menu
from modules.configs.config import SUPER_GROUP_ID
from modules.utils.messages_provider import send, send_to_supergroup
from modules.utils.topic_creator import create_topic

router = Router()

# Пример ссылки:
# https://t.me/EasyDayBot?start=p-manual_s-google
# получится product = manual, source = google

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: Command):
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    link_args = command.args
    
    source = None
    product = None
    
    if link_args:
        
        params = link_args.split('_')
        
        for param in params:
            key, value = param.split('-')
            if key == 's':
                source = value
            elif key == 'p':
                product = value

    user_data = await db.get_one_generic_async(table='users', user_id=user_id)
    
    if not user_data:
        await db.insert_async(columns=['user_id', 'username', 'first_name', 'last_name', 'source'],
                            values=[user_id, username, first_name, last_name, source], table='users')
        
    await create_topic(user_id)
    await send_to_supergroup(user_id=user_id, text=f"@{username} запустил бота\nИсточник: #{source}\nПродукт: #{product}")
    
    product_link = product if product else 'main'
    product_data = await db.get_one_generic_async(table='products', link=product_link)
    
    product_id = product_data['id']
    product_title = product_data['title']
    product_description = product_data['description']
    product_image = product_data['image']
    product_video = product_data['video']
    product_is_free = product_data['is_free']
    product_price = product_data['price']
    product_discount = product_data['discount']
    unique_product_id = product_data['unique_product_id']
    
    purchased_data = await db.get_one_generic_async(table='purchased', user_id=user_id, product_id=product_id)
    
    menu_button = "Скачать"
    menu_callback = "download"
    
    end_price = int(product_price-(product_price/100*product_discount))
    product_is_free = product_is_free if product_is_free or end_price<=0 else False
    
    text = ""
    
    text += f"<b>{product_title}</b>"
    
    if product_description:
        text += f"\n\n<i>{product_description}</i>"
    
    if not product_is_free and not purchased_data:
        text += f"\n\n<b>Стоимость:</b> <i>{end_price} руб.</i>"
        menu_button = "Оплатить и скачать"
        menu_callback = "pay"
    
    markup = await inline_menu(line_1=[(menu_button, f'{menu_callback}:{product_id}')], width_1=1)

    if not product_image and not product_video:
        message_to_user = await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
        
    else:
        
        try:
            if product_image:
                file_path = f"products/{unique_product_id}/media/photos/image.jpg"
                media_file = FSInputFile(file_path)
                message_to_user = await bot.send_photo(chat_id=user_id, photo=media_file, caption=text, reply_markup=markup)
            
            elif product_video:
                file_path = f"products/{unique_product_id}/media/video.mp4"
                media_file = FSInputFile(file_path)
                message_to_user = await bot.send_video(chat_id=user_id, video=media_file, caption=text, reply_markup=markup)
        except: 
            # На всякий случай
            message_to_user = await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
    
    await send_to_supergroup(user_id=user_id, text=f"Отправлено сообщение пользователю: {product_title}")