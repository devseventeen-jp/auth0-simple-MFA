from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    auth0_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    
    # Store explicit MFA preference if we want per-user selection (optional, but good for "method selection")
    # For now, we follow the global setting or this field.
    mfa_method = models.CharField(max_length=10, choices=[('TOTP', 'TOTP'), ('EMAIL', 'Email')], default='TOTP')

    def __str__(self):
        return self.username
