import logging
from django.core.management.base import BaseCommand
from Leaderboard.osu_api_service import OsuApiService
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Запускает менеджер API osu! для постоянного обновления данных пользователей'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting osu! API manager...'))
        try:
            while True:
                OsuApiService.update_all_users_performance()
                self.stdout.write(self.style.SUCCESS('Cycle complete, sleeping 30s...'))
                time.sleep(30)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Interrupted by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running API manager: {str(e)}'))
            logger.exception("Error in osu! API manager")