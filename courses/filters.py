import django_filters
from django_filters import FilterSet, DateFilter
from django.utils.translation import gettext_lazy as _


class CourseFilter(FilterSet):
    # --- Простые текстовые фильтры ---

    # Фильтр по названию курса (частичное совпадение, игнорируя регистр)
    title = django_filters.CharFilter(
        field_name='title',        # Поле в модели Course
        lookup_expr='icontains',   # Искать, если поле содержит введенную строку (регистронезависимо)
        label=_("Title contains")  # Метка для формы фильтра (если вы строите ее вручную или через django-admin)
    )

    # --- Фильтры по датам ---

    # Фильтр по дате начала курса (больше или равно)
    start_date_gte = DateFilter(
        field_name='start_date',
        lookup_expr='gte',
        label=_("Start date from")
    )

    # Фильтр по дате начала курса (меньше или равно)
    start_date_lte = DateFilter(
        field_name='start_date',
        lookup_expr='lte',
        label=_("Start date to")
    )

    # Фильтр по дате окончания курса (больше или равно)
    end_date_gte = DateFilter(
        field_name='end_date',
        lookup_expr='gte',
        label=_("End date from")
    )

    # Фильтр по дате окончания курса (меньше или равно)
    end_date_lte = DateFilter(
        field_name='end_date',
        lookup_expr='lte',
        label=_("End date to")
    )

    # --- Фильтры по булевым полям ---

    # Фильтр по статусу публикации (точное совпадение)
    # Предполагается, что у Course есть булево поле 'is_published'
    is_published = django_filters.BooleanFilter(
        field_name='is_published',
        lookup_expr='exact',
        label=_("Is published?")
    )

    # --- Фильтры по связанным полям (ForeignKey) ---

    # Фильтр по ID автора
    # Предполагается, что у Course есть ForeignKey к модели Author
    author_id = django_filters.NumberFilter(
        field_name='author__id',  # Фильтруем по ID связанного объекта Author
        lookup_expr='exact',
        label=_("Author ID")
    )

    # Фильтр по названию категории (частичное совпадение, регистронезависимо)
    # Предполагается, что у Course есть ForeignKey к модели Category
    category_name = django_filters.CharFilter(
        field_name='category__name', # Обращаемся к полю 'name' в модели Category
        lookup_expr='icontains',
        label=_("Category name contains")
    )

