from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import OsuUsers, DiscordUsers, UnauthorizedOsuUsers
from django.utils import timezone
import responses
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(osu_id="12345")

        self.unauthorized_osu1 = UnauthorizedOsuUsers.objects.create(
            osu_id="12345",
            nick="user1",
            avatar_url="example.jpg"
        )

        self.osu_user1 = OsuUsers.objects.create(
            osu=self.unauthorized_osu1,
            access_token="test_access",
            refresh_token="test_refresh",
            token_expires_at=timezone.now()
        )

        self.user1.osu_user = self.osu_user1
        self.user1.save()

        self.user2 = User.objects.create_user(discord_id="67890")

        self.discord_user2 = DiscordUsers.objects.create(
            discord_id="67890",
            nick="user2",
            display_name="User2",
            avatar="example_avatar",
            access_token="test_access",
            refresh_token="test_refresh",
            token_expires_at=timezone.now()
        )

        self.user2.discord_user = self.discord_user2
        self.user2.save()

    @responses.activate
    def test_anonymous_login_existing_discord(self):
        responses.add(
            responses.POST, 'https://discord.com/api/oauth2/token',
            json={'access_token': 'test_access', 'refresh_token': 'test_refresh', 'expires_in': 604800},
            status=200
        )
        responses.add(
            responses.GET, 'https://discord.com/api/users/@me',
            json={'id': '67890', 'username': 'user2', 'global_name': 'User2', 'avatar': 'example_avatar'},
            status=200
        )
        logger.info("Testing anonymous login with existing Discord ID 67890")
        response = self.client.get(reverse('discord_callback'), {'code': 'test_code_discord'})
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/discord?access='))
        access_token = response.url.split('access=')[1]
        decoded_token = AccessToken(access_token)
        self.assertEqual(int(decoded_token['user_id']), self.user2.id)

    @responses.activate
    def test_anonymous_login_new_discord(self):
        responses.add(
            responses.POST, 'https://discord.com/api/oauth2/token',
            json={'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 604800},
            status=200
        )
        responses.add(
            responses.GET, 'https://discord.com/api/users/@me',
            json={'id': '99999', 'username': 'new_user', 'global_name': 'NewUser', 'avatar': 'new_avatar'},
            status=200
        )
        logger.info("Testing anonymous login with new Discord ID 99999")
        response = self.client.get(reverse('discord_callback'), {'code': 'new_code_discord'})
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/discord?access='))
        new_user = User.objects.get(identifier="discord:99999")
        access_token = response.url.split('access=')[1]
        decoded_token = AccessToken(access_token)
        self.assertEqual(int(decoded_token['user_id']), new_user.id)
        self.assertEqual(new_user.discord_user.discord_id, '99999')

    @responses.activate
    def test_anonymous_login_existing_osu(self):
        responses.add(
            responses.POST, 'https://osu.ppy.sh/oauth/token',
            json={'access_token': 'test_access', 'refresh_token': 'test_refresh', 'expires_in': 86400},
            status=200
        )
        responses.add(
            responses.GET, 'https://osu.ppy.sh/api/v2/me',
            json={'id': '12345', 'username': 'user1', 'avatar_url': 'example.jpg'},
            status=200
        )
        logger.info("Testing anonymous login with existing osu! ID 12345")
        response = self.client.get(reverse('osu_callback'), {'code': 'test_code_osu'})
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/osu?access='))
        access_token = response.url.split('access=')[1]
        decoded_token = AccessToken(access_token)
        self.assertEqual(int(decoded_token['user_id']), self.user1.id)

    @responses.activate
    def test_anonymous_login_new_osu(self):
        responses.add(
            responses.POST, 'https://osu.ppy.sh/oauth/token',
            json={'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 86400},
            status=200
        )
        responses.add(
            responses.GET, 'https://osu.ppy.sh/api/v2/me',
            json={'id': '99999', 'username': 'new_user', 'avatar_url': 'example.jpg'},
            status=200
        )
        logger.info("Testing anonymous login with new osu! ID 99999")
        response = self.client.get(reverse('osu_callback'), {'code': 'new_code_osu'})
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/osu?access='))
        new_user = User.objects.get(identifier="osu:99999")
        access_token = response.url.split('access=')[1]
        decoded_token = AccessToken(access_token)
        self.assertEqual(int(decoded_token['user_id']), new_user.id)
        self.assertEqual(new_user.osu_user.osu.osu_id, '99999')

    @responses.activate
    def test_authorized_bind_new_osu(self):
        refresh = RefreshToken.for_user(self.user2)
        access_token = str(refresh.access_token)
        responses.add(
            responses.POST, 'https://osu.ppy.sh/oauth/token',
            json={'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 86400},
            status=200
        )
        responses.add(
            responses.GET, 'https://osu.ppy.sh/api/v2/me',
            json={'id': '99999', 'username': 'new_user', 'avatar_url': 'example.jpg'},
            status=200
        )
        logger.info(f"Testing bind new osu! ID 99999 to user {self.user2.identifier}")
        response = self.client.get(
            reverse('osu_callback'),
            {'code': 'new_code_osu', 'state': access_token},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/osu?access='))
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.osu_user.osu.osu_id, '99999')

    @responses.activate
    def test_authorized_bind_existing_osu(self):
        refresh = RefreshToken.for_user(self.user2)
        access_token = str(refresh.access_token)
        responses.add(
            responses.POST, 'https://osu.ppy.sh/oauth/token',
            json={'access_token': 'test_access', 'refresh_token': 'test_refresh', 'expires_in': 86400},
            status=200
        )
        responses.add(
            responses.GET, 'https://osu.ppy.sh/api/v2/me',
            json={'id': '12345', 'username': 'user1', 'avatar_url': 'example.jpg'},
            status=200
        )
        logger.info(f"Testing bind existing osu! ID 12345 to user {self.user2.identifier}")
        response = self.client.get(
            reverse('osu_callback'),
            {'code': 'test_code_osu', 'state': access_token},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/osu?access='))
        with self.assertRaises(User.DoesNotExist):
            self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.osu_user.osu.osu_id, '12345')

    @responses.activate
    def test_authorized_bind_new_discord(self):
        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)
        responses.add(
            responses.POST, 'https://discord.com/api/oauth2/token',
            json={'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 604800},
            status=200
        )
        responses.add(
            responses.GET, 'https://discord.com/api/users/@me',
            json={'id': '99999', 'username': 'new_user', 'global_name': 'NewUser', 'avatar': 'new_avatar'},
            status=200
        )
        logger.info(f"Testing bind new Discord ID 99999 to user {self.user1.identifier}")
        response = self.client.get(
            reverse('discord_callback'),
            {'code': 'new_code_discord', 'state': access_token},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/discord?access='))
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.discord_user.discord_id, '99999')

    @responses.activate
    def test_authorized_bind_existing_discord(self):
        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)
        responses.add(
            responses.POST, 'https://discord.com/api/oauth2/token',
            json={'access_token': 'test_access', 'refresh_token': 'test_refresh', 'expires_in': 604800},
            status=200
        )
        responses.add(
            responses.GET, 'https://discord.com/api/users/@me',
            json={'id': '67890', 'username': 'user2', 'global_name': 'User2', 'avatar': 'example_avatar'},
            status=200
        )
        logger.info(f"Testing bind existing Discord ID 67890 to user {self.user1.identifier}")
        response = self.client.get(
            reverse('discord_callback'),
            {'code': 'test_code_discord', 'state': access_token},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/discord?access='))
        with self.assertRaises(User.DoesNotExist):
            self.user2.refresh_from_db()
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.discord_user.discord_id, '67890')

    @responses.activate
    def test_rebind_conflict(self):
        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)
        responses.add(
            responses.POST, 'https://osu.ppy.sh/oauth/token',
            json={'access_token': 'test_access', 'refresh_token': 'test_refresh', 'expires_in': 86400},
            status=200
        )
        responses.add(
            responses.GET, 'https://osu.ppy.sh/api/v2/me',
            json={'id': '12345', 'username': 'user1', 'avatar_url': 'example.jpg'},
            status=200
        )
        logger.info(f"Testing rebind conflict for osu! ID 12345 to user {self.user1.identifier}")
        response = self.client.get(
            reverse('osu_callback'),
            {'code': 'test_code_osu', 'state': access_token},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        logger.info(f"Response status: {response.status_code}, URL: {response.url}")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/callback/osu?access='))
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.osu_user.osu.osu_id, '12345')

    def test_anonymous_access_protected(self):
        logger.info("Testing anonymous access to protected endpoints")
        response = self.client.get(reverse('user'))
        logger.info(f"User endpoint response status: {response.status_code}")
        self.assertEqual(response.status_code, 401)

        response = self.client.get(reverse('osu_login'))
        logger.info(f"osu_login response status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('discord_login'))
        logger.info(f"discord_login response status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_logout(self):
        refresh = RefreshToken.for_user(self.user1)
        access_token = str(refresh.access_token)
        self.client.cookies['refresh_token'] = str(refresh)
        logger.info(f"Testing logout for user {self.user1.identifier}")
        response = self.client.get(reverse('user'), HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logger.info(f"Profile response status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

        self.client.cookies['refresh_token'] = ''
        response = self.client.post('/api/token/refresh/', {})
        logger.info(f"Refresh token response status: {response.status_code}")
        self.assertEqual(response.status_code, 400)

        response = self.client.get(reverse('user'))
        logger.info(f"Profile response after logout: {response.status_code}")
        self.assertEqual(response.status_code, 401)