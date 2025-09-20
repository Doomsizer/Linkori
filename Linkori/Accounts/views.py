import json
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import logging
from django.shortcuts import redirect
from Leaderboard.regions import REGIONS, CITIES, LINKED
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .services import handle_osu_callback, handle_discord_callback
from .serializers import CustomUserSerializer

logger = logging.getLogger(__name__)


CITY_CODE_MAP = {name: code for code, name in CITIES}

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


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_view(request):
    if request.method == 'GET':
        serializer = CustomUserSerializer(request.user)
        return JsonResponse(serializer.data)
    elif request.method == 'PUT':
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'region' in request.data and request.user.osu_user:
                osu = request.user.osu_user.osu
                osu.region = request.data['region']
                osu.cities = request.data.get('city', osu.cities)
                osu.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data)
    return JsonResponse(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_regions(request):
    regions = [{'code': code, 'name': name} for code, name in REGIONS.items()]
    return JsonResponse({'regions': regions}, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cities(request):
    region = request.GET.get('region')
    if not region or region not in LINKED:
        return JsonResponse({'cities': []}, safe=False)
    cities = []
    for name in LINKED[region]:
        if name in CITY_CODE_MAP:
            code = CITY_CODE_MAP[name]
            cities.append({'code': code, 'name': name})
    return JsonResponse({'cities': cities}, safe=False)