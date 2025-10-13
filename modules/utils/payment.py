import uuid
from yookassa import Configuration, Payment
from configs.config import return_url

# Ключи для оплаты в юкассе

live_key = 'live_DZQid-uzxEtn33ccBU7Z4a6uslvgn268fNpjM_sRwPk'
test_key = 'test_Vp_u2RYApTI8-PZgcvv4pcoJeEDyX5-Ge7qHuex0ZOw'

live_account_id = '1024974'
test_account_id = '1035066'

# Реальные
Configuration.account_id = test_account_id
Configuration.secret_key = test_key


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