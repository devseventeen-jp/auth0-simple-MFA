from django.urls import path
from .views import AuthorizeView, MFASetupView, MFAVerifyView, LoginMFAView, MeView

urlpatterns = [
    path('auth/authorize', AuthorizeView.as_view(), name='authorize'),
    path('mfa/setup', MFASetupView.as_view(), name='mfa-setup'),
    path('mfa/verify', MFAVerifyView.as_view(), name='mfa-verify'),
    path('mfa/login', LoginMFAView.as_view(), name='mfa-login'),
    path('auth/me', MeView.as_view(), name='me'),
]
