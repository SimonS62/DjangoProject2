from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from .models import Course, Lesson, Subscription
from users.models import User
from .validators import validate_youtube_link

# --- Вспомогательные функции для создания тестовых данных ---

def create_test_course(title="Test Course"):
    return Course.objects.create(title=title, description="Test Description")

def create_test_lesson(course, title="Test Lesson", content="Test Content", video_link="https://www.youtube.com/watch?v=test"):
    return Lesson.objects.create(course=course, title=title, content=content, video_link=video_link)

# --- Тесты для валидатора ссылок ---

class LinkValidatorTest(APITestCase):
    def test_valid_youtube_link(self):
        self.assertEqual(validate_youtube_link("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(validate_youtube_link("http://youtube.com/watch?v=dQw4w9WgXcQ"), "http://youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(validate_youtube_link(""), "") 

    def test_invalid_link(self):
        with self.assertRaises(ValidationError):
            validate_youtube_link("https://www.google.com")
        with self.assertRaises(ValidationError):
            validate_youtube_link("ftp://example.com/video")

# --- Тесты для CRUD уроков ---

class LessonAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Добавлены уникальные username и email
        self.user = User.objects.create_user(
            username='lesson_user', 
            email='lesson_user@test.com', 
            password='password123'
        )
        self.moderator = User.objects.create_user(
            username='lesson_moderator', 
            email='lesson_moderator@test.com', 
            password='moderatorpassword', 
            is_staff=True
        )

        self.course1 = create_test_course("Course 1")
        self.lesson1 = create_test_lesson(self.course1, title="Lesson 1")
        self.lesson2 = create_test_lesson(self.course1, title="Lesson 2", video_link="https://www.youtube.com/watch?v=other")

        self.list_create_url = reverse('lesson-list-create')
        self.detail_update_delete_url = lambda pk: reverse('lesson-detail-update-delete', kwargs={'pk': pk})

    def test_lesson_list(self):
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # В зависимости от вашей пагинации, данные могут быть в 'results' или просто список
        results = response.json().get('results', response.json())
        self.assertEqual(len(results), 2)

    def test_lesson_create_as_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        data = {
            'course': self.course1.id,
            'title': 'New Lesson by Moderator',
            'content': 'Content for new lesson',
            'video_link': 'https://www.youtube.com/watch?v=new'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 3)

    def test_lesson_create_invalid_link_as_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        data = {
            'course': self.course1.id,
            'title': 'Lesson with Bad Link',
            'content': 'Content',
            'video_link': 'https://www.example.com/video'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lesson_create_as_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'course': self.course1.id,
            'title': 'Lesson by Regular User',
            'content': 'Content'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_as_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_update_delete_url(self.lesson1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# --- Тесты для функционала подписки ---

class SubscriptionAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Свои уникальные данные для этого класса
        self.user = User.objects.create_user(
            username='sub_user', 
            email='sub_user@test.com', 
            password='password123'
        )
        self.another_user = User.objects.create_user(
            username='sub_another', 
            email='sub_another@test.com', 
            password='password456'
        )

        self.course1 = create_test_course("Course for Subscription")
        self.manage_subscription_url = lambda course_id: reverse('manage_subscription', kwargs={'course_id': course_id})

    def test_subscribe_to_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.manage_subscription_url(self.course1.id))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course1).exists())

    def test_subscribe_to_course_again_unsubscribes(self):
        Subscription.objects.create(user=self.user, course=self.course1)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.manage_subscription_url(self.course1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course1).exists())

# --- Тесты пагинации ---

class PaginationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='pag_user', 
            email='pag_user@test.com', 
            password='password123'
        )
        self.course_list_url = reverse('course-list')
        for i in range(12):
            create_test_course(f"Course {i}")

    def test_pagination_works(self):
        response = self.client.get(self.course_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())
