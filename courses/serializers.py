from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_link
from .models import Course, Lesson, Payment


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()  # Для поля подписки

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['owner']

    @staticmethod
    def get_lessons_count(obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий аутентифицированный пользователь на этот курс.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Предполагаем, что у вас есть модель Subscription, связывающая User и Course
            return Subscription.objects.filter(user=request.user, course=obj).exists()
        return False


class LessonSerializer(serializers.ModelSerializer):
    video_link = serializers.CharField(validators=[validate_youtube_link])
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
