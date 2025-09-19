import requests
import time
from .regions import REGIONS
import logging
from Accounts.models import UnauthorizedOsuUsers

logger = logging.getLogger(__name__)

GAME_MODES = ["osu", "taiko", "fruits", "mania"]

REQUEST_DELAY = 0.6

seen_ids = set()

def get_all_players_from_region(region_code: str, mode: str) -> int | bool:
    """Получает всех игроков из региона"""
    players = 0
    page = 1

    while True:
        url = f"https://osuworld.octo.moe/api/RU/RU-{region_code}/top/{mode}?page={page}"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Ошибка {response.status_code} | Регион: {region_code} | Режим: {mode} | Страница: {page}")
            return False

        data = response.json()
        if not data.get("top"):
            break

        for player in data["top"]:
            if player["id"] in seen_ids:
                continue
            seen_ids.add(player["id"])

            UnauthorizedOsuUsers.objects.get_or_create(
                osu_id=player["id"],
                defaults={
                    "region": region_code
                }
            )
            players+=1

        page += 1
        time.sleep(REQUEST_DELAY)

    return players

def parse_extension():
    total_players = 0

    for region in REGIONS.keys():
        for mode in GAME_MODES:
            logger.info(f"Парсим: {region} | {mode}...")
            players = get_all_players_from_region(region, mode)
            if type(players) == bool:
                return False
            logger.info(f"Найдено: {players} игроков")
            total_players += players

    logger.info(f"\nПарсинг с раширения завершен. Всего собрано {total_players} уникальных игроков.")
    return True