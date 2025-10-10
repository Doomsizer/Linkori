from rest_framework.permissions import AllowAny
from Accounts.permissions import IsLinked, IsAuthenticated
from django.db.models import Case, When, Value, IntegerField, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .regions import CITIES
from .models import OsuPerformance, ServerMember
from .serializers import OsuPerformanceSerializer
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from DiscordBot.models import DiscordServer
from Accounts.models import CustomUser
from DiscordBot.serializers import DiscordServerSerializer
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
def get_mainboard(request):
    """
    Таблица по умолчанию на главной /leaderboards с пагинацией
    """
    try:
        entries = OsuPerformance.objects.filter(mode="osu").select_related('user').annotate(
            sort_priority=Case(
                When(pp__gt=0, global_rank__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by(
            '-sort_priority',
            '-pp',
            F('global_rank').asc(nulls_last=True)
        )

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(entries, request)

        serializer = OsuPerformanceSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_servers(request):
    """
    Получить все серверы, на которых состоит авторизованный пользователь.
    Возвращает список серверов с server_id, server_name, server_icon, member_count
    """
    try:
        user = request.user

        server_memberships = ServerMember.objects.filter(user=user).select_related('server')

        servers = [membership.server for membership in server_memberships]

        serializer = DiscordServerSerializer(servers, many=True)

        return Response(serializer.data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsLinked])
def get_leaderboard(request):
    """
    Таблица для авторизованных пользователей. Поддерживает фильтрацию.
    Фильтры:
    - mode: режим игры (osu, taiko, fruits, mania), по умолчанию 'osu'
    - region: код региона фильтрация по региону
    - city: код города фильтрация по городу
    - server: id сервера фильтрация по серверу
    """
    logger.error(request.user.is_linked)
    try:
        mode = request.GET.get('mode', 'osu')
        region_code = request.GET.get('region', None)
        city_code = request.GET.get('city', None)
        server_id = request.GET.get('server', None)

        entries = OsuPerformance.objects.all().select_related('user')

        entries = entries.filter(mode=mode)

        if server_id:
            server_members = ServerMember.objects.filter(server__server_id=server_id).values_list('user_id', flat=True)

            custom_users = CustomUser.objects.filter(id__in=server_members, osu_user__isnull=False)
            osu_ids = custom_users.values_list('osu_user__osu__osu_id', flat=True)

            entries = entries.filter(user__osu_id__in=osu_ids)

        if region_code:
            entries = entries.filter(user__region=region_code)

            if city_code:
                entries = entries.filter(user__cities=city_code)

        entries = entries.annotate(
            sort_priority=Case(
                When(pp__gt=0, global_rank__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by(
            '-sort_priority',
            '-pp',
            F('global_rank').asc(nulls_last=True)
        )

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(entries, request)

        serializer = OsuPerformanceSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_cities(request):
    cities = [{'code': code, 'name': name} for code, name in CITIES]
    return JsonResponse({'cities': cities}, safe=False)