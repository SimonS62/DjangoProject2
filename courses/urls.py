from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from courses.views import (
    CourseViewSet,
    LessonCreateAPIView, LessonListAPIView, LessonRetrieveAPIView,
    LessonUpdateAPIView, LessonDestroyAPIView,
    PaymentViewSet
)

app_name = 'courses'  # Важно для namespace

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('lesson/create/', LessonCreateAPIView.as_view(), name='lesson-create'),
    path('lesson/', LessonListAPIView.as_view(), name='lesson-list'),
    path('lesson/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson-detail'),
    path('lesson/update/<int:pk>/', LessonUpdateAPIView.as_view(), name='lesson-update'),
    path('lesson/delete/<int:pk>/', LessonDestroyAPIView.as_view(), name='lesson-delete'),
    path('courses/<int:course_id>/subscribe/', views.ManageSubscriptionView.as_view(), name='manage_subscription'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail_with_subscription'),
    path('<int:course_id>/subscribe/', views.subscribe_course_view, name='subscribe_course'),
    path('<int:course_id>/unsubscribe/', views.unsubscribe_course_view, name='unsubscribe_course'),
    path('api/courses/<int:course_id>/', views.CourseDetailView.as_view(), name='api_course_detail'),
    path('api/courses/subscribe/', views.SubscribeCourseAPIView.as_view(), name='api_subscribe_course'),
    path('api/courses/unsubscribe/', views.UnsubscribeCourseAPIView.as_view(), name='api_unsubscribe_course'),
    path('api/payments/init/', views.InitPaymentAPIView.as_view(), name='api_init_payment'),
    path('api/payments/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('api/payments/status/', views.RetrievePaymentStatusAPIView.as_view(), name='api_payment_status'),

]