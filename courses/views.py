from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from drf_yasg.openapi import Response
from pyexpat.errors import messages
from rest_framework import generics, viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
import stripe
from courses.models import Course, Lesson, Payment, Subscription
from courses.permissions import IsOwner, IsModerator
from courses.serializers import CourseSerializer, LessonSerializer, PaymentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from users.permissions import IsModerator
from . import models
from .paginators import StandardPagination
from django.db.models import Exists, OuterRef
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .stripe_service import StripeServiceError, create_checkout_session, create_stripe_price, create_stripe_product, \
    retrieve_checkout_session
from users.filters import PaymentFilter
from django_filters import rest_framework as filters


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

@login_required
def subscribe_course_view(request, course_id: int):
    """
    Обрабатывает подписку пользователя на курс.
    """
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        raise Http404("Курс не найден.") # Или можно использовать get_object_or_404

    user = request.user

    if request.method == 'POST':
        try:
            # Проверяем, не подписан ли пользователь уже
            if not Subscription.objects.filter(user=user, course=course).exists():
                Subscription.objects.create(user=user, course=course)
                messages.success(request, f'Вы успешно подписались на курс "{course.title}"!')
            else:
                messages.warning(request, f'Вы уже подписаны на курс "{course.title}".')
        except Exception as e:
            messages.error(request, f'Произошла ошибка при подписке: {e}')


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

        # Перенаправление на страницу деталей курса.
        return redirect('course_detail', course_id=course_id)
    else:
        messages.error(request, 'Недопустимый метод запроса.')
        return redirect('course_detail', course_id=course_id)

