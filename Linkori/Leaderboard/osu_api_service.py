import requests
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.utils import timezone
from datetime import timedelta
from Accounts.models import OsuUsers, UnauthorizedOsuUsers
from .models import OsuApiApplication, OsuPerformance

logger = logging.getLogger(__name__)

OSU_RETRY_ATTEMPTS = 12
OSU_RETRY_WAIT_BASE = 5
OSU_RATE_LIMIT = 60
MAX_WORKERS = 8

class OsuApiService:
    session = requests.Session()

    @staticmethod
    def get_active_api_application():
        for attempt in range(OSU_RETRY_ATTEMPTS):
            applications = OsuApiApplication.objects.filter(is_active=True).order_by('requests_count')
            for app in applications:
                app.reset_errors_if_needed()
                if app.can_make_request():
                    return app
            if attempt < OSU_RETRY_ATTEMPTS - 1:
                wait_time = OSU_RETRY_WAIT_BASE * (2 ** attempt)
                logger.warning(f"No available API app, waiting {wait_time}s (attempt {attempt+1}/{OSU_RETRY_ATTEMPTS})")
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

        now = timezone.now()
        if app.access_token and app.token_expires_at and app.token_expires_at > now + timedelta(minutes=5):
            return app.access_token

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
            response = OsuApiService.session.post(token_url, data=data, timeout=10)
            if response.status_code != 200:
                error_msg = response.json().get('error', 'Unknown error')
                logger.error(f"Failed to get osu! token for {app.name}: {error_msg}")
                if error_msg == 'invalid_client':
                    app.increment_error()
                return None
            data = response.json()
            app.access_token = data['access_token']
            app.token_expires_at = now + timedelta(seconds=data['expires_in'])
            app.save()
            return app.access_token
        except requests.RequestException as e:
            logger.error(f"Request error getting token for {app.name}: {str(e)}")
            app.increment_error()
            return None

    @staticmethod
    def get_user_data(user_id, app=None, use_user_token=False, mode=""):
        if app is None:
            app = OsuApiService.get_active_api_application()
            if app is None:
                logger.warning("No active app for user data fetch")
                return None

        if not app.can_make_request():
            logger.warning(f"Cannot get data for user {user_id} with {app.name}: limit reached")
            time.sleep(1)
            return None

        if use_user_token:
            token = OsuApiService.get_user_token()
            if token is None:
                token = OsuApiService.get_client_credentials_token(app)
        else:
            token = OsuApiService.get_client_credentials_token(app)

        if token is None:
            logger.warning(f"No token for user {user_id} with {app.name}")
            return None

        user_url = f'https://osu.ppy.sh/api/v2/users/{user_id}/{mode}'

        try:
            success = app.increment_counter()
            if not success:
                logger.warning(f"Cannot increment counter for {app.name} for user {user_id}")
                time.sleep(1)
                return None

            user_response = OsuApiService.session.get(
                user_url,
                headers={'Authorization': f'Bearer {token}'},
                timeout=10
            )

            if user_response.status_code == 404:
                logger.warning(f"User {user_id} not found (404)")
                return None
            elif user_response.status_code != 200:
                error_msg = user_response.json().get('error', 'Unknown error') if user_response.text else 'No response'
                logger.error(f"Failed to get user data for {user_id}: HTTP {user_response.status_code}, {error_msg}")
                if error_msg == 'invalid_client':
                    app.increment_error()
                return None

            return user_response.json()
        except requests.RequestException as e:
            logger.error(f"Request error for user {user_id}: {str(e)}")
            app.increment_error()
            return None

    @classmethod
    def update_user_performance(cls, user, app=None, mode="osu"):
        logger.debug(f"Updating performance for user {user.osu_id} mode {mode} with app {app.name if app else 'None'}")
        osu_data = cls.get_user_data(user.osu_id, app, mode=mode)
        if osu_data is None:
            logger.warning(f"Failed to get data for user {user.osu_id} mode {mode}")
            return None

        statistics = osu_data.get('statistics', {})

        try:
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

            logger.info(f"Updated performance for {user.osu_id} mode {mode}: {performance.pp}pp")
            return performance
        except Exception as e:
            logger.error(f"Error saving performance for {user.osu_id} mode {mode}: {str(e)}")
            return None

    @classmethod
    def update_all_modes_for_user(cls, user):
        logger.info(f"Starting all modes update for user {user.osu_id}")
        app = cls.get_active_api_application()
        if app is None:
            logger.warning(f"No app for user {user.osu_id}")
            return {}

        osu_data = cls.get_user_data(user.osu_id, app, mode='osu')
        if osu_data is None:
            logger.warning(f"Failed to get base data for user {user.osu_id}")
            return {}

        try:
            user.nick = osu_data.get('username', user.nick)
            user.avatar_url = osu_data.get('avatar_url')
            user.save()
            logger.debug(f"Updated nick/avatar for {user.osu_id}")
        except Exception as e:
            logger.error(f"Error saving user {user.osu_id}: {str(e)}")

        results = {}
        modes = ['osu', 'taiko', 'fruits', 'mania']

        for mode in modes:
            try:
                performance = cls.update_user_performance(user, app, mode)
                results[mode] = {
                    'success': performance is not None,
                    'pp': performance.pp if performance else 0
                }
            except Exception as e:
                logger.error(f"Error updating mode {mode} for {user.osu_id}: {str(e)}")
                results[mode] = {'success': False, 'error': str(e)}

        return results

    @classmethod
    def _update_single_user(cls, user):
        try:
            cls.update_all_modes_for_user(user)
            return 1
        except Exception as e:
            logger.error(f"Error updating single user {user.osu_id}: {str(e)}")
            return 0

    @classmethod
    def update_all_users_performance(cls):
        apps = list(OsuApiApplication.objects.filter(is_active=True))
        if not apps:
            logger.error("No active apps for parsing user stats")
            return 0

        users = list(UnauthorizedOsuUsers.objects.all())
        if not users:
            logger.info("No users to update")
            return 0

        logger.info(f"Starting update for {len(users)} users with {len(apps)} apps")

        num_workers = min(MAX_WORKERS, len(apps) * 2)
        update_count = 0
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(cls._update_single_user, user) for user in users]
            for future in as_completed(futures):
                try:
                    count = future.result()
                    update_count += count
                except Exception as e:
                    logger.error(f"Future error: {str(e)}")

        logger.info(f"Total updated users: {update_count}")
        return update_count

    @classmethod
    def update_from_osu_ids_list(cls, osu_ids, modes=['osu']):
        update_count = 0
        for osu_id in osu_ids:
            try:
                user_obj, created = UnauthorizedOsuUsers.objects.get_or_create(
                    osu_id=osu_id,
                    defaults={'nick': str(osu_id)}
                )
                for mode in modes:
                    cls.update_user_performance(user_obj, None, mode)
                update_count += 1
            except Exception as e:
                logger.error(f"Error updating from ID {osu_id}: {str(e)}")

        return update_count