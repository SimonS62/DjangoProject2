from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson
from users.models import Payment
import datetime
import random


User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with dummy payment data.'

    def handle(self, *args, **options):
        User.objects.all().count() # Убедимся, что есть пользователи
        Course.objects.all().count() # Убедимся, что есть курсы
        Lesson.objects.all().count() # Убедимся, что есть уроки

        if not User.objects.exists():
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        if not Course.objects.exists():
            self.stdout.write(self.style.ERROR('No courses found. Please create courses first.'))
            return
        if not Lesson.objects.exists():
            self.stdout.write(self.style.ERROR('No lessons found. Please create lessons first.'))
            return

        users = list(User.objects.all())
        courses = list(Course.objects.all())
        lessons = list(Lesson.objects.all())
        payment_methods = [choice[0] for choice in Payment.PaymentMethod.choices]

        num_payments = 20 # Количество фиктивных платежей для создания

        for _ in range(num_payments):
            user = random.choice(users)
            amount = round(random.uniform(500, 5000), 2)
            payment_method = random.choice(payment_methods)
            payment_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))

            # Случайный выбор: либо курс, либо урок
            if random.choice([True, False]):
                course = random.choice(courses)
                lesson = None
            else:
                lesson = random.choice(lessons)
                course = None

            Payment.objects.create(
                user=user,
                payment_date=payment_date,
                course=course,
                lesson=lesson,
                amount=amount,
                payment_method=payment_method
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {num_payments} payments.'))
