import stripe
from django.conf import settings
from .models import Course, Payment

# !!! Важно: Установите ваш секретный ключ Stripe !!!
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeServiceError(Exception):
    """Кастомное исключение для ошибок Stripe."""
    pass

def create_stripe_product(course: Course):
    """
    Создает продукт в Stripe, связывая его с объектом Course.
    Возвращает ID продукта Stripe.
    """
    try:
        response = stripe.Product.create(
            name=course.title,
            # description=course.description # Если есть описание
            metadata={'course_id': str(course.id)} # Важно для связи обратно
        )
        return response['id']
    except stripe.error.StripeError as e:
        raise StripeServiceError(f"Ошибка создания продукта Stripe: {e}")

def create_stripe_price(product_id: str, amount: float, currency: str = 'usd'):
    """
    Создает цену в Stripe для указанного продукта.
    amount передается в центах (умножаем на 100).
    """
    try:
        response = stripe.Price.create(
            product=product_id,
            unit_amount=int(amount * 100), # Цена в центах
            currency=currency,
        )
        return response['id']
    except stripe.error.StripeError as e:
        raise StripeServiceError(f"Ошибка создания цены Stripe: {e}")

def create_checkout_session(price_id: str, course_title: str, success_url: str):
    """
    Создает сессию оплаты в Stripe.
    Возвращает URL сессии Stripe.
    """
    try:
        response = stripe.checkout.Session.create(
            payment_method_types=['card'], # Только оплата картой
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment', # Или 'subscription' если нужно
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}", # Получаем ID сессии
            cancel_url=success_url, # Можно уйти на страницу курсов или деталей курса
            # customer_email=user_email, # Если есть email пользователя
            metadata={'course_title': course_title} # Для идентификации сессии
        )
        return response['id'], response['url']
    except stripe.error.StripeError as e:
        raise StripeServiceError(f"Ошибка создания сессии Stripe Checkout: {e}")

# Дополнительно: Функция для получения статуса сессии (для Задания 3)
def retrieve_checkout_session(session_id: str):
    """
    Получает данные сессии Stripe по ее ID.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except stripe.error.StripeError as e:
        raise StripeServiceError(f"Ошибка получения сессии Stripe: {e}")