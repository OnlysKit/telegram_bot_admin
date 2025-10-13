from aiogram import Router
from aiogram import F
from aiogram.types import Message
from modules.utils.bot_fn import inline_menu, tg_hyperlink
from modules.utils.messages_provider import send
from modules.bot.bot import bot
from modules.utils import db
from modules.utils.payment import yoomoney_pay, yoomoney_pay_check

router = Router()

async def send_product(user_id, product_id):
    print(123)

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
        
    else:
        await send_product()
        
        
@router.callback_query(F.data.startswith(("check_pay:")))
async def handle_pay(message: Message):
     
    user_id = message.from_user.id
    payment_id, product_id = message.data.split(':')
    
    check_result = yoomoney_pay_check(payment_id=payment_id)
    
    if check_result:
        await send_product()
    else:
        text = "<b>Проверка не пройдена</b>\n\n<i>Обычно оплата проходит в течении 5-30 секунд\nПодождите и попробуйте проверить еще</i>\n\nЕсли вы оплатили, а проверка всё еще не проходит, напишите об этом прямо здесь. Поддержка видит сообщения бота и готова помочь"
        await bot.send_message(chat_id=user_id, text=text)