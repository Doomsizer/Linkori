from celery import shared_task
from .extension_service import parse_extension
from .googlesheet_service import parse_players

@shared_task()
def parse_browser_extension():
    if parse_extension():
        return {
            "status": "success",
            "message": "Successfully parsed users from extension"
        }
    else:
        return {
            "status": "error",
            "message": "Failed to parse users from extension, check logs for more info"
        }

@shared_task
def parse_google_sheet():
    if parse_players():
        return {
            "status": "success",
            "message": "Successfully parsed users from table"
        }
    else:
        return {
            "status": "error",
            "message": "Failed to parse users from table, check logs for more info"
        }