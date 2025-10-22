import logging
from django.core.management.base import BaseCommand
from Leaderboard.osu_api_service import OsuApiService
from Leaderboard.models import OsuApiApplication
from django.utils import timezone
import os
from dotenv import load_dotenv
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает обновление данных пользователей osu!'

    def ensure_api_applications(self):
        """Проверяет наличие api приложений для парсинга, создает их, если не находит"""
        load_dotenv()

        api_apps = [
            {
                'name': os.getenv('VEEX_NAME'),
                'client_id': os.getenv('VEEX_CLIENT_ID'),
                'client_secret': os.getenv('VEEX_CLIENT_SECRET'),
            },
            {
                'name': os.getenv('REPPL_NAME'),
                'client_id': os.getenv('REPPL_CLIENT_ID'),
                'client_secret': os.getenv('REPPL_CLIENT_SECRET'),
            },
        ]

        for app in api_apps:
            if not all([app['name'], app['client_id'], app['client_secret']]):
                self.stdout.write(
                    self.style.ERROR(f'Missing .env variables for {app["name"]}')
                )
                continue

            existing_app = OsuApiApplication.objects.filter(
                name=app['name'],
                client_id=app['client_id'],
                client_secret=app['client_secret']
            ).first()

            if not existing_app:
                OsuApiApplication.objects.create(
                    name=app['name'],
                    client_id=app['client_id'],
                    client_secret=app['client_secret'],
                    is_active=True,
                    requests_count=0,
                    error_times=[],
                    reset_time=timezone.now(),
                    access_token='',
                    token_expires_at=None
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created OsuApiApplication for {app["name"]}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'OsuApiApplication for {app["name"]} already exists')
                )

        required_names = [app['name'] for app in api_apps]
        existing_names = OsuApiApplication.objects.filter(
            name__in=required_names
        ).values_list('name', flat=True)

        if set(required_names) != set(existing_names):
            missing = set(required_names) - set(existing_names)
            raise Exception(f'Missing required API applications: {missing}')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting osu! update manager...'))

        try:
            self.ensure_api_applications()

            while True:
                count = OsuApiService.update_all_users_performance()
                self.stdout.write(
                    self.style.SUCCESS(f'Cycle complete, updated {count} users, sleeping 30s...')
                )
                time.sleep(30)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Interrupted by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running update manager: {str(e)}'))
            logger.exception("Error in osu! update manager")