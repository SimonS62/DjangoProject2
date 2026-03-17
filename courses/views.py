from rest_framework import generics, viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import RetrieveAPIView
from courses.models import Course, Lesson, Payment, Subscription
from courses.permissions import IsOwner, IsModerator
from courses.serializers import CourseSerializer, LessonSerializer, PaymentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from users.filters import PaymentFilter
from users.permissions import IsModerator
from .paginators import StandardPagination
from django.db.models import Exists, OuterRef


# Уроки через Generic классы
class LessonCreateAPIView(generics.CreateAPIView):
    """Создание урока"""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModerator]  # Модераторы не могут создавать

    def perform_create(self, serializer):
        lesson = serializer.save(owner=self.request.user)
        lesson.owner = self.request.user
        lesson.save()

class LessonListAPIView(generics.ListAPIView):
    """Список уроков"""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.groups.filter(name='moderator').exists():
            # Модераторы и админы видят все уроки
            return Lesson.objects.all()
        else:
            # Обычные пользователи видят только свои уроки
            return Lesson.objects.filter(owner=user)

class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Просмотр урока"""
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsModerator | IsAdminUser]

class LessonUpdateAPIView(generics.UpdateAPIView):
    """Обновление урока"""
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsModerator]

class LessonDestroyAPIView(generics.DestroyAPIView):
    """Удаление урока"""
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner & ~IsModerator]  # Модераторы не могут удалять

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CourseFilter

    def get_permissions(self):
        # Общие права: только аутентифицированные для большинства действий
        base_permissions = [IsAuthenticated]

        if self.action == 'list':
            # Модераторы и все аутентифицированные могут просматривать списки
            # Используем | (OR) для объединения прав
            self.permission_classes = [AllowAny] # Или IsAuthenticated, если нужно
        elif self.action == 'retrieve':
            # Модераторы и все аутентифицированные могут просматривать детали
            self.permission_classes = [AllowAny] # Или IsAuthenticated, если нужно
        elif self.action == 'update' or self.action == 'partial_update':
            # Модераторы и владельцы могут редактировать
            self.permission_classes = [IsAuthenticated, IsModerator | IsOwner] # <-- Тут мы используем IsOwner из Задания 3
        elif self.action == 'create':
            # Только модераторы могут создавать новые курсы
            self.permission_classes = [IsAuthenticated, IsModerator]
        elif self.action == 'destroy':
            # Только модераторы могут удалять курсы
            self.permission_classes = [IsAuthenticated, IsModerator]
        else:
            self.permission_classes = base_permissions
        return [permission() for permission in self.permission_classes]

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LessonFilter

    def get_permissions(self):
        # Общие права: только аутентифицированные для большинства действий
        base_permissions = [IsAuthenticated]

        if self.action == 'list':
            # Модераторы и все аутентифицированные могут просматривать списки
            self.permission_classes = [AllowAny] # Или IsAuthenticated, если нужно
        elif self.action == 'retrieve':
            # Модераторы и все аутентифицированные могут просматривать детали
            self.permission_classes = [AllowAny] # Или IsAuthenticated, если нужно
        elif self.action == 'update' or self.action == 'partial_update':
            # Модераторы и владельцы могут редактировать
            self.permission_classes = [IsAuthenticated, IsModerator | IsOwner] # <-- Тут мы используем IsOwner из Задания 3
        elif self.action == 'create':
            # Только модераторы могут создавать новые уроки
            self.permission_classes = [IsAuthenticated, IsModerator]
        elif self.action == 'destroy':
            # Только модераторы могут удалять уроки
            self.permission_classes = [IsAuthenticated, IsModerator]
        else:
            self.permission_classes = base_permissions
        return [permission() for permission in self.permission_classes]

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для платежей"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PaymentFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

class CourseListView(generics.ListAPIView): # Или APIView, ListCreateAPIView
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = StandardPagination # Интегрируем пагинатор

    def get_queryset(self):
        """
        Добавляем признак подписки для каждого курса в списке,
        если пользователь аутентифицирован.
        """
        queryset = super().get_queryset()
        request = self.request
        if request.user.is_authenticated:
            # Используем Exists для эффективной проверки подписки
            subscribed_courses = Subscription.objects.filter(
                user=request.user,
                course_id=OuterRef('pk') # Сравниваем с pk текущего курса
            )
            queryset = queryset.annotate(
                is_subscribed=Exists(subscribed_courses)
            )
        else:
            # Для неаутентифицированных пользователей, поле is_subscribed будет False
            queryset = queryset.annotate(is_subscribed=models.Value(False)) # Добавляем поле, если его нет в сериализаторе
        return queryset

class CourseDetailView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # pagination_class = StandardPagination # Пагинация для уроков внутри курса, если нужно

    def get_queryset(self):
        """
        Аналогично CourseListView, добавляем is_subscribed для детализации.
        """
        queryset = super().get_queryset()
        request = self.request
        if request.user.is_authenticated:
            subscribed_courses = Subscription.objects.filter(
                user=request.user,
                course_id=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_subscribed=Exists(subscribed_courses)
            )
        else:
            queryset = queryset.annotate(is_subscribed=models.Value(False))
        return queryset