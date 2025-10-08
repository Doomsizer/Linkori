import logging
from django.core.management.base import BaseCommand
from Leaderboard.osu_api_service import OsuApiService
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает обновление данных пользователей osu!'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting osu! update manager...'))
        try:
            while True:
                count = OsuApiService.update_all_users_performance()
                self.stdout.write(self.style.SUCCESS(f'Cycle complete, updated {count} users, sleeping 30s...'))
                time.sleep(30)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Interrupted by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running update manager: {str(e)}'))
            logger.exception("Error in osu! update manager")