from rest_framework.pagination import PageNumberPagination


class DonorPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50