from rest_framework import viewsets, generics
from .models import Course
from .serializers import CourseSerializer
from .models import Lesson
from .serializers import LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonListCreateView(generics.ListCreateAPIView):
    """
    Список всех уроков и возможность создания нового урока (POST).
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Отображение, обновление (PUT/PATCH) и удаление (DELETE) одного урока по PK.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

