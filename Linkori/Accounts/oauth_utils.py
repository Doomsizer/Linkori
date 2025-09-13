from django.conf import settings
from django.utils import timezone
from .exceptions import TokenError
from .models import UnauthorizedOsuUsers, OsuUsers, DiscordUsers
import requests
import logging

logger = logging.getLogger(__name__)

def process_osu_token(code, redirect_uri=None):
    token_url = 'https://osu.ppy.sh/oauth/token'
    if redirect_uri is None:
        redirect_uri = settings.OSU_REDIRECT_URI

    data = {
        'client_id': settings.OSU_CLIENT_ID,
        'client_secret': settings.OSU_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }

    try:
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            error_details = response.text if response.text else f"HTTP {response.status_code}"
            logger.error(f"Failed to get osu! token: {error_details}")
            raise TokenError("osu", error_details)

        token_data = response.json()
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'expires_in': token_data['expires_in'],
            'expires_at': timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
        }
    except requests.RequestException as e:
        logger.error(f"Request error during osu! token fetch: {str(e)}")
        raise TokenError("osu", str(e))

def get_osu_user_data(token):
    url = 'https://osu.ppy.sh/api/v2/me'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            logger.warning(f"User not found (404 - likely banned/restricted)")
            return None
        elif response.status_code == 401:
            logger.warning(f"Unauthorized (401 - token invalid or expired)")
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting osu! user data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception getting osu! user data: {str(e)}")
        return None

def create_or_update_osu_user(osu_id, nick, token_data, avatar=None):
    uosu_user, created = UnauthorizedOsuUsers.objects.get_or_create(
        osu_id=osu_id,
        defaults={
            'nick': nick,
            'avatar_url': avatar,
        }
    )

    if not created:
        uosu_user.nick = nick
        uosu_user.avatar_url = avatar
        uosu_user.save()

    osu_user, created = OsuUsers.objects.get_or_create(
        osu=uosu_user,
        defaults={
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expires_at': token_data['expires_at']
        }
    )

    if not created:
        osu_user.access_token = token_data['access_token']
        osu_user.refresh_token = token_data['refresh_token']
        osu_user.token_expires_at = token_data['expires_at']
        osu_user.save()

    return osu_user

def process_discord_token(code, redirect_uri=None):
    token_url = 'https://discord.com/api/oauth2/token'
    if redirect_uri is None:
        redirect_uri = settings.DISCORD_REDIRECT_URI

    data = {
        'client_id': settings.DISCORD_CLIENT_ID,
        'client_secret': settings.DISCORD_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }

    try:
        response = requests.post(token_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if response.status_code != 200:
            error_details = response.text if response.text else f"HTTP {response.status_code}"
            logger.error(f"Failed to get Discord token: {error_details}")
            raise TokenError("discord", error_details)

        token_data = response.json()
        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'expires_in': token_data['expires_in'],
            'expires_at': timezone.now() + timezone.timedelta(seconds=token_data['expires_in'])
        }
    except requests.RequestException as e:
        logger.error(f"Request error during Discord token fetch: {str(e)}")
        raise TokenError("discord", str(e))

def get_discord_user_data(token):
    url = 'https://discord.com/api/users/@me'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            logger.warning(f"User not found (404)")
            return None
        elif response.status_code == 401:
            logger.warning(f"Unauthorized (401 - token invalid or expired)")
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting Discord user data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception getting Discord user data: {str(e)}")
        return None

def create_or_update_discord_user(discord_id, nick, display_name, token_data, avatar=None):
    discord_user, created = DiscordUsers.objects.get_or_create(
        discord_id=discord_id,
        defaults={
            'nick': nick,
            'display_name': display_name,
            'avatar': avatar,
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expires_at': token_data['expires_at']
        }
    )

    if not created:
        discord_user.nick = nick
        discord_user.display_name = display_name
        discord_user.avatar = avatar
        discord_user.access_token = token_data['access_token']
        discord_user.refresh_token = token_data['refresh_token']
        discord_user.token_expires_at = token_data['expires_at']
        discord_user.save()

    return discord_user