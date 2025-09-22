from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    path('accounts/', include('Accounts.urls')),
    re_path(r'^(?!static/|api/|accounts/|admin/).*$', TemplateView.as_view(template_name='index.html'), name='react_app'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)