from django.db import models
from Accounts.models import CustomUser
from DiscordBot.models import DiscordServer


class ServerMember(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='server_memberships')
    server = models.ForeignKey(DiscordServer, on_delete=models.CASCADE, related_name='members')

    class Meta:
        unique_together = ('user', 'server')
        verbose_name = "Участник сервера"
        verbose_name_plural = "Участники серверов"