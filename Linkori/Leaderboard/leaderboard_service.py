import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import ServerLeaderboard, ServerLeaderboardEntry, ServerMember, OsuPerformance
from DiscordBot.models import DiscordServer
from Accounts.models import CustomUser

logger = logging.getLogger(__name__)


def get_unauthorized_user(user_id):
    """
    Получает UnauthorizedOsuUsers для указанного пользователя
    Пример использования в View:
    def some_view(user_id):
        unauthorized_user = get_unauthorized_user(user_id)
    """
    # Получаем пользователя с предзагрузкой связей
    user = get_object_or_404(
        Users.objects.select_related('osu_user__osu_id'),
        pk=user_id
    )

    # Проверяем цепочку связей
    if not user.osu_user or not user.osu_user.osu_id:
        return None

    return user.osu_user.osu_id


class LeaderboardService:
    """Сервис для работы с лидербордами"""

    @staticmethod
    def get_server_leaderboard(server_id, refresh=False, max_age_hours=24):
        """
        Получает или создает лидерборд для указанного сервера
        Args:
            server_id: ID Discord сервера
            refresh: Нужно ли обновить лидерборд
            max_age_hours: Максимальный возраст данных в часах
        """
        try:
            server = DiscordServer.objects.get(server_id=server_id)
        except DiscordServer.DoesNotExist:
            logger.error(f"Server with ID {server_id} does not exist")
            return None

        # Получаем или создаем лидерборд
        leaderboard, created = ServerLeaderboard.objects.get_or_create(server=server)

        # Проверяем, нужно ли обновить лидерборд
        needs_refresh = created or refresh
        if not needs_refresh and max_age_hours > 0:
            time_threshold = timezone.now() - timedelta(hours=max_age_hours)
            needs_refresh = leaderboard.last_updated < time_threshold

        # Обновляем лидерборд, если нужно
        if needs_refresh:
            # Обновляем лидерборд для всех режимов
            LeaderboardService.update_server_leaderboard_all_modes(leaderboard)

        return leaderboard

    @staticmethod
    @transaction.atomic
    def update_server_leaderboard(leaderboard, mode='osu'):
        """
        Обновляет лидерборд, пересчитывая позиции всех игроков для указанного режима
        Args:
            leaderboard: Объект ServerLeaderboard
            mode: Режим игры (osu, taiko, fruits, mania)
        """
        server = leaderboard.server
        logger.info(f"Updating leaderboard for server {server.server_name} in mode {mode}")

        # Получаем всех участников сервера с подключенными osu! аккаунтами
        members = ServerMember.objects.filter(
            server=server,
            user__osu_user__isnull=False,
            user__is_authorized=True
        ).select_related('user')

        # Получаем их производительность для указанного режима
        performances = []
        for member in members:
            try:
                unauthorized_user = get_unauthorized_user(member.user.id)
                performance = OsuPerformance.objects.get(user=unauthorized_user, mode=mode)
                performances.append({
                    'user': member.user,
                    'pp': performance.pp,
                    'global_rank': performance.global_rank,
                    'accuracy': performance.accuracy,
                    'playcount': performance.playcount,
                    'level': performance.level
                })
            except OsuPerformance.DoesNotExist:
                # У этого пользователя нет данных о производительности для этого режима
                continue

        # Сортируем по pp (от большего к меньшему)
        performances.sort(key=lambda x: x['pp'], reverse=True)

        # Очищаем старые записи в лидерборде для этого режима
        leaderboard.entries.filter(mode=mode).delete()

        # Создаем новые записи
        entries = []
        for i, perf in enumerate(performances):
            entry = ServerLeaderboardEntry(
                leaderboard=leaderboard,
                user=perf['user'],
                position=i + 1,
                pp=perf['pp'],
                global_rank=perf.get('global_rank'),
                accuracy=perf.get('accuracy'),
                playcount=perf.get('playcount'),
                level=perf.get('level'),
                mode=mode
            )
            entries.append(entry)

        # Сохраняем все записи за один запрос
        if entries:
            ServerLeaderboardEntry.objects.bulk_create(entries)

        # Обновляем время обновления
        leaderboard.last_updated = timezone.now()
        leaderboard.save()

        logger.info(f"Updated leaderboard for server {server.server_name} with {len(entries)} entries for mode {mode}")
        return leaderboard

    @staticmethod
    def update_server_leaderboard_all_modes(leaderboard):
        """
        Обновляет лидерборд для всех режимов игры
        Args:
            leaderboard: Объект ServerLeaderboard
        """
        modes = ['osu', 'taiko', 'fruits', 'mania']
        results = {}

        for mode in modes:
            try:
                LeaderboardService.update_server_leaderboard(leaderboard, mode)
                results[mode] = True
            except Exception as e:
                logger.error(f"Error updating leaderboard for mode {mode}: {str(e)}")
                results[mode] = False

        return results

    @staticmethod
    def get_user_servers(user):
        """
        Получает список серверов, на которых присутствует пользователь
        """
        return DiscordServer.objects.filter(members__user=user)

    @staticmethod
    def get_user_position(user, server_id, mode='osu'):
        """
        Получает позицию пользователя в лидерборде указанного сервера
        Args:
            user: Объект пользователя
            server_id: ID сервера Discord
            mode: Режим игры (osu, taiko, fruits, mania)
        """
        try:
            server = DiscordServer.objects.get(server_id=server_id)
            leaderboard = ServerLeaderboard.objects.get(server=server)
            entry = ServerLeaderboardEntry.objects.get(leaderboard=leaderboard, user=user, mode=mode)
            return entry.position
        except (DiscordServer.DoesNotExist, ServerLeaderboard.DoesNotExist, ServerLeaderboardEntry.DoesNotExist):
            return None

    @staticmethod
    def get_top_players(server_id, limit=100, mode='osu'):
        """
        Получает топ игроков на указанном сервере
        Args:
            server_id: ID сервера Discord
            limit: Максимальное количество игроков
            mode: Режим игры (osu, taiko, fruits, mania)
        """
        try:
            server = DiscordServer.objects.get(server_id=server_id)
            leaderboard = ServerLeaderboard.objects.get(server=server)
            return ServerLeaderboardEntry.objects.filter(
                leaderboard=leaderboard,
                mode=mode
            ).order_by('position')[:limit].select_related('user')
        except (DiscordServer.DoesNotExist, ServerLeaderboard.DoesNotExist):
            return []

    @staticmethod
    def get_or_create_server_leaderboard(server):
        """
        Получает или создает лидерборд для указанного сервера
        Args:
            server: Объект DiscordServer
        Returns:
            tuple: (leaderboard, created)
        """
        return ServerLeaderboard.objects.get_or_create(server=server)