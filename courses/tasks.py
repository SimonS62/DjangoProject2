from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from users.models import User


@shared_task
def send_course_update_email(user_email, course_title, course_link):
    """
    Асинхронная задача для отправки письма об обновлении курса.
    """
    try:
        subject = f"Обновление материалов курса: {course_title}"
        message = (
            f"Здравствуйте!\n\n"
            f"Хотим сообщить, что в курсе '{course_title}' появились новые материалы.\n"
            f"Вы можете ознакомиться с ними по ссылке: {course_link}\n\n"
            f"С уважением,\n"
            f"Команда вашего проекта"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user_email]

        send_mail(subject, message, from_email, recipient_list)
        print(f"Письмо успешно отправлено пользователю {user_email} об обновлении курса {course_title}") # Логирование
    except Exception as e:
        print(f"Ошибка при отправке письма пользователю {user_email}: {e}") # Логирование ошибки


@shared_task
def block_inactive_users():
    """
    Фоновая задача для блокировки неактивных пользователей.
    """
    # Проверяем, что USE_TZ = True в settings.py
    one_month_ago = timezone.now() - timedelta(days=30)
    # Важно: last_login может быть None для новых пользователей, не прошедших авторизацию
    # Поэтому проверяем, что last_login не None
    inactive_users = User.objects.filter(
        last_login__lt=one_month_ago,
        is_active=True,
        last_login__isnull=False # Добавляем проверку на null
    )

    for user in inactive_users:
        user.is_active = False
        user.save()
        print(f"Пользователь {user.username} (ID: {user.id}) заблокирован из-за неактивности.")