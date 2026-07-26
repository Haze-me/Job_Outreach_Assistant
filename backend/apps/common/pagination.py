"""Pagination policy for every list endpoint."""

from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """Page-number pagination with a client-controllable, capped page size.

    The response includes ``page``/``total_pages`` on top of DRF's defaults so
    the frontend can render numbered pagination without extra requests.
    """

    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer", "example": 123},
                "total_pages": {"type": "integer", "example": 7},
                "page": {"type": "integer", "example": 1},
                "page_size": {"type": "integer", "example": 20},
                "next": {"type": "string", "nullable": True, "format": "uri"},
                "previous": {"type": "string", "nullable": True, "format": "uri"},
                "results": schema,
            },
        }
