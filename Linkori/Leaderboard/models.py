from django.db import models
from Accounts.models import CustomUser, UnauthorizedOsuUsers
from django.utils import timezone
from DiscordBot.models import DiscordServer


class ServerMember(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='server_memberships')
    server = models.ForeignKey(DiscordServer, on_delete=models.CASCADE, related_name='members')

    class Meta:
        unique_together = ('user', 'server')
        verbose_name = "Участник сервера"
        verbose_name_plural = "Участники серверов"


class OsuApiApplication(models.Model):
    name = models.CharField(max_length=100)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    requests_count = models.IntegerField(default=0)
    reset_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def reset_counter_if_needed(self):
        """Сбрасывает счетчик запросов, если прошла минута"""
        now = timezone.now()
        if (now - self.reset_time).total_seconds() > 60:
            self.requests_count = 0
            self.reset_time = now
            self.save()

    def increment_counter(self):
        """Увеличивает счетчик запросов"""
        self.reset_counter_if_needed()
        self.requests_count += 1
        self.save()

    def can_make_request(self):
        """Проверяет, можно ли выполнить запрос (лимит 60 запросов в минуту)"""
        self.reset_counter_if_needed()
        return self.requests_count < 60


class OsuPerformance(models.Model):
    """Модель для хранения данных о производительности игрока в osu!"""
    user = models.ForeignKey(UnauthorizedOsuUsers, on_delete=models.CASCADE, related_name='osu_performances')
    global_rank = models.IntegerField(null=True, blank=True)
    country_rank = models.IntegerField(null=True, blank=True)
    pp = models.FloatField(default=0)
    accuracy = models.FloatField(default=0)
    playcount = models.IntegerField(default=0)
    level = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    mode = models.CharField(max_length=10, default='osu', choices=[
        ('osu', 'osu!'),
        ('taiko', 'osu!taiko'),
        ('fruits', 'osu!catch'),
        ('mania', 'osu!mania'),
    ])

    def __str__(self):
        return f"{self.user.nick} - {self.pp}pp ({self.get_mode_display()})"

    class Meta:
        verbose_name = "Рейтинг osu!"
        verbose_name_plural = "Рейтинги osu!"
        unique_together = ('user', 'mode')


class ServerLeaderboard(models.Model):
    """Модель для хранения лидерборда по серверу"""
    server = models.OneToOneField(DiscordServer, on_delete=models.CASCADE, related_name='leaderboard')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Лидерборд сервера {self.server.server_name}"

    class Meta:
        verbose_name = "Лидерборд сервера"
        verbose_name_plural = "Лидерборды серверов"


class ServerLeaderboardEntry(models.Model):
    """Модель для хранения позиции игрока в лидерборде сервера"""
    leaderboard = models.ForeignKey(ServerLeaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    position = models.IntegerField()
    global_rank = models.IntegerField(null=True, blank=True)
    country_rank = models.IntegerField(null=True, blank=True)
    pp = models.FloatField(default=0)
    accuracy = models.FloatField(default=0)
    playcount = models.IntegerField(default=0)
    level = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    mode = models.CharField(max_length=10, default='osu', choices=[
        ('osu', 'osu!'),
        ('taiko', 'osu!taiko'),
        ('fruits', 'osu!catch'),
        ('mania', 'osu!mania'),
    ])

    class Meta:
        unique_together = ('leaderboard', 'user', 'mode')
        ordering = ['mode', 'position']
        verbose_name = "Запись лидерборда"
        verbose_name_plural = "Записи лидерборда"