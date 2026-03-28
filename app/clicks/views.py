"""
Views for the clicks app.
"""

from clicks.serializers import ClickSerializer
from core.models import Click
from core.pagination import CustomPagination
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class ClickViewSet(viewsets.ModelViewSet):
    """
    Manage clicks in the database.
    """

    serializer_class = ClickSerializer
    queryset = Click.objects.all()
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
        queryset = Click.objects.filter(user=self.request.user)

        domain_id = self.request.query_params.get("domain_id")

        if domain_id is not None:
            queryset = queryset.filter(domain__id=domain_id)

        return queryset.order_by("-click_time")
