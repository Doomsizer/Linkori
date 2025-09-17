from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

AVATAR_SOURCES = [
    ('osu', 'Osu!'),
    ('discord', 'Discord'),
]
NICK_SOURCES = [
    ('osu', 'Osu!'),
    ('discord_username', 'Discord Username'),
    ('discord_display_name', 'Discord Display Name'),
]

REGIONS = {
    "SA": "Республика Саха",
    "KHA": "Хабаровский край",
    "PRI": "Приморский край",
    "AMU": "Амурская область",
    "MAG": "Магаданская область",
    "SAK": "Сахалинская область",
    "CHU": "Чукотский автономный округ",
    "KAM": "Камчатский край",
    "YEV": "Еврейская автономная область",
    "BU": "Республика Бурятия",
    "ZAB": "Забайкальский край",
}

CITIES = [
    ('BLG', 'Благовещенск'),
    ('BEL', 'Белогорск'),
    ('SVO', 'Свободный'),
    ('TYN', 'Тында'),
    ('ZEY', 'Зея'),
    ('SHI', 'Шимановск'),
    ('RAY', 'Райчихинск'),
    ('ZAV', 'Завитинск'),
    ('SKO', 'Сковородино'),
    ('ULU', 'Улан-Удэ'),
    ('SEV', 'Северобайкальск'),
    ('GUS', 'Гусиноозёрск'),
    ('KYA', 'Кяхта'),
    ('ZAK', 'Закаменск'),
    ('BAB', 'Бабушкин'),
    ('BIR', 'Биробиджан'),
    ('OBL', 'Облучье'),
    ('CHI', 'Чита'),
    ('KRK', 'Краснокаменск'),
    ('BOR', 'Борзя'),
    ('PTZ', 'Петровск-Забайкальский'),
    ('NER', 'Нерчинск'),
    ('MOG', 'Могоча'),
    ('SHL', 'Шилка'),
    ('BAL', 'Балей'),
    ('HIL', 'Хилок'),
    ('SRE', 'Сретенск'),
    ('PTK', 'Петропавловск-Камчатский'),
    ('ELZ', 'Елизово'),
    ('VIL', 'Вилючинск'),
    ('MAG', 'Магадан'),
    ('SUS', 'Сусуман'),
    ('VLA', 'Владивосток'),
    ('USS', 'Уссурийск'),
    ('NAH', 'Находка'),
    ('ART', 'Артём'),
    ('ARS', 'Арсеньев'),
    ('SPA', 'Спасск-Дальний'),
    ('BKA', 'Большой Камень'),
    ('PAR', 'Партизанск'),
    ('LES', 'Лесозаводск'),
    ('DLG', 'Дальнегорск'),
    ('DLR', 'Дальнереченск'),
    ('FOK', 'Фокино'),
    ('YAK', 'Якутск'),
    ('NYU', 'Нерюнгри'),
    ('MIR', 'Мирный'),
    ('LEN', 'Ленск'),
    ('UDC', 'Удачный'),
    ('VLY', 'Вилюйск'),
    ('NYR', 'Нюрба'),
    ('POK', 'Покровск'),
    ('OLE', 'Олёкминск'),
    ('TOM', 'Томмот'),
    ('SRK', 'Среднеколымск'),
    ('VER', 'Верхоянск'),
    ('YUS', 'Южно-Сахалинск'),
    ('KOR', 'Корсаков'),
    ('KHM', 'Холмск'),
    ('OHA', 'Оха'),
    ('POR', 'Поронайск'),
    ('DOL', 'Долинск'),
    ('NEV', 'Невельск'),
    ('ANV', 'Анива'),
    ('ALS', 'Александровск-Сахалинский'),
    ('UGL', 'Углегорск'),
    ('SHA', 'Шахтёрск'),
    ('MAK', 'Макаров'),
    ('TMR', 'Томари'),
    ('SKU', 'Северо-Курильск'),
    ('KUR', 'Курильск'),
    ('KHA', 'Хабаровск'),
    ('KOM', 'Комсомольск-на-Амуре'),
    ('AMU', 'Амурск'),
    ('SGA', 'Советская Гавань'),
    ('NIK', 'Николаевск-на-Амуре'),
    ('BIK', 'Бикин'),
    ('VYA', 'Вяземский'),
    ('ANA', 'Анадырь'),
    ('BIL', 'Билибино'),
    ('PEV', 'Певек'),
]

