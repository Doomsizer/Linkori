import logging
import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import TokenError
from .models import CustomUser, UnauthorizedOsuUsers, DiscordUsers
from Leaderboard.models import ServerMember
from DiscordBot.models import DiscordServer
from .oauth_utils import process_osu_token, get_osu_user_data, create_or_update_osu_user, process_discord_token, get_discord_user_data, create_or_update_discord_user

logger = logging.getLogger(__name__)

def get_custom_user_by_osu_id(osu_id):
    try:
        unauthorized_user = UnauthorizedOsuUsers.objects.get(osu_id=osu_id)
        osu_user = unauthorized_user.tokens
        custom_user = osu_user.user
        return custom_user
    except (UnauthorizedOsuUsers.DoesNotExist, AttributeError):
        return None

def get_custom_user_by_discord_id(discord_id):
    try:
        discord_user = DiscordUsers.objects.get(discord_id=discord_id)
        custom_user = discord_user.user
        return custom_user
    except (DiscordUsers.DoesNotExist, AttributeError):
        return None


def handle_osu_callback(request):
    logger.info(f"Processing osu_callback with params: {request.GET}, Headers: {request.headers}")
    code = request.GET.get('code')
    try:
        token_data = process_osu_token(code)
        osu_data = get_osu_user_data(token_data['access_token'])
        if not osu_data:
            logger.error("Failed to get osu! user data")
            return JsonResponse({'message': 'Failed to get osu! user data', 'status': 'fail'},
                                status=status.HTTP_400_BAD_REQUEST)

        osu_id = osu_data['id']
        nick = osu_data['username']
        avatar = osu_data.get('avatar_url')

        osu_user = create_or_update_osu_user(osu_id=osu_id, nick=nick, avatar=avatar, token_data=token_data)

        is_special_user = str(osu_id) == '24625610'

        existing_user = get_custom_user_by_osu_id(osu_id)

        if existing_user:
            if request.user.is_authenticated and existing_user != request.user:
                logger.info(
                    f"Rebinding osu! user {osu_id} from {existing_user.identifier} to {request.user.identifier}")
                existing_user.delete()
                request.user.osu_user = osu_user

                if is_special_user:
                    request.user.is_staff = True
                    request.user.is_superuser = True

                request.user.save()
                user = request.user
            elif existing_user == request.user:
                logger.info(f"User {request.user.identifier} already authorized with osu! {osu_id}")

                if is_special_user:
                    existing_user.is_staff = True
                    existing_user.is_superuser = True
                    existing_user.save()

                user = request.user
            else:
                logger.info(f"Logging in existing osu! user {existing_user.identifier}")

                if is_special_user:
                    existing_user.is_staff = True
                    existing_user.is_superuser = True

                existing_user.save()
                user = existing_user
        elif request.user.is_authenticated:
            logger.info(f"Binding osu! user {osu_id} to authenticated user {request.user.identifier}")
            request.user.osu_user = osu_user

            if is_special_user:
                request.user.is_staff = True
                request.user.is_superuser = True

            request.user.save()
            user = request.user
        else:
            user = CustomUser.objects.create_user(
                osu_id=osu_id,
                is_staff=is_special_user,
                is_superuser=is_special_user
            )
            user.osu_user = osu_user
            user.save()
            logger.info(
                f"Created new CustomUser for osu! user {osu_id} with staff={is_special_user}, superuser={is_special_user}")

        refresh = RefreshToken.for_user(user)
        response = JsonResponse({
            'access': str(refresh.access_token),
            'status': 'success'
        })
        logger.info(f"Set refresh_token cookie for user {user.identifier}")
        return response

    except TokenError as e:
        logger.error(f"OAuth error: {str(e)}")
        return JsonResponse({'message': str(e), 'status': 'fail'}, status=status.HTTP_400_BAD_REQUEST)

def handle_discord_callback(request):
    logger.info(f"Processing discord_callback with params: {request.GET}, Headers: {request.headers}")
    code = request.GET.get('code')
    try:
        token_data = process_discord_token(code)
        discord_data = get_discord_user_data(token_data['access_token'])
        if not discord_data:
            logger.error("Failed to get Discord user data")
            return JsonResponse({'message': 'Failed to get Discord user data', 'status': 'fail'}, status=400)

        discord_id = discord_data['id']
        nick = discord_data['username']
        display_name = discord_data.get('global_name')
        try:
            avatar = discord_data['avatar']
        except Exception:
            logger.info(f"Discord user {discord_id} doesnt have avatar")
            avatar = None

        discord_user = create_or_update_discord_user(
            discord_id=discord_id,
            nick=nick,
            display_name=display_name,
            avatar=avatar,
            token_data=token_data
        )

        existing_user = get_custom_user_by_discord_id(discord_id)

        if existing_user:
            if request.user.is_authenticated and existing_user != request.user:
                logger.info(f"Rebinding Discord user {discord_id} from {existing_user.identifier} to {request.user.identifier}")
                existing_user.delete()
                request.user.discord_user = discord_user
                request.user.save()
                user = request.user
            elif existing_user == request.user:
                logger.info(f"User {request.user.identifier} already authorized with Discord {discord_id}")
                user = request.user
            else:
                logger.info(f"Logging in existing Discord user {existing_user.identifier}")
                user = existing_user
                user.save()
        elif request.user.is_authenticated:
            logger.info(f"Binding Discord user {discord_id} to authenticated user {request.user.identifier}")
            request.user.discord_user = discord_user
            request.user.save()
            user = request.user
        else:
            user = CustomUser.objects.create_user(discord_id=discord_id)
            user.discord_user = discord_user
            user.save()
            logger.info(f"Created new CustomUser for Discord user {discord_id}")

        try:
            guilds_url = 'https://discord.com/api/users/@me/guilds'
            headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
            response = requests.get(guilds_url, headers=headers, timeout=5)
            if response.status_code == 200:
                guilds_data = response.json()
                bot_servers = set(DiscordServer.objects.values_list('server_id', flat=True))
                for guild in guilds_data:
                    if guild['id'] in bot_servers:
                        server = DiscordServer.objects.get(server_id=guild['id'])
                        ServerMember.objects.get_or_create(
                            user=user,
                            server=server
                        )
                        logger.info(f"Added ServerMember for user {user.identifier} on server {server.server_name}")
            else:
                logger.warning(f"Failed to fetch guilds for Discord user {discord_id}, status: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error fetching guilds for Discord user {discord_id}: {str(e)}")

        refresh = RefreshToken.for_user(user)
        response = JsonResponse({
            'access': str(refresh.access_token),
            'status': 'success'
        })
        logger.info(f"Set refresh_token cookie for user {user.identifier}")
        return response

    except TokenError as e:
        logger.error(f"OAuth error: {str(e)}")
        return JsonResponse({'message': str(e), 'status': 'fail'}, status=400)