from rest_framework import viewsets, filters
from .models import Payment
from .filters import PaymentFilter

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter # Добавляем стандартный фильтр сортировки DRF
    )
    filterset_class = PaymentFilter
    ordering_fields = ('payment_date',) # Поля, по которым можно сортировать
    ordering = ('-payment_date',) # Сортировка по умолчанию (новые платежи первыми)
