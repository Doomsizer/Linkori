import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Linkori.settings')

app = Celery('Linkori')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'parse-discord-servers-daily': {
        'task': 'DiscordBot.tasks.parse_discord_servers',
        'schedule': crontab(hour='1'),
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')