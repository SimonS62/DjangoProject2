from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__' # Выводит все поля урока

class CourseSerializer(serializers.ModelSerializer):
    num_lessons = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            'id',
            'title',
            'preview',
            'description',
            'num_lessons',
            'lessons'
        )
        read_only_fields = ('num_lessons', 'lessons')

    def get_num_lessons(self, obj):
        return obj.lessons.count()