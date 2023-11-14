from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser and print the generated token"

    def handle(self, *args, **options):
        # token = uuid.uuid4().hex  # Generate a random token
        password = uuid.uuid4().hex

        try:
            user = User.objects.create_superuser(
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser created successfully"))
            # Writwe the token to the console
            token = user.token
            password = user.password
            self.stdout.write(self.style.SUCCESS(f"Token: {token}"))
            self.stdout.write(self.style.SUCCESS(f"Password: {password}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating superuser: {e}"))
