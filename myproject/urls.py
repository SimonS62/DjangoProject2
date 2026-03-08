from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/materials/", include("materials.urls", namespace="materials")),
    path("api/users/", include("users.urls", namespace="users")),
    path('api/courses/', include('courses.urls')),
]

# Для отдачи медиафайлов во время разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
