from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 10  # Количество элементов на странице
    page_size_query_param = 'page_size' # Параметр для изменения размера страницы в запросе (e.g., ?page_size=5)
    max_page_size = 50 # Максимальное количество элементов, которое может запросить пользователь