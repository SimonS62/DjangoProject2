from rest_framework import generics
from rest_framework import viewsets
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class LessonListCreateView(generics.ListCreateAPIView):
    """
    Получение списка уроков и создание нового урока.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Получение, обновление (полное/частичное) и удаление одного урока.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer