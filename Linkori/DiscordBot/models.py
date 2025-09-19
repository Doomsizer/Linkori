from django.db import models


class DiscordServer(models.Model):
    server_id = models.CharField(max_length=255, unique=True)
    server_name = models.CharField(max_length=255)
    server_icon = models.CharField(max_length=255, blank=True, null=True)
    member_count = models.IntegerField(default=0)

    def __str__(self):
        return self.server_name

    class Meta:
        verbose_name = "Discord сервер"
        verbose_name_plural = "Discord серверы"
