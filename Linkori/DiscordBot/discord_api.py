import requests
import logging
from Leaderboard.models import ServerMember
from Accounts.models import CustomUser
from .models import DiscordServer

logger = logging.getLogger(__name__)


class DiscordBotApi:
    @staticmethod
    def get_servers(bot_token):
        """
        Получает список серверов, на которых присутствует бот, через Discord API
        и создает или обновляет соответствующие записи в базе данных.

        Args:
            bot_token (str): Токен бота Discord

        Returns:
            bool: True если операция успешна, False в случае ошибки
        """
        bot_guilds_url = "https://discord.com/api/users/@me/guilds?with_counts=true"
        headers = {"Authorization": f"Bot {bot_token}"}

        try:
            response = requests.get(bot_guilds_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get bot guilds: {response.status_code}, {response.text}")
                return False

            guilds = response.json()
            logger.info(f"Bot is present on {len(guilds)} servers")

            created_count = 0
            updated_count = 0

            for guild in guilds:
                server_id = guild.get('id')
                server_name = guild.get('name')
                server_icon = guild.get('icon')
                member_count = guild.get('approximate_member_count')

                if not server_id or not server_name:
                    logger.warning(f"Incomplete server data: {guild}")
                    continue

                server, created = DiscordServer.objects.update_or_create(
                    server_id=server_id,
                    defaults={
                        'server_id': server_id,
                        'server_name': server_name,
                        'server_icon': server_icon,
                        'member_count': member_count,
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            logger.info(f"Created {created_count} new servers, updated {updated_count} existing servers")
            return True

        except requests.RequestException as e:
            logger.error(f"Request error during Discord bot guilds fetch: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error while processing Discord servers: {str(e)}")
            return False