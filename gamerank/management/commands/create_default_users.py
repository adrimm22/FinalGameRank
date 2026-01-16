from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gamerank.models import UserSettings


class Command(BaseCommand):
    help = "Creates default users for testing/login purposes"

    def handle(self, *args, **kwargs):
        default_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'testuser',
                'password': 'test123',
                'email': 'testuser@example.com',
            },
            {
                'username': 'gamer1',
                'password': 'gamer123',
                'email': 'gamer1@example.com',
            },
            {
                'username': 'gamer2',
                'password': 'gamer123',
                'email': 'gamer2@example.com',
            },
        ]

        created_count = 0
        existing_count = 0

        for user_data in default_users:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )
            
            if created:
                user.set_password(password)
                user.save()
                UserSettings.objects.get_or_create(user=user)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created user: {username} (password: {password})')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ User already exists: {username}')
                )
                existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nFinished! Created {created_count} user(s), {existing_count} already existed.'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\nDefault users created:\n'
                '  - admin / admin123 (superuser)\n'
                '  - testuser / test123\n'
                '  - gamer1 / gamer123\n'
                '  - gamer2 / gamer123'
            )
        )
