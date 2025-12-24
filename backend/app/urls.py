from django.urls import path
from .views import AuthorizeView, MFASetupView, MFAVerifyView, MeView

urlpatterns = [
    path('auth/authorize', AuthorizeView.as_view(), name='authorize'),
    path('mfa/setup', MFASetupView.as_view(), name='mfa-setup'),
    path('mfa/verify', MFAVerifyView.as_view(), name='mfa-verify'),
    path('auth/me', MeView.as_view(), name='me'),
]
