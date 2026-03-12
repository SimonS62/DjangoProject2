from django.urls import path, include
from rest_framework.routers import DefaultRouter
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

    # Урлы для уроков (через Generic классы)
    path('lesson/create/', LessonCreateAPIView.as_view(), name='lesson-create'),
    path('lesson/', LessonListAPIView.as_view(), name='lesson-list'),
    path('lesson/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson-detail'),
    path('lesson/update/<int:pk>/', LessonUpdateAPIView.as_view(), name='lesson-update'),
    path('lesson/delete/<int:pk>/', LessonDestroyAPIView.as_view(), name='lesson-delete'),
]