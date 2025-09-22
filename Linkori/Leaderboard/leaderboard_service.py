import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import ServerLeaderboard, ServerLeaderboardEntry, ServerMember, OsuPerformance
from DiscordBot.models import DiscordServer
from Accounts.models import CustomUser

logger = logging.getLogger(__name__)


def get_unauthorized_osu_user(user_id):
    user = get_object_or_404(
        CustomUser.objects.select_related('osu_user__osu'),
        pk=user_id
    )
    if not user.osu_user or not user.osu_user.osu:
        return None
    return user.osu_user.osu


class LeaderboardService:
    @staticmethod
    def get_server_leaderboard(server_id, refresh=False, max_age_hours=24):
        try:
            server = DiscordServer.objects.get(server_id=server_id)
        except DiscordServer.DoesNotExist:
            logger.error(f"Server with ID {server_id} does not exist")
            return None

        leaderboard, created = ServerLeaderboard.objects.get_or_create(server=server)

        needs_refresh = created or refresh
        if not needs_refresh and max_age_hours > 0:
            time_threshold = timezone.now() - timedelta(hours=max_age_hours)
            needs_refresh = leaderboard.last_updated < time_threshold

        if needs_refresh:
            LeaderboardService.update_server_leaderboard_all_modes(leaderboard)

        return leaderboard

    @staticmethod
    @transaction.atomic
    def update_server_leaderboard(leaderboard, mode='osu'):
        server = leaderboard.server
        logger.info(f"Updating leaderboard for server {server.server_name} in mode {mode}")

        members = ServerMember.objects.filter(
            server=server,
            user__osu_user__isnull=False,
            user__is_linked=True
        ).select_related('user')

        performances = []
        for member in members:
            try:
                osu_user = get_unauthorized_osu_user(member.user.id)
                performance = OsuPerformance.objects.get(user=osu_user, mode=mode)
                performances.append({
                    'user': member.user,
                    'pp': performance.pp,
                    'global_rank': performance.global_rank,
                    'accuracy': performance.accuracy,
                    'playcount': performance.playcount,
                    'level': performance.level
                })
            except OsuPerformance.DoesNotExist:
                continue

        performances.sort(key=lambda x: x['pp'], reverse=True)

        leaderboard.entries.filter(mode=mode).delete()

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

        if entries:
            ServerLeaderboardEntry.objects.bulk_create(entries)

        leaderboard.last_updated = timezone.now()
        leaderboard.save()

        logger.info(f"Updated leaderboard for server {server.server_name} with {len(entries)} entries for mode {mode}")
        return leaderboard

    @staticmethod
    def update_server_leaderboard_all_modes(leaderboard):
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
        return DiscordServer.objects.filter(members__user=user)

    @staticmethod
    def get_user_position(user, server_id, mode='osu'):
        try:
            server = DiscordServer.objects.get(server_id=server_id)
            leaderboard = ServerLeaderboard.objects.get(server=server)
            entry = ServerLeaderboardEntry.objects.get(leaderboard=leaderboard, user=user, mode=mode)
            return entry.position
        except (DiscordServer.DoesNotExist, ServerLeaderboard.DoesNotExist, ServerLeaderboardEntry.DoesNotExist):
            return None

    @staticmethod
    def get_top_players(server_id, limit=100, mode='osu'):
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
        return ServerLeaderboard.objects.get_or_create(server=server)