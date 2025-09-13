import logging
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class CustomJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization', '')
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
            except (InvalidToken, TokenError, User.DoesNotExist) as e:
                logger.warning(f"JWT authentication failed: {str(e)}")
                request.user = request.user or get_user_model().objects.none()
        else:
            logger.debug("No Bearer token in headers, using AnonymousUser")

        response = self.get_response(request)
        return response