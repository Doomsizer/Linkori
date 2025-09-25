import requests
import csv
import re
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from Accounts.models import UnauthorizedOsuUsers
from .regions import CITIES, REGIONS

logger = logging.getLogger(__name__)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1phBl7gphO-fgoVSglRbwwcrtKwRbJbPIe-1HRjvy3t0/export?format=csv&gid=0#gid=0"


def extract_osu_link(profile_text: str) -> str:
    """Извлекает ссылку на профиль osu! из текста."""
    link_match = re.search(r'https?://osu\.ppy\.sh/users/\d+', profile_text)
    return link_match.group(0) if link_match else ""

def get_osu_user_id(url):
    """Извлекает id из ссылки"""
    match = re.search(r'/users/(\d+)', url)
    return match.group(1) if match else None


def parse_players():
    """Парсит данные из листа parsing"""
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retry))

    try:
        response = session.get(SHEET_URL, timeout=15)
        response.encoding = "utf-8"
        response.raise_for_status()

        players_count = 0
        for row in csv.reader(response.text.splitlines()):
            if len(row) < 5:
                continue

            # Столбцы: A (0) — ссылка, C (2) — ник, H (7) — город, I (8) — регион
            profile_text = row[0].strip()
            nick = row[2].strip()
            city = row[7].strip() if row[3] else ""
            region = row[8].strip() if row[4] else ""

            profile_url = extract_osu_link(profile_text)
            if not profile_url or not nick:
                continue

            city_normalized = city.strip().lower()
            region_normalized = region.strip()
            if region_normalized == "ЕАО":
                region_normalized = "Еврейская автономная область"
            if not region_normalized:
                continue

            city_code = None
            city_name = None
            for code, name in CITIES:
                if city_normalized == name.strip().lower():
                    city_code = code
                    city_name = name
                    break
            defaults = {
                "region": list(REGIONS.keys())[list(REGIONS.values()).index(region_normalized)]
            }
            if city_name:
                defaults["cities"] = city_code
            UnauthorizedOsuUsers.objects.get_or_create(
                osu_id=get_osu_user_id(profile_url),
                defaults=defaults
            )
            players_count += 1
            if players_count % 100 == 0:
                logger.info(f"Обработано {players_count} игроков")

        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при парсинге google таблички: {e}")
        logger.info(f"Данные, обработанные до ошибки при парсинге google таблички")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка при парсинге google таблички: {e}")
        logger.info(f"Данные, обработанные до ошибки при парсинге google таблички")
        return False