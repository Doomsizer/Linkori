from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from Leaderboard.regions import REGIONS, CITIES

AVATAR_SOURCES = [
    ('osu', 'Osu!'),
    ('discord', 'Discord'),
]
NICK_SOURCES = [
    ('osu', 'Osu!'),
    ('discord_username', 'Discord Username'),
    ('discord_display_name', 'Discord Display Name'),
]


class CustomUserManager(BaseUserManager):
    def create_user(self, discord_id=None, osu_id=None, **extra_fields):
        identifier = extra_fields.pop('identifier', None)
        if not discord_id and not osu_id and not identifier:
            raise ValueError('Должен быть указан хотя бы один ID: discord_id или osu_id, или identifier')

        if discord_id:
            identifier = f'discord:{discord_id}'
        elif osu_id:
            identifier = f'osu:{osu_id}'

        user = self.model(identifier=identifier, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, discord_id=None, osu_id=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser должен иметь is_superuser=True.')

        identifier = extra_fields.pop('identifier', None)
        if not discord_id and not osu_id and not identifier:
            identifier = 'admin:1'

        return self.create_user(discord_id=discord_id, osu_id=osu_id, identifier=identifier, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    identifier = models.CharField(max_length=100, unique=True)
    discord_user = models.OneToOneField('DiscordUsers', on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='user')
    osu_user = models.OneToOneField('OsuUsers', on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_linked = models.BooleanField(default=False)
    avatar_source = models.CharField(max_length=10, choices=AVATAR_SOURCES, null=True, blank=True)
    nick_source = models.CharField(max_length=20, choices=NICK_SOURCES, null=True, blank=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'identifier'
    password = None
    last_login = None

    def has_usable_password(self):
        return False

    def check_password(self, raw_password):
        """
        Переопределяем для superuser: любой пароль (или пустой) считается валидным.
        Избегает ошибки len(None) и позволяет логин без реального пароля.
        """
        if self.is_superuser:
            return True
        return False

    def get_full_name(self):
        return self.identifier

    def get_short_name(self):
        return self.identifier

    def __str__(self):
        return self.identifier

    def get_region_display(self):
        return REGIONS.get(self.region, '')

    def get_city_display(self):
        for code, name in CITIES:
            if code == self.city:
                return name
        return ''

    def save(self, *args, **kwargs):
        self.is_linked = bool(self.osu_user and self.discord_user)
        super().save(*args, **kwargs)


class OsuUsers(models.Model):
    osu = models.OneToOneField('UnauthorizedOsuUsers', on_delete=models.CASCADE, related_name='tokens')
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True)
    token_expires_at = models.DateTimeField()


class UnauthorizedOsuUsers(models.Model):
    osu_id = models.CharField(max_length=255, unique=True)
    nick = models.CharField(max_length=255, default='')
    avatar_url = models.URLField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=3, choices=REGIONS, null=True)
    cities = models.CharField(max_length=3, choices=CITIES, null=True)
    last_updated = models.DateTimeField(auto_now=True)


class DiscordUsers(models.Model):
    discord_id = models.CharField(max_length=255, unique=True)
    nick = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True)
    avatar = models.CharField(max_length=255, null=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True)
    token_expires_at = models.DateTimeField()