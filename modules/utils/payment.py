import uuid
from yookassa import Configuration, Payment
from modules.configs.config import return_url, shop_key, account_id

Configuration.account_id = account_id
Configuration.secret_key = shop_key

def yoomoney_pay(price, text):

    payment = Payment.create({
                "amount": {
                    "value": f"{price}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url
                },
                "capture": True,
                "description": text
            }, uuid.uuid4())

    confirmation_url = payment.confirmation.confirmation_url

    return {'confirmation_url': confirmation_url, 'payment_id': payment.id}


def yoomoney_pay_check(payment_id):

    payment = Payment.find_one(payment_id)

    pay_status = payment.status

    if pay_status == 'succeeded':
        return True