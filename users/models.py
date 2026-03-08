from django.db import models
from django.contrib.auth.models import AbstractUser
from courses.models import Course, Lesson


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return self.email if self.email else self.username

class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличные'
        TRANSFER = 'transfer', 'Перевод на счет'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    # Поля для связи с курсом или уроком
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)

    def clean(self):
        # Валидация: либо курс, либо урок должен быть указан, но не оба одновременно
        if self.course and self.lesson:
            raise models.ValidationError("Платеж может быть связан либо с курсом, либо с уроком, но не с обоими.")
        if not self.course and not self.lesson:
            raise models.ValidationError("Платеж должен быть связан с курсом или уроком.")

    def __str__(self):
        return f"Платеж пользователя {self.user.username} от {self.payment_date.strftime('%Y-%m-%d')} на сумму {self.amount}"



