from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, UserViewSet


router = DefaultRouter()
router.register('users', UserViewSet, basename='user') # basename нужен для ModelViewSet

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('', include(router.urls)),
]