from rest_framework import serializers
from .models import CustomUser, DiscordUsers, OsuUsers, UnauthorizedOsuUsers, AVATAR_SOURCES, NICK_SOURCES
from Leaderboard.regions import REGIONS, LINKED, CITIES
import requests
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)

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
    avatar_source = serializers.ChoiceField(choices=AVATAR_SOURCES, required=False)
    nick_source = serializers.ChoiceField(choices=NICK_SOURCES, required=False)
    region = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    region_display = serializers.SerializerMethodField()
    city_display = serializers.SerializerMethodField()
    displayed_avatar_url = serializers.SerializerMethodField()
    displayed_nick = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'discord_user', 'osu_user', 'avatar_source', 'nick_source', 'region', 'city',
                  'region_display', 'city_display', 'displayed_avatar_url', 'displayed_nick']

    def get_region(self, obj):
        if obj.osu_user and obj.osu_user.osu:
            return obj.osu_user.osu.region
        return None

    def get_city(self, obj):
        if obj.osu_user and obj.osu_user.osu:
            return obj.osu_user.osu.cities
        return None

    def get_region_display(self, obj):
        region = self.get_region(obj)
        return REGIONS.get(region, '')

    def get_city_display(self, obj):
        city = self.get_city(obj)
        for code, name in CITIES:
            if code == city:
                return name
        return ''

    def get_displayed_avatar_url(self, obj):
        if obj.avatar_source == 'osu' and obj.osu_user:
            avatar_url = obj.osu_user.osu.avatar_url
            return self._validate_osu_avatar(avatar_url)
        elif obj.avatar_source == 'discord' and obj.discord_user:
            return self._validate_discord_avatar(obj.discord_user)
        elif not obj.avatar_source:
            if obj.osu_user and obj.osu_user.osu.avatar_url:
                return self._validate_osu_avatar(obj.osu_user.osu.avatar_url)
            elif obj.discord_user and obj.discord_user.avatar:
                return self._validate_discord_avatar(obj.discord_user)
            return None
        return None

    def _validate_osu_avatar(self, avatar_url):
        if not avatar_url:
            return None
        parsed_url = urllib.parse.urlparse(avatar_url)
        if not (parsed_url.scheme in ['http', 'https'] and
                parsed_url.netloc in ['a.ppy.sh', 's.ppy.sh']):
            return None
        full_path = parsed_url.path + ('?' + parsed_url.query if parsed_url.query else '')
        if not re.search(r'\.(png|jpg|jpeg|gif)', full_path, re.IGNORECASE):
            return None
        try:
            response = requests.head(avatar_url, timeout=2)
            if response.status_code != 200:
                return None
        except requests.RequestException:
            return None
        return avatar_url

    def _validate_discord_avatar(self, discord_user):
        avatar = discord_user.avatar
        if not avatar or len(avatar) < 2:
            return None
        ext = '.gif' if avatar.startswith('a_') else '.png'
        discord_avatar_url = f"https://cdn.discordapp.com/avatars/{discord_user.discord_id}/{avatar}{ext}?size=128"
        return discord_avatar_url

    def get_displayed_nick(self, obj):
        if obj.nick_source == 'osu' and obj.osu_user:
            return obj.osu_user.osu.nick
        elif obj.nick_source == 'discord_username' and obj.discord_user:
            return obj.discord_user.nick
        elif obj.nick_source == 'discord_display_name' and obj.discord_user:
            return obj.discord_user.display_name
        elif not obj.nick_source:
            if obj.osu_user and obj.osu_user.osu.nick:
                return obj.osu_user.osu.nick
            elif obj.discord_user and obj.discord_user.nick:
                return obj.discord_user.nick
            return None
        return None

    def validate_avatar_source(self, value):
        if value == 'osu' and not self.instance.osu_user:
            raise serializers.ValidationError("Osu! аккаунт не привязан")
        if value == 'discord' and not self.instance.discord_user:
            raise serializers.ValidationError("Discord аккаунт не привязан")
        return value

    def validate_nick_source(self, value):
        if value == 'osu' and not self.instance.osu_user:
            raise serializers.ValidationError("Osu! аккаунт не привязан")
        if value in ['discord_username', 'discord_display_name'] and not self.instance.discord_user:
            raise serializers.ValidationError("Discord аккаунт не привязан")
        return value

    def validate(self, data):
        region = data.get('region')
        city = data.get('city')
        if region and city:
            city_name = next((name for code, name in CITIES if code == city), None)
            if city_name and city_name not in LINKED.get(region, []):
                raise serializers.ValidationError("Город не соответствует выбранному региону")
        return data