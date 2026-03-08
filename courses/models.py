from django.db import models


class Lesson(models.Model):
    """
    Модель для представления отдельных уроков.
    """
    title = models.CharField(max_length=200, verbose_name="Название урока")
    description = models.TextField(blank=True, verbose_name="Описание урока")
    # Можно добавить дополнительные поля, например:
    # video_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на видео")
    # duration = models.PositiveIntegerField(blank=True, null=True, verbose_name="Длительность (в минутах)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['created_at']


class Course(models.Model):
    """
    Модель для представления курсов, состоящих из уроков.
    """
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = models.TextField(verbose_name="Описание курса")
    preview = models.ImageField(
        upload_to='course_previews/',
        blank=True,
        null=True,
        verbose_name="Превью курса"
    )
    # Связь ManyToMany с уроками. Один курс может содержать много уроков,
    # один урок может быть в разных курсах.
    lessons = models.ManyToManyField(
        Lesson,
        related_name='courses',
        verbose_name="Уроки курса"
    )
    # Дополнительные поля для курса:
    # author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    # price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Цена")
    # published = models.BooleanField(default=False, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['created_at']