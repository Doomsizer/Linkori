import requests
import logging
import time
from django.utils import timezone
from datetime import timedelta
from .models import OsuApiApplication, OsuPerformance
from Accounts.models import CustomUser, OsuUsers, UnauthorizedOsuUsers

logger = logging.getLogger(__name__)

class OsuApiService:
    @staticmethod
    def get_active_api_application(max_retries=12, wait_time=5):
        """
        Выбирает активное API-приложение с ротацией и ожиданием.
        Если нет доступного — ждёт и ретраит.
        """
        for attempt in range(max_retries):
            applications = OsuApiApplication.objects.filter(is_active=True).order_by('requests_count')
            for app in applications:
                if app.can_make_request():
                    return app
            if attempt < max_retries - 1:
                logger.warning(f"No available API app, waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
        logger.error("All API applications exhausted after retries")
        return None

    @staticmethod
    def get_user_token():
        now = timezone.now()
        osu_user = OsuUsers.objects.filter(
            token_expires_at__gte=now
        ).order_by('-token_expires_at').first()
        return osu_user.access_token if osu_user else None

    @staticmethod
    def get_client_credentials_token(app=None):
        if app is None:
            app = OsuApiService.get_active_api_application()
            if app is None:
                return None

        if not app.can_make_request():
            logger.warning(f"Cannot get token for {app.name}: limit reached")
            time.sleep(1)
            return None

        success = app.increment_counter()
        if not success:
            time.sleep(1)
            return None

        token_url = 'https://osu.ppy.sh/oauth/token'
        data = {
            'client_id': app.client_id,
            'client_secret': app.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'public'
        }

        try:
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get osu! token: {response.text}")
                return None
            token = response.json()['access_token']
            time.sleep(1)
            return token
        except requests.RequestException as e:
            logger.error(f"Request error during osu! token fetch: {str(e)}")
            return None

    @staticmethod
    def get_user_data(user_id, app=None, use_user_token=False, mode=""):
        if app is None:
            app = OsuApiService.get_active_api_application()
            if app is None:
                return None

        if not app.can_make_request():
            logger.warning(f"Cannot get data for {user_id}: limit reached")
            time.sleep(1)
            return None

        if use_user_token:
            token = OsuApiService.get_user_token()
            if token is None:
                token = OsuApiService.get_client_credentials_token(app)
        else:
            token = OsuApiService.get_client_credentials_token(app)

        if token is None:
            return None

        user_url = f'https://osu.ppy.sh/api/v2/users/{user_id}/{mode}'

        try:
            success = app.increment_counter()
            if not success:
                time.sleep(1)
                return None

            user_response = requests.get(
                user_url,
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )
            time.sleep(1)

            if user_response.status_code == 404:
                logger.warning(f"User {user_id} not found (404)")
                return None
            elif user_response.status_code != 200:
                logger.error(f"Failed to get osu! user data: HTTP {user_response.status_code}")
                return None

            return user_response.json()
        except requests.RequestException as e:
            logger.error(f"Request error during osu! user data fetch: {str(e)}")
            return None

    @classmethod
    def update_user_performance(cls, user, app=None, mode="osu"):
        osu_data = cls.get_user_data(user.osu_id, app, mode=mode)
        if osu_data is None:
            logger.error(f"Failed to get osu! data for user {user.osu_id} in mode {mode}")
            return None

        statistics = osu_data.get('statistics', {})

        try:
            if mode == 'osu':
                user.nick = osu_data.get('username', user.nick)
                user.avatar_url = osu_data.get('avatar_url')
                user.save()

            performance, created = OsuPerformance.objects.get_or_create(
                user=user,
                mode=mode,
                defaults={
                    'global_rank': statistics.get('global_rank'),
                    'country_rank': statistics.get('country_rank'),
                    'pp': statistics.get('pp', 0),
                    'accuracy': statistics.get('hit_accuracy', 0),
                    'playcount': statistics.get('play_count', 0),
                    'level': statistics.get('level', {}).get('current', 0),
                }
            )

            if not created:
                performance.global_rank = statistics.get('global_rank')
                performance.country_rank = statistics.get('country_rank')
                performance.pp = statistics.get('pp', 0)
                performance.accuracy = statistics.get('hit_accuracy', 0)
                performance.playcount = statistics.get('play_count', 0)
                performance.level = statistics.get('level', {}).get('current', 0)
                performance.save()

            logger.info(f"Updated performance for user {user.osu_id} in mode {mode}: {performance.pp}pp")
            return performance
        except Exception as e:
            logger.error(f"Error updating performance for user {user.osu_id}: {str(e)}")
            return None

    @classmethod
    def update_all_modes_for_user(cls, user, app=None):
        results = {}
        modes = ['osu', 'taiko', 'fruits', 'mania']

        for mode in modes:
            try:
                performance = cls.update_user_performance(user, None, mode)
                results[mode] = {
                    'success': performance is not None,
                    'pp': performance.pp if performance else 0
                }
            except Exception as e:
                logger.error(f"Error updating {mode} for user {user.nick}: {str(e)}")
                results[mode] = {'success': False, 'error': str(e)}

        return results

    @classmethod
    def update_all_users_performance(cls):
        users_to_update = UnauthorizedOsuUsers.objects.all()

        logger.info(f"Found {users_to_update.count()} users to update performance")

        update_count = 0
        for user in users_to_update:
            try:
                cls.update_all_modes_for_user(user, None)
                update_count += 1
            except Exception as e:
                logger.error(f"Error updating performance for user {user.osu_id}: {str(e)}")

        return update_count

    @classmethod
    def update_from_osu_ids_list(cls, osu_ids, modes=['osu']):
        """
        Обновляет по списку osu_id с ротацией и ожиданием.
        Создаёт UnauthorizedOsuUsers если нет.
        """
        update_count = 0
        for osu_id in osu_ids:
            try:
                user_obj, created = UnauthorizedOsuUsers.objects.get_or_create(
                    osu_id=osu_id,
                    defaults={'nick': osu_id}
                )
                for mode in modes:
                    cls.update_user_performance(user_obj, None, mode)
                update_count += 1
            except Exception as e:
                logger.error(f"Error updating from ID {osu_id}: {str(e)}")

        logger.info(f"Updated {update_count} users from list")
        return update_count