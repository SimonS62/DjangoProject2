from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

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
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Пользователь'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Курс'
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Урок'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='Способ оплаты')
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата оплаты')

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"Платеж {self.user.email} - {self.amount} руб."