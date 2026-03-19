from rest_framework.exceptions import ValidationError
from urllib.parse import urlparse


def validate_youtube_link(value):
    """
    Валидатор, проверяющий, что ссылка ведет на YouTube.
    """
    if not value:
        return value  # Разрешаем пустые ссылки

    try:
        parsed_url = urlparse(value)
        if parsed_url.netloc not in ('www.youtube.com', 'youtube.com'):
            raise ValidationError('Разрешены только ссылки на YouTube.com.')
    except Exception as e:
        raise ValidationError(f'Некорректный формате ссылки: {e}')

    return value