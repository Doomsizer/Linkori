import logging
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class CustomJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization', '')
        request.user = AnonymousUser()

        if auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                validated_token = AccessToken(token)
                user_id = validated_token['user_id']
                User = get_user_model()
                user = User.objects.get(id=user_id)

                request.user = user
                request.auth = validated_token
                logger.info(f"Authenticated user {user.identifier} via JWT")

            except (InvalidToken, TokenError) as e:
                logger.info(f"JWT authentication failed: {str(e)}")
            except Exception as e:
                logger.warning(f"Authentication failed: {str(e)}")

        elif request.user.is_staff:
            logger.info(f"Authenticated admin user {request.user} via admin panel")

        response = self.get_response(request)
        return response

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/admin/'):
            if not request.path.startswith('/admin/static/') and not request.path.startswith('/admin/media/'):
                if not request.user.is_authenticated or not request.user.is_staff:
                    return redirect('/')
        return None