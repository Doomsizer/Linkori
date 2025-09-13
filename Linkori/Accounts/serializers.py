from rest_framework import serializers
from .models import CustomUser, DiscordUsers, OsuUsers, UnauthorizedOsuUsers

class DiscordUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordUsers
        fields = ['discord_id', 'nick', 'display_name', 'avatar']

class UnauthorizedOsuUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnauthorizedOsuUsers
        fields = ['osu_id', 'nick', 'avatar_url', 'region', 'cities']

class OsuUserSerializer(serializers.ModelSerializer):
    osu = UnauthorizedOsuUsersSerializer(read_only=True)

    class Meta:
        model = OsuUsers
        fields = ['access_token', 'refresh_token', 'token_expires_at', 'osu']

class CustomUserSerializer(serializers.ModelSerializer):
    discord_user = DiscordUserSerializer(read_only=True)
    osu_user = OsuUserSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'discord_user', 'osu_user']