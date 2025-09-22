class OAuthError(Exception):
    """Базовое исключение для ошибок OAuth"""
    def __init__(self, message="OAuth authentication failed", code=400):
        self.message = message
        self.code = code
        super().__init__(self.message)

class TokenError(OAuthError):
    """Ошибка получения токена"""
    def __init__(self, provider, error_details=None):
        message = f"Failed to get token from {provider} provider"
        if error_details:
            message += f": {error_details}"
        super().__init__(message=message, code=400)

class AccountAlreadyLinked(OAuthError):
    """Аккаунт уже привязан к другому пользователю"""
    def __init__(self, provider, provider_id):
        self.provider = provider
        self.provider_id = provider_id
        super().__init__(
            message=f"This {provider} account is already linked to another user",
            code=409
        )