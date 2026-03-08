from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonListCreateView
from .views import LessonDetailView

app_name = "materials"

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"lessons", LessonListCreateView)


urlpatterns = [
    path("", include(router.urls)),
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list-create"),
    path("lessons/<int:pk>/", LessonDetailView.as_view(), name="lesson-detail"),
]
