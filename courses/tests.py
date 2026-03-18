from multiprocessing.connection import Client
from unittest import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
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
        self.assertEqual(validate_youtube_link(""), "") # Пустая ссылка валидна

    def test_invalid_link(self):
        with self.assertRaises(ValidationError):
            validate_youtube_link("https://www.google.com")
        with self.assertRaises(ValidationError):
            validate_youtube_link("ftp://example.com/video")

# --- Тесты для CRUD уроков ---

class LessonAPITest(APITestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.moderator = User.objects.create_user(username='moderator', password='moderatorpassword', is_staff=True) # Предполагаем, что staff = модератор

        self.course1 = create_test_course("Course 1")
        self.lesson1 = create_test_lesson(self.course1, title="Lesson 1")
        self.lesson2 = create_test_lesson(self.course1, title="Lesson 2", video_link="https://www.youtube.com/watch?v=other")

        # URLs (адаптированные под вашу структуру)
        self.list_create_url = reverse('lesson-list-create') # Предполагаемое имя URL для списка/создания уроков
        self.detail_update_delete_url = lambda pk: reverse('lesson-detail-update-delete', kwargs={'pk': pk}) # Предполагаемое имя URL для деталей/обновления/удаления

    def test_lesson_list(self):
        """
        Проверяет получение списка уроков.
        """
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 2) # Проверяем количество уроков

    def test_lesson_create_as_moderator(self):
        """
        Проверяет создание урока модератором.
        """
        self.client.force_authenticate(user=self.moderator)
        data = {
            'course': self.course1.id,
            'title': 'New Lesson by Moderator',
            'content': 'Content for new lesson',
            'video_link': 'https://www.youtube.com/watch?v=new'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 3) # Было 2, стало 3
        self.assertEqual(response.json()['title'], 'New Lesson by Moderator')

    def test_lesson_create_invalid_link_as_moderator(self):
        """
        Проверяет создание урока с невалидной ссылкой модератором.
        """
        self.client.force_authenticate(user=self.moderator)
        data = {
            'course': self.course1.id,
            'title': 'Lesson with Bad Link',
            'content': 'Content',
            'video_link': 'https://www.example.com/video' # Не YouTube
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Разрешены только ссылки на YouTube.com.', str(response.data)) # Проверяем сообщение об ошибке

    def test_lesson_create_as_regular_user_forbidden(self):
        """
        Проверяет, что обычный пользователь не может создавать уроки.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'course': self.course1.id,
            'title': 'Lesson by Regular User',
            'content': 'Content',
            'video_link': 'https://www.youtube.com/watch?v=user'
        }
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # или 401, если нет прав
        self.assertEqual(Lesson.objects.count(), 2)


    def test_lesson_update_as_moderator(self):
        """
        Проверяет обновление урока модератором.
        """
        self.client.force_authenticate(user=self.moderator)
        new_data = {
            'title': 'Updated Lesson 1 Title',
            'content': 'Updated content for lesson 1',
            'video_link': 'https://www.youtube.com/watch?v=updated'
        }
        response = self.client.put(self.detail_update_delete_url(self.lesson1.id), new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Lesson.objects.get(id=self.lesson1.id).title, 'Updated Lesson 1 Title')

    def test_lesson_update_invalid_link_as_moderator(self):
        """
        Проверяет обновление урока с невалидной ссылкой модератором.
        """
        self.client.force_authenticate(user=self.moderator)
        new_data = {
            'title': 'Updated Lesson 1 Title',
            'content': 'Updated content for lesson 1',
            'video_link': 'https://www.another-site.com/video'
        }
        response = self.client.put(self.detail_update_delete_url(self.lesson1.id), new_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Разрешены только ссылки на YouTube.com.', str(response.data))

    def test_lesson_update_as_regular_user_forbidden(self):
        """
        Проверяет, что обычный пользователь не может обновлять уроки.
        """
        self.client.force_authenticate(user=self.user)
        new_data = {
            'title': 'Attempt to Update Lesson 1',
            'content': 'Some content',
            'video_link': 'https://www.youtube.com/watch?v=tryupdate'
        }
        response = self.client.put(self.detail_update_delete_url(self.lesson1.id), new_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # или 401
        self.assertEqual(Lesson.objects.get(id=self.lesson1.id).title, "Lesson 1") # Урок не изменился

    def test_lesson_delete_as_moderator(self):
        """
        Проверяет удаление урока модератором.
        """
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_update_delete_url(self.lesson1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 1) # Было 2, стал 1

    def test_lesson_delete_as_regular_user_forbidden(self):
        """
        Проверяет, что обычный пользователь не может удалять уроки.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_update_delete_url(self.lesson1.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # или 401
        self.assertEqual(Lesson.objects.count(), 2) # Урок не удален


# --- Тесты для функционала подписки ---
class SubscriptionAPITest(APITestCase):

    def setUp(self):
        self.client = Client()
        # Используем get_user_model() если он настроен правильно
        self.user = User.objects.create_user(username='subscriber_user', password='password123')
        self.another_user = User.objects.create_user(username='another_user', password='password456')

        self.course1 = create_test_course("Course for Subscription")
        self.course2 = create_test_course("Course without Subscription")

        # Установка URL'ов
        self.manage_subscription_url = lambda course_id: reverse('manage_subscription', kwargs={'course_id': course_id})
        self.course_detail_url = lambda pk: reverse('course_detail_with_subscription', kwargs={'pk': pk}) # URL для деталей курса

    def test_subscribe_to_course(self):
        """
        Проверяет успешную подписку на курс.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.manage_subscription_url(self.course1.id))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['message'], 'Подписка добавлена')
        self.assertTrue(response.json()['is_subscribed'])
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(Subscription.objects.get(user=self.user, course=self.course1).user, self.user)

    def test_subscribe_to_course_again_unsubscribes(self):
        """
        Проверяет, что повторный POST на эндпоинт подписки удаляет подписку.
        """
        Subscription.objects.create(user=self.user, course=self.course1)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.manage_subscription_url(self.course1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['message'], 'Подписка удалена')
        self.assertFalse(response.json()['is_subscribed'])
        self.assertEqual(Subscription.objects.count(), 0) # Подписка должна быть удалена

    def test_delete_subscription(self):
        """
        Проверяет явное удаление подписки (через DELETE).
        """
        Subscription.objects.create(user=self.user, course=self.course1)
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.manage_subscription_url(self.course1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['message'], 'Подписка удалена')
        self.assertFalse(response.json()['is_subscribed'])
        self.assertEqual(Subscription.objects.count(), 0)

    def test_delete_nonexistent_subscription(self):
        """
        Проверяет, что удаление несуществующей подписки возвращает ошибку.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.manage_subscription_url(self.course1.id)) # Нет подписки

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['message'], 'Нет активной подписки для удаления')
        self.assertEqual(Subscription.objects.count(), 0)

    def test_subscribe_unauthenticated(self):
        """
        Проверяет, что подписка невозможна без аутентификации.
        """
        response = self.client.post(self.manage_subscription_url(self.course1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_course_detail_shows_subscription_status_for_authenticated(self):
        """
        Проверяет, что детали курса показывают правильный статус подписки для аутентифицированного пользователя.
        """
        # Пользователь подписан
        Subscription.objects.create(user=self.user, course=self.course1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.course_detail_url(self.course1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['is_subscribed']) # Подписан

        # Пользователь не подписан
        response = self.client.get(self.course_detail_url(self.course2.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_subscribed']) # Не подписан

    def test_course_detail_shows_subscription_status_for_unauthenticated(self):
        """
        Проверяет, что детали курса показывают False для is_subscribed для неаутентифицированного пользователя.
        """
        self.client.logout() # Убедимся, что пользователь не аутентифицирован
        response = self.client.get(self.course_detail_url(self.course1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_subscribed']) # Всегда False для анонимов

# --- Тесты для пагинации (пример для списка курсов) ---
class PaginationTest(APITestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='pagetestuser', password='password123')
        self.course_list_url = reverse('course-list') # Предполагаемое имя URL для списка курсов

        # Создаем больше курсов, чем page_size (который по умолч. = 10)
        for i in range(15):
            create_test_course(f"Another Course {i+1}")

    def test_default_pagination(self):
        """
        Проверяет, что пагинация работает по умолчанию.
        """
        response = self.client.get(self.course_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 10) # Должно быть 10 элементов
        self.assertIsNotNone(response.json()['next']) # Должна быть ссылка на следующую страницу
        self.assertIsNone(response.json()['previous']) # Предыдущей страницы нет

    def test_custom_page_size(self):
        """
        Проверяет возможность изменения размера страницы через query param.
        """
        response = self.client.get(f"{self.course_list_url}?page_size=5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)
        self.assertIsNotNone(response.json()['next'])

    def test_pagination_second_page(self):
        """
        Проверяет получение второй страницы.
        """
        response = self.client.get(f"{self.course_list_url}?page=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5) # 15 курсов, 10 на первой странице, 5 на второй
        self.assertIsNotNone(response.json()['previous']) # Предыдущая страница должна быть
        self.assertIsNone(response.json()['next']) # Следующей страницы нет

class SubscriptionViewTest(TestCase):

    def setUp(self):
        """
        Инициализация тестового окружения.
        Создаем пользователя, курс для тестов.
        """
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.course = Course.objects.create(title='Тестовый курс')
        self.nonexistent_course_id = 999 # ID курса, которого не существует

        # URL-адреса для тестирования
        # Используем reverse для получения URL-адресов, включая префикс пространства имен, если он есть
        self.subscribe_url = lambda course_id: reverse('subscribe_course', kwargs={'course_id': course_id})
        self.unsubscribe_url = lambda course_id: reverse('unsubscribe_course', kwargs={'course_id': course_id})

        # Вам нужно будет убедиться, что URL-шаблон 'course_detail' существует
        # и его имя корректно указано в вашем проекте.
        # Если он находится в courses/urls.py, то:
        self.course_detail_url = lambda course_id: reverse('course_detail', kwargs={'course_id': course_id})
        # Если бы он был в users/urls.py с namespace='users':
        # self.course_detail_url = lambda course_id: reverse('users:course_detail', kwargs={'course_id': course_id})


    def test_user_can_subscribe_to_course(self):
        """
        Проверяем, что авторизованный пользователь может подписаться на курс.
        """
        self.client.login(username='testuser', password='password123')
        # По URL 'courses/1/subscribe/'
        response = self.client.post(self.subscribe_url(self.course.id), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())
        self.assertContains(response, 'Вы успешно подписались')

    def test_user_can_unsubscribe_from_course(self):
        """
        Проверяем, что авторизованный пользователь может отписаться от курса.
        """
        # Сначала подписываемся
        Subscription.objects.create(user=self.user, course=self.course)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        self.client.login(username='testuser', password='password123')
        # По URL 'courses/1/unsubscribe/'
        response = self.client.post(self.unsubscribe_url(self.course.id), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())
        self.assertContains(response, 'Вы успешно отписались')

    def test_cannot_subscribe_to_nonexistent_course(self):
        """
        Проверяем, что нельзя подписаться на несуществующий курс.
        """
        self.client.login(username='testuser', password='password123')
        # Попытка подписаться на несуществующий курс
        self.client.post(self.subscribe_url(self.nonexistent_course_id), follow=True)

        # Если get_object_or_404 или Http404 сработали, response.status_code будет 404
        # Но с follow=True, Django пытается отобразить страницу 404.
        # Лучше проверить, что подписка не произошла.
        self.assertEqual(Subscription.objects.count(), 0)

        # Можно также проверить, что если бы мы не использовали follow=True, был бы 404
        # response_no_follow = self.client.post(self.subscribe_url(self.nonexistent_course_id))
        # self.assertEqual(response_no_follow.status_code, 404)


    def test_cannot_subscribe_without_authorization(self):
        """
        Проверяем, что нельзя подписаться без авторизации.
        """
        # Попытка подписаться без входа в систему
        response = self.client.post(self.subscribe_url(self.course.id))

        # @login_required должен перенаправить на страницу входа.
        # Убедитесь, что LOGIN_URL в settings.py настроен правильно (обычно '/accounts/login/')
        # 'next' параметр указывает, куда вернуться после входа.
        expected_redirect_url = f"/accounts/login/?next={self.subscribe_url(self.course.id)}"
        self.assertRedirects(response, expected_redirect_url)
        self.assertFalse(Subscription.objects.exists())

    def test_cannot_unsubscribe_without_authorization(self):
        """
        Проверяем, что нельзя отписаться без авторизации.
        """
        # Попытка отписаться без входа в систему
        response = self.client.post(self.unsubscribe_url(self.course.id))
        expected_redirect_url = f"/accounts/login/?next={self.unsubscribe_url(self.course.id)}"
        self.assertRedirects(response, expected_redirect_url)
        self.assertFalse(Subscription.objects.exists())

    def test_unsubscribe_when_not_subscribed(self):
        """
        Проверяем, что если пользователь не подписан, то отписка не удаляет ничего и выдает предупреждение.
        """
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.unsubscribe_url(self.course.id), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Subscription.objects.exists())
        self.assertContains(response, 'Вы не были подписаны')