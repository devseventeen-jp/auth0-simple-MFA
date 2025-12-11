from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import io
import base64
from .serializers import Auth0TokenSerializer, MFASetupSerializer, MFAVerifySerializer, UserSerializer
from .auth0_utils import validate_auth0_token
import time

User = get_user_model()

class AuthorizeView(APIView):
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
            'email': email
        })

        if not user.is_approved:
            return Response({
                'status': 'error',
                'file_status': 'not_approved',
                'message': 'Account verification pending.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check MFA
        # 1. Has MFA setup?
        method = user.mfa_method
        has_setup = False
        
        if method == 'TOTP':
            has_setup = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        else:
             # EMAIL is always "setup" implicitly, or we can check a flag.
             # For this simple implementation, Email is considered always available if selected.
             has_setup = True 

        # Create a temporary session token for MFA steps if not fully logged in
        # For simplicity, we return user info and expect client to call /mfa/login
        
        return Response({
            'user': UserSerializer(user).data,
            'mfa_required': True, # Always true according to spec? Or only if setup?
                                  # Spec says "Login時にMFA必須の場合". We'll assume enforced.
            'mfa_setup_required': not has_setup,
            'mfa_method': method
        })

class MFASetupView(APIView):
    def post(self, request):
        # Authenticate user. Since we don't have a session yet, we assume the client sends 
        # the same Auth0 Token validation or a pre-session token. 
        # For simplicity in this "Authorize -> Setup" flow, we'll re-validate Auth0 token 
        # or implement a temporary signed token.
        # Let's rely on Auth0 token again for identity.
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
             return Response({'error': 'Bearer token required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = validate_auth0_token(token)
            user = User.objects.get(auth0_sub=payload['sub'])
        except Exception:
             return Response({'error': 'Invalid token'}, status=401)

        # Determine Method
        req_method = request.data.get('method')
        server_method = getattr(settings, 'MFA_METHOD', 'TOTP')
        
        # Priority: Request > User Pref > Server Config
        method = req_method or server_method
        
        if method == 'TOTP':
            # Create unconfirmed device
            device = TOTPDevice.objects.create(user=user, confirmed=False, name="default")
            url = device.config_url
            
            img = qrcode.make(url)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return Response({
                'method': 'TOTP',
                'secret': device.key, # Optional to show text
                'qr_code': f"data:image/png;base64,{img_str}"
            })
            
        elif method == 'EMAIL':
            # Generate code and simulate sending
            code = get_random_string(length=6, allowed_chars='0123456789')
            # Store in cache: "mfa_email_<user_id>" -> code
            cache.set(f"mfa_email_{user.id}", code, timeout=300)
            
            # Send email
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject=f'Your {settings.MFA_ISSUER_NAME} Verification Code',
                    message=f'Your verification code is: {code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print(f"DEBUG: Email sent to {user.email}")
            except Exception as e:
                print(f"ERROR: Failed to send email to {user.email}: {e}")
                # Fallback print for development if email fails
                print(f"DEBUG: Email OTP for {user.email}: {code}")
            
            return Response({
                'method': 'EMAIL',
                'message': f'Code sent to {user.email}'
            })

        return Response({'error': 'Invalid method'}, status=400)

class MFAVerifyView(APIView):
    def post(self, request):
        # Identity Check
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
        method = request.data.get('method', getattr(settings, 'MFA_METHOD', 'TOTP'))

        if method == 'TOTP':
            # Verify basic device
            # Check unconfirmed first for setup
            device = TOTPDevice.objects.filter(user=user, confirmed=False).last()
            if not device:
                # Login Check
                device = TOTPDevice.objects.filter(user=user, confirmed=True).last()
            
            if not device:
                return Response({'error': 'No TOTP setup found'}, status=400)
                
            if device.verify_token(code):
                device.confirmed = True
                device.save()
                user.mfa_method = 'TOTP'
                user.save()
                return Response({'status': 'verified', 'method': 'TOTP'})
            else:
                return Response({'error': 'Invalid Code'}, status=400)
                
        elif method == 'EMAIL':
            cached_code = cache.get(f"mfa_email_{user.id}")
            if cached_code == code:
                user.mfa_method = 'EMAIL'
                user.save()
                return Response({'status': 'verified', 'method': 'EMAIL'})
            else:
                return Response({'error': 'Invalid or Expired Code'}, status=400)
                
        return Response({'error': 'Unknown Method'}, status=400)

class LoginMFAView(APIView):
    """
    Final step to get session/token after MFA.
    """
    def post(self, request):
        # Just alias to Verify for now, optionally issuing a long-lived JWT here
        # For this PoC, Verify is enough, but we should login() the user
         return MFAVerifyView().post(request)

class MeView(APIView):
    def get(self, request):
        # In a real app, verify Session or Django Token
        # Here we accept the Auth0 token to Identify
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

