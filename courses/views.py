from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Course, Lesson, Payment
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer
from .permissions import IsOwnerOrStaff


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet для уроков"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для платежей"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователи видят только свои платежи
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)
