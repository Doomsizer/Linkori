from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None:
            return None

        try:
            user = User._default_manager.get_by_natural_key(username)
            if self.user_can_authenticate(user):
                if user.is_superuser:
                    return user
                if user.check_password(password):
                    return user
        except User.DoesNotExist:
            return None
        return None