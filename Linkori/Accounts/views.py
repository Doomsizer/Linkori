import json
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import logging
from django.shortcuts import redirect
from urllib.parse import urlencode
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .services import handle_osu_callback, handle_discord_callback
from .models import CustomUser
from .serializers import CustomUserSerializer

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def osu_login_view(request):
    logger.info("Redirecting to osu! authorization")
    redirect_uri = settings.OSU_REDIRECT_URI
    state = request.GET.get('state', '')
    osu_auth_url = (
        f"https://osu.ppy.sh/oauth/authorize?"
        f"client_id={settings.OSU_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=identify+public&"
        f"state={state}"
    )
    return JsonResponse({'url': osu_auth_url, 'status': 'success'})

@api_view(['GET'])
@permission_classes([AllowAny])
def discord_login_view(request):
    logger.info("Redirecting to Discord authorization")
    redirect_uri = settings.DISCORD_REDIRECT_URI
    state = request.GET.get('state', '')
    discord_auth_url = (
        f"https://discord.com/oauth2/authorize?"
        f"client_id={settings.DISCORD_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=identify+guilds&"
        f"state={state}"
    )
    return JsonResponse({'url': discord_auth_url, 'status': 'success'})

@api_view(['GET'])
@permission_classes([AllowAny])
def osu_callback_view(request):
    state = request.GET.get('state', '')
    if state:
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(state)
            request.user = auth.get_user(validated_token)
            logger.info(f"Authenticated user {request.user.identifier} via state token in osu_callback")
        except InvalidToken as e:
            logger.warning(f"Invalid state token in osu_callback: {str(e)}")

    response = handle_osu_callback(request)
    if isinstance(response, JsonResponse) and response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        access_token = data.get('access')
        logger.info(f"osu! callback response: {data}")
        if access_token:
            return redirect(f'/callback/osu?access={access_token}')
    logger.warning("Failed osu! callback, redirecting to /login")
    return redirect('/login')

@api_view(['GET'])
@permission_classes([AllowAny])
def discord_callback_view(request):
    state = request.GET.get('state', '')
    if state:
        try:
            auth = JWTAuthentication()
            validated_token = auth.get_validated_token(state)
            request.user = auth.get_user(validated_token)
            logger.info(f"Authenticated user {request.user.identifier} via state token in discord_callback")
        except InvalidToken as e:
            logger.warning(f"Invalid state token in discord_callback: {str(e)}")

    response = handle_discord_callback(request)
    if isinstance(response, JsonResponse) and response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        access_token = data.get('access')
        logger.info(f"Discord callback response: {data}")
        if access_token:
            return redirect(f'/callback/discord?access={access_token}')
    logger.warning("Failed Discord callback, redirecting to /login")
    return redirect('/login')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view(request):
    logger.info(f"Headers: {request.headers}")
    logger.info(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
    serializer = CustomUserSerializer(request.user)
    return JsonResponse(serializer.data, safe=False)