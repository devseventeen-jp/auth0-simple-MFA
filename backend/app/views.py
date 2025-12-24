from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.core.mail import send_mail
from django_otp.plugins.otp_totp.models import TOTPDevice

import qrcode
import io
import base64

from .serializers import Auth0TokenSerializer, UserSerializer
from .auth0_utils import validate_auth0_token

User = get_user_model()

class AuthorizeView(APIView):
    """
    Called by callback.vue after Auth0 login.
    If user is new or unapproved, instructs frontend to go to MFA setup.
    If user is approved, logs them in directly.
    """
    def post(self, request):
        serializer = Auth0TokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        id_token = serializer.validated_data['id_token']
        try:
            payload = validate_auth0_token(id_token)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
        auth0_sub = payload['sub']
        email = payload.get('email', '')
        username = payload.get('nickname', email.split('@')[0])

        user, created = User.objects.get_or_create(auth0_sub=auth0_sub, defaults={
            'username': username,
            'email': email,
            'is_approved': False # New users are always unapproved
        })

        if not user.is_approved:
            # Check if TOTP is already confirmed (though is_approved should be True if so)
            has_totp = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
            
            return Response({
                'status': 'needs_mfa_setup',
                'user': UserSerializer(user).data,
                'mfa_setup_required': not has_totp,
                'message': 'Account pending activation. Please complete MFA setup.'
            })

        # Already approved user
        return Response({
            'status': 'success',
            'user': UserSerializer(user).data,
            'message': 'Login successful.'
        })

class MFASetupView(APIView):
    """
    User chooses a method and this view prepares it.
    """
    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
             return Response({'error': 'Bearer token required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = validate_auth0_token(token)
            user = User.objects.get(auth0_sub=payload['sub'])
        except Exception:
             return Response({'error': 'Invalid token'}, status=401)

        method = request.data.get('method')
        
        if method == 'TOTP':
            # Create unconfirmed device for setup
            # Remove old unconfirmed devices if any
            TOTPDevice.objects.filter(user=user, confirmed=False).delete()
            device = TOTPDevice.objects.create(user=user, confirmed=False, name="default")
            
            img = qrcode.make(device.config_url)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return Response({
                'method': 'TOTP',
                'secret': device.key,
                'qr_code': f"data:image/png;base64,{img_str}"
            })
            
        elif method == 'EMAIL':
            code = get_random_string(length=6, allowed_chars='0123456789')
            cache_key = f"mfa_email_{user.id}"
            cache.set(cache_key, code, timeout=300)
            
            try:
                send_mail(
                    subject=f'Your {settings.MFA_ISSUER_NAME} Verification Code',
                    message=f'Your verification code is: {code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"ERROR: Email send failed: {e}")
            
            print(f"DEBUG: Email OTP for {user.email}: {code}")
            
            return Response({
                'method': 'EMAIL',
                'message': f'Code sent to {user.email}'
            })

        return Response({'error': 'Invalid method'}, status=400)

class MFAVerifyView(APIView):
    """
    Verifies the code, and if successful, ACTIVATE the user.
    """
    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
             return Response({'error': 'Bearer token required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = validate_auth0_token(token)
            user = User.objects.get(auth0_sub=payload['sub'])
        except Exception:
             return Response({'error': 'Invalid token'}, status=401)

        code = request.data.get('code')
        method = request.data.get('method')

        verified = False
        if method == 'TOTP':
            device = TOTPDevice.objects.filter(user=user, confirmed=False).last()
            if not device:
                 # Check confirmed just in case they are re-doing it
                 device = TOTPDevice.objects.filter(user=user, confirmed=True).last()
            
            if device and device.verify_token(code):
                device.confirmed = True
                device.save()
                verified = True
                
        elif method == 'EMAIL':
            cache_key = f"mfa_email_{user.id}"
            cached_code = cache.get(cache_key)
            if cached_code and str(cached_code) == str(code):
                verified = True
                cache.delete(cache_key)

        if verified:
            user.is_approved = True
            user.mfa_method = method
            user.save()
            return Response({
                'status': 'verified',
                'message': 'Account activated successfully!',
                'user': UserSerializer(user).data
            })
        
        return Response({'error': 'Invalid verification code'}, status=400)

class MeView(APIView):
    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
             return Response({'error': 'Bearer token required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = validate_auth0_token(token)
            user = User.objects.get(auth0_sub=payload['sub'])
            return Response(UserSerializer(user).data)
        except Exception:
             return Response({'error': 'Invalid token'}, status=401)
