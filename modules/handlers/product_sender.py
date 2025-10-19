from aiogram import Router
from aiogram import F
from aiogram.types import Message, FSInputFile
import os
from modules.utils.bot_fn import inline_menu, tg_hyperlink
from modules.utils.messages_provider import send
from modules.bot.bot import bot
from modules.utils import db
from modules.utils.payment import yoomoney_pay, yoomoney_pay_check

router = Router()

async def send_media_file(user_id, file_path, file_type, caption=None):
    """
    Отправляет медиа файл пользователю через FSInputFile
    """
    if not os.path.exists(file_path):
        message_to_user = await bot.send_message(chat_id=user_id, text="Файл не найден. Мы уже работаем над этим")
        await send(user_id, message=message_to_user)
        return False
    
    try:
        media_file = FSInputFile(file_path)
        
        if file_type == 'photo':
            message_to_user = await bot.send_photo(chat_id=user_id, photo=media_file, caption=caption)
            await send(user_id, message=message_to_user)
        elif file_type == 'video':
            message_to_user = await bot.send_video(chat_id=user_id, video=media_file, caption=caption)
            await send(user_id, message=message_to_user)
        elif file_type == 'audio':
            message_to_user = await bot.send_audio(chat_id=user_id, audio=media_file, caption=caption)
            await send(user_id, message=message_to_user)
        else:  # document или любой другой тип
            message_to_user = await bot.send_document(chat_id=user_id, document=media_file, caption=caption)
            await send(user_id, message=message_to_user)
        
        return True
    except Exception as e:
        message_to_user = await bot.send_message(chat_id=user_id, text=f"Ошибка при отправке файла. Мы уже работаем на этим")
        await send(user_id, message=message_to_user)
        return False

async def send_product(user_id, product_id, caption=None):
    product_data = await db.get_one_generic_async(table='products', id=product_id)
    unique_product_id = product_data['unique_product_id']
    file_type = product_data['file_type']
    product_title = product_data['title']
    file_title = product_data['file_title']
    paid_caption = product_data['paid_caption']
    
    if not caption:
        
        caption = paid_caption if paid_caption else f"<b>{product_title}</b>"
    
    # Путь к файлу продукта (используем path из БД)
    file_path = f"products/{unique_product_id}/files/{file_title}"
    
    # Отправляем файл продукта
    if os.path.exists(file_path):
        await send_media_file(user_id, file_path, file_type, caption)
    else:
        message_to_user = await bot.send_message(chat_id=user_id, text=f"Файл не найден. Мы уже работаем над этим")
        await send(user_id, message=message_to_user)

@router.callback_query(F.data.startswith(("pay:", "download:")))
async def handle_pay(message: Message):
    
    user_id = message.from_user.id
    
    action = message.data.split(":")[0]
    product_id = message.data.split(":")[1]
    
    product_data = await db.get_one_generic_async(table='products', id=product_id)
    
    if not product_data:
        await message.answer("Продукт не найден")
        return
    
    markup = None
    
    product_price = product_data['price']
    product_discount = product_data['discount']
    product_title = product_data['title']
    product_is_free = product_data['is_free']
    
    end_price = int(product_price-(product_price/100*product_discount))
    product_is_free = product_is_free if product_is_free or end_price<=0 else False
    
    if action == "pay" and not product_is_free:
        
        payment_data = yoomoney_pay(end_price, product_title)
        confirmation_url = payment_data['confirmation_url']
        hyperlink = await tg_hyperlink(confirmation_url, str(confirmation_url)[8:])
        payment_id = payment_data['payment_id']
        
        markup = await inline_menu(line_1=[(f"Перейти 🔗", confirmation_url)], width_1=2,
                                   line_2=[(f"Проверить оплату ✔", f'check_pay:{payment_id}:{product_id}')], width_2=1)
        text = f"⬇️ <b>Перейдите по ссылке для покупки</b> ⬇️\n\n<i>{hyperlink}</i>"
        
        message_to_user = await bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
        await send(user_id, message=message_to_user)
        
        purchased_data = await db.get_one_generic_async(table='purchased', user_id=user_id, product_id=product_id)
        if not purchased_data:
            await db.insert_async(['product_id', 'user_id', 'step', 'paid'], [product_id, user_id, 'create_link', 0], table='purchased')
        
    else:
        await send_product(user_id=user_id, product_id=product_id)
        
        
@router.callback_query(F.data.startswith(("check_pay:")))
async def handle_pay(message: Message):
     
    user_id = message.from_user.id
    _, payment_id, product_id = message.data.split(':')
    
    check_result = yoomoney_pay_check(payment_id=payment_id)
    
    purchased_data = await db.get_one_generic_async(table='purchased', user_id=user_id, product_id=product_id)
    if not purchased_data:
            await db.insert_async(['product_id', 'user_id', 'step', 'paid'], [product_id, user_id, 'check', 0], table='purchased')
    
    if check_result:
        await send_product(user_id=user_id, product_id=product_id)
        
        await db.update_generic_async(table='purchased', columns=['step', 'paid'],
                                      values=['success_check', 1], user_id=user_id, product_id=product_id)
        
    else:
        text = "<b>Проверка не пройдена</b>\n\n<i>Обычно оплата проходит в течении 5-30 секунд\nПодождите и попробуйте проверить еще</i>\n\nЕсли вы оплатили, но проверка всё еще не проходит, напишите об этом\n\n<b>Поддержка ответит в ближайшее время</b>"
        message_to_user = await bot.send_message(chat_id=user_id, text=text)
        await send(user_id, message=message_to_user)
        
        await db.update_generic_async(table='purchased', columns=['step', 'paid'],
                                      values=['unsuccess_check', 0], user_id=user_id, product_id=product_id)