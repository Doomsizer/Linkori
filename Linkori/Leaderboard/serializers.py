from rest_framework import serializers
from .models import OsuPerformance
from Accounts.serializers import UnauthorizedOsuUsersSerializer

class OsuPerformanceSerializer(serializers.ModelSerializer):
    user = UnauthorizedOsuUsersSerializer(read_only=True)
    class Meta:
        model = OsuPerformance
        fields = ['user', 'global_rank', 'country_rank', 'pp', 'mode']