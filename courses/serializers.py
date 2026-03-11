from rest_framework import serializers
from .models import Course, Lesson, Payment


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['owner']

    @staticmethod
    def get_lessons_count(obj):
        return obj.lessons.count()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ['owner']


class PaymentSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(
        choices=Payment.PAYMENT_METHODS
    )
    class Meta:
        model = Payment
        fields = '__all__'
