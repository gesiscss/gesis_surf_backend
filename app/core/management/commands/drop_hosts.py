"""
Drop all hosts from the database
"""

from core.models import Category, Criteria, Host
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Drop all hosts from the database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Drop all hosts from the database"

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """_summary_"""
        Host.objects.all().delete()
        Category.objects.all().delete()
        Criteria.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All hosts dropped!"))
