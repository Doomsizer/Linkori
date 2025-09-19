import logging
from celery import shared_task
from django.conf import settings
from .discord_api import DiscordBotApi
from DiscordBot.models import DiscordServer
from Accounts.models import CustomUser, DiscordUsers
from Leaderboard.models import ServerMember
from .models import DiscordServer

logger = logging.getLogger(__name__)


@shared_task
def parse_discord_servers():
    """
    Задача для парсинга discord серверов на которых есть бот.
    """
    logger.info("Starting Discord servers parsing task")

    bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)

    if not bot_token:
        logger.error("DISCORD_BOT_TOKEN not found in settings")
        return False

    try:
        success = DiscordBotApi.get_servers(bot_token)
        if success:
            logger.info("Discord servers parsing completed successfully")
        else:
            logger.error("Discord servers parsing failed")
        return success
    except Exception as e:
        logger.exception(f"Error while parsing Discord servers: {str(e)}")
        return False