# Подписка на курс (API)
class SubscribeCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    @swagger_auto_schema(
        operation_id='subscribe_course',
        operation_summary='Подписаться на курс',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'course_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID курса'),
            },
            required=['course_id']
        ),
        responses={
            201: 'Подписка успешна',
            400: 'Ошибка (например, уже подписан или курс не найден)',
            401: 'Не авторизован',
            404: 'Курс не найден'
        }
    )
    def post(self, request, *args, **kwargs):
         # Добавим проверку, что курс существует, еще до попытки подписки
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'detail': 'Необходимо указать ID курса.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'detail': 'Курс не найден.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Проверяем, не подписан ли пользователь уже
        if Subscription.objects.filter(user=user, course=course).exists():
            return Response({'detail': 'Вы уже подписаны на этот курс.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            Subscription.objects.create(user=user, course=course)
            # Если нужен ответ с сериализованными данными подписки:
            # serializer = SubscriptionSerializer(new_subscription)
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'detail': 'Подписка успешна!'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': f'Произошла ошибка при подписке: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Отписка от курса (API)
class UnsubscribeCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    

    @swagger_auto_schema(
        operation_id='unsubscribe_course',
        operation_summary='Отписаться от курса',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'course_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID курса'),
            },
            required=['course_id']
        ),
        responses={
            200: 'Отписка успешна',
            400: 'Ошибка (например, не подписан)',
            401: 'Не авторизован',
            404: 'Курс не найден'
        }
    )
    def post(self, request, *args, **kwargs):
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'detail': 'Необходимо указать ID курса.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'detail': 'Курс не найден.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.delete()
            return Response({'detail': 'Отписка успешна!'}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Вы не были подписаны на этот курс.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Произошла ошибка при отписке: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InitPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    @swagger_auto_schema(
        operation_id='init_payment',
        operation_summary='Инициировать платеж за курс',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'course_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID курса'),
            },
            required=['course_id']
        ),
        responses={
            201: openapi.Response(
                'Платеж создан, ссылка на оплату предоставлена.',
                PaymentSerializer # Отдаем сериализованные данные платежа
            ),
            400: 'Ошибка (например, курс не найден, цена не установлена, или уже есть активный платеж)',
            401: 'Не авторизован',
            500: 'Внутренняя ошибка сервера'
        }
    )
    def post(self, request, success_url=None, *args, **kwargs):
        course_id = request.data.get('course_id')
        user = request.user

        if not course_id:
            return Response({'detail': 'Необходимо указать ID курса.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'detail': 'Курс не найден.'}, status=status.HTTP_404_NOT_FOUND)

        # --- Проверка: есть ли уже активный платеж для этого курса у пользователя? ---
        # Можно добавить логику, чтобы пользователь не мог создать новый платеж, если предыдущий:
        # 1. Уже оплачен
        # 2. В процессе оплаты (если вы отслеживаете это)
        # Пока простая проверка: если есть платеж в статусе 'created'
        if Payment.objects.filter(user=user, course=course, status='created').exists():
            return Response({'detail': 'У вас уже есть неоплаченный платеж для этого курса.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- Создание продукта и цены в Stripe ---
        try:
            if not course.stripe_product_id:
                course.stripe_product_id = create_stripe_product(course)
                course.save() # Сохраняем ID продукта Stripe в базу данных


            if not hasattr(course, 'price') or course.price is None:
                 return Response({'detail': 'Цена курса не установлена.'}, status=status.HTTP_400_BAD_REQUEST)

            stripe_price_id = create_stripe_price(
                product_id=course.stripe_product_id, 
                amount=course.price, 
                currency=course.currency if hasattr(course, 'currency') else 'usd'
            )

            # --- Создание платежа в нашей системе ---
            # Создаем запись о платеже до создания сессии Stripe
            payment = Payment.objects.create(
                user=user,
                course=course,
                stripe_product_id=course.stripe_product_id,
                stripe_price_id=stripe_price_id, # Сохраняем ID цены
                amount=course.price, # Цена нашей системы
                currency=course.currency if hasattr(course, 'currency') else 'usd', # Валюта нашей системы
                status='created' # Платеж создан, но еще не оплачен
            )

            session_id, checkout_url = create_checkout_session(
                price_id=stripe_price_id,
                course_title=course.title,
                success_url=success_url
            )

            # Обновляем нашу запись о платеже
            payment.stripe_checkout_session_id = session_id
            payment.checkout_url = checkout_url
            payment.save()

            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except StripeServiceError as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Course.DoesNotExist: # Повторная проверка, на случай если курс удалили между запросами
            return Response({'detail': 'Курс не найден.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Логируем ошибку для отладки
            # logger.error(f"Ошибка при инициации платежа: {e}") 
            return Response({'detail': f'Произошла внутренняя ошибка сервера: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentSuccessView(APIView):
    permission_classes = [IsAuthenticated] # Можно сделать доступным без аутентификации, если пользователь уже авторизован

    @swagger_auto_schema(
        operation_id='payment_success',
        operation_summary='Перенаправление после успешной оплаты',
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="ID сессии Stripe", type=openapi.TYPE_STRING),
        ],
        responses={
            200: 'Успешная оплата',
            400: 'Неверные параметры запроса',
            404: 'Платеж не найден',
            500: 'Ошибка сервера'
        }
    )
    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response({'detail': 'ID сессии Stripe не найден в параметрах запроса.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Получаем сессию из Stripe, чтобы убедиться, что она действительно оплачена
            stripe_session = retrieve_checkout_session(session_id)

            # Проверяем статус сессии Stripe
            if stripe_session.payment_status == 'paid':
                # 2. Находим наш платеж в базе данных
                payment = Payment.objects.get(stripe_checkout_session_id=session_id)

                # 3. Обновляем статус нашего платежа, если он еще не оплачен
                if payment.status != 'paid':
                    payment.status = 'paid'
                    payment.save()

                    # Здесь можно добавить логику:
                    # - Назначить пользователю доступ к курсу
                    # - Отправить email с подтверждением
                    # - ...

                    # Для модели Subscription, если она уже есть
                    # try:
                    #     subscription, created = Subscription.objects.get_or_create(user=payment.user, course=payment.course)
                    #     if created:
                    #         messages.success(request, f"Вы успешно получили доступ к курсу '{payment.course.title}'!")
                    # except Exception as sub_err:
                    #     print(f"Ошибка при создании подписки после оплаты: {sub_err}")

                    return Response({'detail': 'Оплата прошла успешно! Спасибо!', 'payment_id': payment.id}, status=status.HTTP_200_OK)
                else:
                    # Платеж уже был обработан
                    return Response({'detail': 'Этот платеж уже был успешно обработан.'}, status=status.HTTP_200_OK) # Или 409 Conflict

            else:
                # Платеж не оплачен или статус неизвестен
                # Можно обновить статус платежа
                if payment.status != stripe_session.payment_status:
                    payment.status = stripe_session.payment_status
                    payment.save()
                return Response({'detail': f'Статус оплаты: {stripe_session.payment_status}. Ваша оплата еще не подтверждена.', 'payment_id': payment.id}, status=status.HTTP_400_BAD_REQUEST)

        except Payment.DoesNotExist:
            return Response({'detail': 'Платеж не найден в нашей системе.'}, status=status.HTTP_404_NOT_FOUND)
        except StripeServiceError as e:
            return Response({'detail': f'Ошибка при проверке статуса оплаты: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'detail': f'Произошла внутренняя ошибка сервера: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RetrievePaymentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='retrieve_payment_status',
        operation_summary='Получить статус платежа по ID сессии Stripe',
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="ID сессии Stripe", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                'Статус платежа',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'payment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID платежа в нашей системе'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Статус платежа (created, paid, failed, ...)'),
                        'stripe_session_status': openapi.Schema(type=openapi.TYPE_STRING, description='Статус в Stripe'),
                        'checkout_url': openapi.Schema(type=openapi.TYPE_STRING, description='Link to checkout page if not paid'),
                    }
                )
            ),
            400: 'Неверные параметры запроса',
            404: 'Платеж не найден',
            500: 'Ошибка сервера'
        }
    )
    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response({'detail': 'ID сессии Stripe не найден в параметрах запроса.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Ищем платеж в нашей базе данных
            payment = Payment.objects.get(stripe_checkout_session_id=session_id)

            # 2. Получаем актуальный статус из Stripe API
            stripe_session = retrieve_checkout_session(session_id)

            # 3. Обновляем статус нашего платежа, если он изменился
            if payment.status != stripe_session.payment_status:
                payment.status = stripe_session.payment_status
                payment.save()

            response_data = {
                'payment_id': payment.id,
                'status': payment.status,
                'stripe_session_status': stripe_session.payment_status,
            }

            # Если платеж еще не оплачен, возвращаем ссылку на оплату
            if payment.status == 'created' and payment.checkout_url:
                response_data['checkout_url'] = payment.checkout_url

            return Response(response_data, status=status.HTTP_200_OK)

        except Payment.DoesNotExist:
            return Response({'detail': 'Платеж не найден в нашей системе.'}, status=status.HTTP_404_NOT_FOUND)
        except StripeServiceError as e:
            return Response({'detail': f'Ошибка при проверке статуса оплаты: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'detail': f'Произошла внутренняя ошибка сервера: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

