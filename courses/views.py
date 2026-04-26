from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import generics, viewsets, filters as drf_filters, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from courses.models import Course, Lesson, Payment, Subscription
from courses.permissions import IsOwner
from users.permissions import IsModerator
from courses.serializers import CourseSerializer, LessonSerializer, PaymentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from . import models
from .paginators import StandardPagination
from django.db.models import Exists, OuterRef, Value
from users.filters import PaymentFilter
from .filters import CourseFilter


class LessonCreateAPIView(generics.CreateAPIView):
    """Создание урока"""
    serializer_class = LessonSerializer
    # Модераторы не могут создавать уроки
    permission_classes = [IsAuthenticated, ~IsModerator]

    def perform_create(self, serializer):
        lesson = serializer.save(owner=self.request.user)

class LessonListAPIView(generics.ListAPIView):
    """Список уроков"""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Если пользователь — модератор или админ (is_staff), он видит все уроки
        if user.is_staff or user.groups.filter(name='moderator').exists():
            return Lesson.objects.all()
        else:
            # Иначе, обычные пользователи видят только свои уроки
            return Lesson.objects.filter(owner=user)

class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Просмотр урока"""
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    # Права: владелец урока ИЛИ модератор ИЛИ администратор
    # Используем | (OR) для объединения прав
    permission_classes = [IsAuthenticated, IsOwner | IsModerator | IsAdminUser]

class LessonUpdateAPIView(generics.UpdateAPIView):
    """Обновление урока"""
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    # Права: владелец урока ИЛИ модератор
    permission_classes = [IsAuthenticated, IsOwner | IsModerator]

class LessonDestroyAPIView(generics.DestroyAPIView):
    """Удаление урока"""
    queryset = Lesson.objects.all()
    # Права: владелец урока И И НЕ модератор.
    # Это значит, что только владелец может удалить,
    # и модераторы не могут удалять уроки даже если они их владельцы.
    permission_classes = [IsAuthenticated, IsOwner & ~IsModerator]

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]  # Исправленный импорт filters
    filterset_class = CourseFilter

    def get_permissions(self):
        """
        Определение прав доступа для различных действий ViewSet.
        """
        if self.action == 'list':
            # Все аутентифицированные пользователи могут просматривать списки курсов
            # Можно установить AllowAny, если требуется доступ для неаутентифицированных
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            # Все аутентифицированные пользователи могут просматривать детали курса
            # Можно установить AllowAny, если требуется доступ для неаутентифицированных
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'update' or self.action == 'partial_update':
            # Модераторы и владельцы курсов могут редактировать
            # Убедитесь, что IsOwner корректно определен и используется
            self.permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        elif self.action == 'create':
            # Только модераторы могут создавать новые курсы
            self.permission_classes = [IsAuthenticated, IsModerator]
        elif self.action == 'destroy':
            # Только модераторы могут удалять курсы
            self.permission_classes = [IsAuthenticated, IsModerator]
        else:
            # По умолчанию для всех остальных действий
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter] # Исправленный импорт filters

    def get_permissions(self):
        """
        Определение прав доступа для различных действий ViewSet.
        """
        if self.action == 'list':
            # Все аутентифицированные пользователи могут просматривать списки уроков
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            # Все аутентифицированные пользователи могут просматривать детали урока
            self.permission_classes = [IsAuthenticated]
        elif self.action == 'update' or self.action == 'partial_update':
            # Модераторы и владельцы уроков могут редактировать
            self.permission_classes = [IsAuthenticated, IsModerator | IsOwner]
        elif self.action == 'create':
            # Только модераторы могут создавать новые уроки
            self.permission_classes = [IsAuthenticated, IsModerator]
        elif self.action == 'destroy':
            # Только модераторы могут удалять уроки
            self.permission_classes = [IsAuthenticated, IsModerator]
        else:
            # По умолчанию для всех остальных действий
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для платежей"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend]  # DjangoFilterBackend импортирован отдельно
    filterset_class = PaymentFilter
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Ограничивает доступ к платежам: админы видят все, остальные - только свои.
        """
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
        Добавляет признак подписки (is_subscribed) для каждого курса в списке.
        """
        queryset = super().get_queryset()
        request = self.request
        if request.user.is_authenticated:
            # Используем Exists для эффективной проверки подписки
            # OuterRef('pk') ссылается на первичный ключ (pk) текущего курса из queryset
            subscribed_courses = Subscription.objects.filter(
                user=request.user,
                course_id=OuterRef('pk')
            )
            queryset = queryset.annotate(
                is_subscribed=Exists(subscribed_courses)
            )
        else:
            # Для неаутентифицированных пользователей, поле is_subscribed устанавливается в False
            # Используем Value из django.db.models
            queryset = queryset.annotate(is_subscribed=Value(False))
        return queryset

class CourseDetailView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # pagination_class = StandardPagination # Пагинация для уроков внутри курса, если нужно

    def get_queryset(self):
        """
        Аналогично CourseListView, добавляет is_subscribed для детализации.
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
            queryset = queryset.annotate(is_subscribed=Value(False)) # Используем Value
        return queryset

@login_required
def subscribe_course_view(request, course_id: int):
    """
    Обрабатывает подписку пользователя на курс.
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        # Используем Http404 для более понятной ошибки
        raise Http404("Курс не найден.")

    user = request.user

    if request.method == 'POST':
        try:
            # Проверяем, не подписан ли пользователь уже, чтобы избежать дублирования
            if not Subscription.objects.filter(user=user, course=course).exists():
                Subscription.objects.create(user=user, course=course)
                messages.success(request, f'Вы успешно подписались на курс "{course.title}"!')
            else:
                messages.warning(request, f'Вы уже подписаны на курс "{course.title}".')
        except Exception as e:
            messages.error(request, f'Произошла ошибка при подписке: {e}')

        # Перенаправляем пользователя обратно на страницу курса
        return redirect('course_detail', course_id=course_id)
    else:
        messages.error(request, 'Недопустимый метод запроса.')
        return redirect('course_detail', course_id=course_id)


@login_required
def unsubscribe_course_view(request, course_id: int):
    """
    Обрабатывает отписку пользователя от курса.
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise Http404("Курс не найден.")

    user = request.user

    if request.method == 'POST':
        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()
            messages.success(request, f'Вы успешно отписались от курса "{course.title}"!')
        except Subscription.DoesNotExist:
            messages.warning(request, 'Вы не были подписаны на этот курс.')
        except Exception as e:
            messages.error(request, f'Произошла ошибка при отписке: {e}')

        return redirect('course_detail', course_id=course_id)
    else:
        messages.error(request, 'Недопустимый метод запроса.')
        return redirect('course_detail', course_id=course_id)

class ManageSubscriptionView(APIView):
    """
    Управляет подпиской пользователя на курс (подписать/отписать).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = self.kwargs.get('course_id')

        # Получаем объект курса или 404
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({"error": "Курс не найден"}, status=status.HTTP_404_NOT_FOUND)

        # Ищем подписку
        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            # Если подписка есть — удаляем
            subscription.delete()
            message = 'Подписка удалена'
        else:
            # Если подписки нет — создаем
            Subscription.objects.create(user=user, course=course)
            message = 'Подписка добавлена'

        return Response({"message": message}, status=status.HTTP_200_OK)
