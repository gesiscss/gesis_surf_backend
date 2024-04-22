"""
Drop all hosts from the database
"""

from django.core.management.base import BaseCommand
from core.models import Host, Category, Criteria


class Command(BaseCommand):
    """_summary_

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Drop all hosts from the database"

    def handle(self, *args, **options):
        """_summary_"""
        Host.objects.all().delete()
        Category.objects.all().delete()
        Criteria.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("All hosts dropped!"))
