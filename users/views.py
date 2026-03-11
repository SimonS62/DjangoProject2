from rest_framework import viewsets, filters
from courses.models import Payment
from courses.serializers import PaymentSerializer
from .filters import PaymentFilter


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = (
        filters.OrderingFilter
    )
    filter_class = PaymentFilter
    ordering_fields = ('payment_date',)
    ordering = ('-payment_date',)
