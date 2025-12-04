"""
Views for the scroll app.
"""

from core.models import Scroll
from core.pagination import CustomPagination
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from scrolls.serializers import ScrollSerializer


class ScrollViewSet(viewsets.ModelViewSet):
    """
    Manage scrolls in the database.
    """

    serializer_class = ScrollSerializer
    queryset = Scroll.objects.all()
    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Return objects for the current authenticated user only.
        """
        queryset = Scroll.objects.filter(user=self.request.user)

        domain_id = self.request.query_params.get("domain_id")

        if domain_id is not None:
            queryset = queryset.filter(domain__id=domain_id)

        return queryset.order_by("-scroll_time")
