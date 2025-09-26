from rest_framework import serializers
from .models import DiscordServer

class DiscordServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordServer
        fields = ['server_id', 'server_name', 'server_icon', 'member_count']