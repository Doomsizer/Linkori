from django.db import models
from Accounts.models import CustomUser, UnauthorizedOsuUsers
from django.utils import timezone
from DiscordBot.models import DiscordServer
import logging

logger = logging.getLogger(__name__)

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
    error_count = models.IntegerField(default=0)
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
            logger.info(f"Reset counter for {self.name}: requests_count=0 at {now}")
            return True
        return False

    def increment_counter(self):
        """Увеличивает счетчик запросов, только если <60"""
        self.reset_counter_if_needed()
        if self.requests_count >= 60:
            logger.warning(f"Limit reached for {self.name}: requests_count={self.requests_count}, waiting for reset")
            return False
        self.requests_count += 1
        self.save()
        logger.info(f"Incremented {self.name}: requests_count={self.requests_count}")
        return True

    def can_make_request(self):
        """Проверяет, можно ли выполнить запрос (лимит 60 запросов в минуту)"""
        self.reset_counter_if_needed()
        can = self.requests_count < 60
        if not can:
            logger.warning(f"Cannot request {self.name}: count={self.requests_count} >=60")
        return can

    def increment_error(self):
        """Увеличивает счётчик ошибок, если >=3 — деактивирует app"""
        self.error_count += 1
        self.save()
        logger.warning(f"Error for {self.name}: error_count={self.error_count}")
        if self.error_count >= 3:
            self.is_active = False
            self.save()
            logger.error(f"Deactivated broken app {self.name}: too many errors ({self.error_count})")
            return False
        return True


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