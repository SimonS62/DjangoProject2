from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

from myproject import settings

# Установка переменной окружения для настроек проекта
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Создание экземпляра объекта Celery
app = Celery('myproject')

# Загрузка настроек из файла Django
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.timezone = settings.TIME_ZONE

# Автоматическое обнаружение и регистрация задач из файлов tasks.py в приложениях Django
app.autodiscover_tasks()

# Настройки Celery Beat
app.conf.beat_schedule = {
    # Пример периодической задачи (будет описана в задании 3)
    'block_inactive_users': {
        'task': 'courses.tasks.update_progress', # Путь к вашей задаче
        'schedule': crontab(hour=0, minute=0), # Ежедневно в полночь
        # Или другая периодичность, например, раз в неделю:
        # 'schedule': crontab(day_of_week='sunday', hour=3, minute=30),
    },
}