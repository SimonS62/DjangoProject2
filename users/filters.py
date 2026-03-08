import django_filters
from .models import Payment
from courses.models import Course, Lesson


class PaymentFilter(django_filters.FilterSet):
    # Фильтрация по дате оплаты (простой вариант по полной дате)
    payment_date = django_filters.DateFilter(lookup_expr='date')

    # Фильтрация по ID курса
    course_id = django_filters.ModelChoiceFilter(
        queryset=Course.objects.all(),
        field_name='course_id', # Фильтруем по полю 'course_id' в модели Payment
        to_field_name='id', # Берем ID из модели Course
        label='Курс (ID)'
    )

    # Фильтрация по ID урока
    lesson_id = django_filters.ModelChoiceFilter(
        queryset=Lesson.objects.all(),
        field_name='lesson_id', # Фильтруем по полю 'lesson_id' в модели Payment
        to_field_name='id', # Берем ID из модели Lesson
        label='Урок (ID)'
    )

    # Фильтрация по способу оплаты
    payment_method = django_filters.ChoiceFilter(choices=Payment.PaymentMethod.choices)

    class Meta:
        model = Payment
        fields = ['payment_date', 'course_id', 'lesson_id', 'payment_method']