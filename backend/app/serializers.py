from rest_framework import serializers

class Auth0TokenSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    access_token = serializers.CharField(required=False)

class MFASetupSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['TOTP', 'EMAIL'], required=False)

class MFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)

class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    is_approved = serializers.BooleanField()
    mfa_method = serializers.CharField()
