import django_filters
from django_filters import rest_framework as filters, FilterSet
from courses.models import Payment


class PaymentFilter(FilterSet):
    class Meta:
        model = Payment
        fields = ['payment_method', 'course', 'lesson']

    # Фильтр по способу оплаты
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHODS,
        lookup_expr='iexact'
    )

    # Фильтр по курсу (по id)
    course = django_filters.NumberFilter(
        field_name='course__id',
        lookup_expr='exact'
    )

    # Фильтр по уроку (по id)
    lesson = django_filters.NumberFilter(
        field_name='lesson__id',
        lookup_expr='exact'
    )

    # Фильтр по дате (больше или равно)
    payment_date_gte = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='gte'
    )

    # Фильтр по дате (меньше или равно)
    payment_date_lte = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='lte'
    )

