from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('users.urls')), # Пока пусто, но для будущих API-эндпоинтов
    path('api/v1/', include('materials.urls')), # Для материалов
    path('api/v1/', include('materials.urls')),
]

# Для отдачи медиафайлов во время разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