LINKED = {
    'SA':
        [
            'Якутск', 'Нерюнгри', 'Мирный', 'Ленск', 'Удачный', 'Вилюйск', 'Нюрба', 'Покровск',
            'Олёкминск', 'Томмот', 'Среднеколымск', 'Верхоянск'
        ],
    'KHA':
        [
            'Хабаровск', 'Комсомольск-на-Амуре', 'Амурск', 'Советская Гавань', 'Николаевск-на-Амуре', 'Бикин', 'Вяземский'
        ],
    'PRI':
        [
            'Владивосток', 'Уссурийск', 'Находка', 'Артём', 'Арсеньев', 'Спасск-Дальний', 'Большой Камень',
            'Партизанск', 'Лесозаводск', 'Дальнегорск', 'Дальнереченск', 'Фокино'
        ],
    'AMU':
        [
            'Благовещенск', 'Белогорск', 'Свободный', 'Тында', 'Зея', 'Шимановск', 'Райчихинск', 'Завитинск', 'Сковородино'
        ],
    'MAG': [
        'Магадан', 'Сусуман'
        ],
    'SAK':
        [
            'Южно-Сахалинск', 'Корсаков', 'Холмск', 'Оха', 'Поронайск', 'Долинск', 'Невельск', 'Анива',
            'Александровск-Сахалинский', 'Углегорск', 'Шахтёрск', 'Макаров', 'Томари', 'Северо-Курильск', 'Курильск'
        ],
    'CHU':
        [
            'Анадырь', 'Билибино', 'Певек'
        ],
    'KAM':
        [
            'Петропавловск-Камчатский', 'Елизово', 'Вилючинск'
        ],
    'YEV':
        [
            'Биробиджан', 'Облучье'
        ],
    'BU':
        [
            'Улан-Удэ', 'Северобайкальск', 'Гусиноозёрск', 'Кяхта', 'Закаменск', 'Бабушкин'
        ],
    'ZAB':
        [
            'Чита', 'Краснокаменск', 'Борзя', 'Петровск-Забайкальский',
            'Нерчинск', 'Могоча', 'Шилка', 'Балей', 'Хилок', 'Сретенск'
        ]
}

class CustomUserManager(BaseUserManager):
    def create_user(self, discord_id=None, osu_id=None, **extra_fields):
        if not discord_id and not osu_id:
            raise ValueError('Должен быть указан хотя бы один ID: discord_id или osu_id')
        if discord_id:
            identifier = f'discord:{discord_id}'
        else:
            identifier = f'osu:{osu_id}'
        user = self.model(identifier=identifier, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, discord_id=None, osu_id=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser должен иметь is_superuser=True.')
        return self.create_user(discord_id=discord_id, osu_id=osu_id, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    identifier = models.CharField(max_length=100, unique=True)
    discord_user = models.OneToOneField('DiscordUsers', on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    osu_user = models.OneToOneField('OsuUsers', on_delete=models.SET_NULL, null=True, blank=True, related_name='user')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_linked = models.BooleanField(default=False)
    avatar_source = models.CharField(max_length=10, choices=AVATAR_SOURCES, null=True, blank=True)
    nick_source = models.CharField(max_length=20, choices=NICK_SOURCES, null=True, blank=True)
    region = models.CharField(max_length=3, choices=list(REGIONS.items()), null=True, blank=True)
    city = models.CharField(max_length=3, choices=[(code, name) for code, name in CITIES], null=True, blank=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'identifier'
    password = None
    last_login = None

    def has_usable_password(self):
        return False

    def get_region_display(self):
        return REGIONS.get(self.region, '')

    def get_city_display(self):
        for code, name in CITIES:
            if code == self.city:
                return name
        return ''

    def save(self, *args, **kwargs):
        self.is_linked = bool(self.osu_user and self.discord_user)
        super().save(*args, **kwargs)

class OsuUsers(models.Model):
    osu = models.OneToOneField('UnauthorizedOsuUsers', on_delete=models.CASCADE, related_name='tokens')
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True)
    token_expires_at = models.DateTimeField()

class UnauthorizedOsuUsers(models.Model):
    osu_id = models.CharField(max_length=255, unique=True)
    nick = models.CharField(max_length=255, default='')
    avatar_url = models.URLField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=3, choices=REGIONS, null=True)
    cities = models.CharField(max_length=3, choices=CITIES, null=True)
    last_updated = models.DateTimeField(auto_now=True)

class DiscordUsers(models.Model):
    discord_id = models.CharField(max_length=255, unique=True)
    nick = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True)
    avatar = models.CharField(max_length=255, null=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True)
    token_expires_at = models.DateTimeField()