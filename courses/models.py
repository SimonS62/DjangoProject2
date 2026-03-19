from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()
objects = models.Manager()

class Course(models.Model):
    """Модель курса"""
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    preview = models.ImageField(upload_to='courses/previews/', null=True, blank=True, verbose_name='Превью')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    # Владелец курса
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Владелец'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока"""
    objects = None
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    preview = models.ImageField(upload_to='lessons/previews/', null=True, blank=True, verbose_name='Превью')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')

    # Привязка к курсу
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )

    # Владелец урока
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Владелец'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title

class Payment(models.Model):
    """Модель платежа"""
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        # Можно добавить другие методы: 'bank_transfer', 'online_gateway' и т.д.
    ]

    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
        ('refunded', 'Возвращен'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Пользователь'
    )

    course = models.ForeignKey(
        'courses.Course', # Используйте правильный путь к вашей модели Course
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Курс'
    )

    lesson = models.ForeignKey(
        'lessons.Lesson', # Используйте правильный путь к вашей модели Lesson
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Урок'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='Способ оплаты')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name='ID транзакции (внешний)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус оплаты'
    )
    extra_data = models.JSONField(blank=True, null=True, verbose_name='Дополнительные данные')


    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-payment_date'] # Опционально: сортировка по дате

    def __str__(self):
        return f"Платеж №{self.id} ({self.user.username if self.user else 'Неизвестный пользователь'}) - {self.amount} руб. [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        # Пример: Автоматическое заполнение transaction_id, если он отсутствует
        # Это может быть реализовано иначе, в зависимости от логики вашей системы
        if not self.transaction_id and self.status == 'completed':
             # Генерация уникального ID, если это необходимо на данном этапе
             # Убедитесь, что ID генерируется правильно и уникально
             pass
        super().save(*args, **kwargs)

class Subscription(models.Model):
    """
    Модель для подписки пользователя на обновления курса.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course') # Одному пользователю можно подписаться на курс только один раз
        ordering = ['-created_at']

    def __str__(self):
        return f"Подписка {self.user.username} на {self.course.title}"