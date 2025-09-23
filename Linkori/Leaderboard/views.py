from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Case, When, Value, IntegerField, F
from rest_framework.decorators import api_view, permission_classes
from .models import OsuPerformance
from .serializers import OsuPerformanceSerializer
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse

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
