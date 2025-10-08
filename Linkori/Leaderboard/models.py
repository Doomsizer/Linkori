from django.db import models
from Accounts.models import CustomUser, UnauthorizedOsuUsers
from django.utils import timezone
from DiscordBot.models import DiscordServer
import logging

logger = logging.getLogger(__name__)

OSU_RATE_LIMIT = 60
OSU_ERROR_THRESHOLD = 3
OSU_ERROR_WINDOW_SECONDS = 900

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
    error_times = models.JSONField(default=list)
    reset_time = models.DateTimeField(default=timezone.now)
    access_token = models.CharField(max_length=255, blank=True)
    token_expires_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.name

    def reset_counter_if_needed(self):
        now = timezone.now()
        if (now - self.reset_time).total_seconds() > 60:
            self.requests_count = 0
            self.reset_time = now
            self.save()
            return True
        return False

    def increment_counter(self):
        from django.db.models import F
        from django.db import transaction
        with transaction.atomic():
            self = type(self).objects.select_for_update().get(pk=self.pk)
            self.reset_counter_if_needed()
            if self.requests_count >= OSU_RATE_LIMIT:
                return False
            self.requests_count = F('requests_count') + 1
            self.save(update_fields=['requests_count'])
            self.refresh_from_db()
            return True

    def can_make_request(self):
        self.reset_counter_if_needed()
        return self.requests_count < OSU_RATE_LIMIT

    def get_recent_error_count(self):
        now = timezone.now()
        recent = []
        for t_str in self.error_times:
            try:
                t = timezone.datetime.fromisoformat(t_str)
                if (now - t).total_seconds() < OSU_ERROR_WINDOW_SECONDS:
                    recent.append(t_str)
            except:
                pass
        if len(recent) != len(self.error_times):
            self.error_times = recent
            self.save()
        return len(recent)

    def increment_error(self):
        self.error_times.append(timezone.now().isoformat())
        self.save()
        if self.get_recent_error_count() >= OSU_ERROR_THRESHOLD:
            self.is_active = False
            self.save()
            return False
        return True

    def reset_errors_if_needed(self):
        count = self.get_recent_error_count()
        if count < OSU_ERROR_THRESHOLD and not self.is_active:
            self.is_active = True
            self.save()


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