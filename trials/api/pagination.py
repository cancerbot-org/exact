import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class TrialsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 200
    page_query_param = 'page'

    def get_paginated_response(self, data, extra_keys: dict = None):
        total_items = self.page.paginator.count
        page_size = self.page.paginator.per_page
        total_pages = math.ceil(total_items / page_size)

        if extra_keys is None:
            extra_keys = {}

        return Response({
            'results': data,
            'count': total_pages,
            'itemsTotalCount': total_items,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            **extra_keys,
        })
