import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Linkori.settings')

# Создаем экземпляр Celery
app = Celery('Linkori')

# Загружаем настройки из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем и регистрируем задачи из всех приложений
app.autodiscover_tasks()

# Настраиваем периодические задачи
app.conf.beat_schedule = {
    'parse-discord-servers-hourly': {
        'task': 'DiscordBot.tasks.parse_discord_servers',
        'schedule': crontab(minute='*/1'),  # Каждый час
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')