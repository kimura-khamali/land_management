# api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
import phonenumbers

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField(max_length=6)

class CustomUserCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'password', 'confirm_password', 'role']

    def validate_phone_number(self, value):
        try:
            parsed_number = phonenumbers.parse(value, "KE")
            if not phonenumbers.is_valid_number(parsed_number):
                raise serializers.ValidationError("Invalid phone number")
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format")

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    phone_number = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class SetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    new_password = serializers.CharField()
    otp = serializers.CharField()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'role']
        read_only_fields = ['id', 'phone_number']



























# from rest_framework import serializers
# from django.contrib.auth import get_user_model
# import phonenumbers

# User = get_user_model()

# class LoginSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()

# class VerifyOtpSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     otp = serializers.CharField(max_length=6)

# class CustomUserCreationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#     confirm_password = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'phone_number', 'password', 'confirm_password', 'role']

#     def validate_phone_number(self, value):
#         try:
#             parsed_number = phonenumbers.parse(value, "KE")
#             if not phonenumbers.is_valid_number(parsed_number):
#                 raise serializers.ValidationError("Invalid phone number")
#             return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
#         except phonenumbers.NumberParseException:
#             raise serializers.ValidationError("Invalid phone number format")

#     def validate(self, data):
#         if data['password'] != data['confirm_password']:
#             raise serializers.ValidationError("Passwords do not match")
#         return data

#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
#         user = User.objects.create_user(**validated_data)
#         return user

# class OTPVerificationSerializer(serializers.Serializer):
#     otp = serializers.CharField(max_length=6)
#     phone_number = serializers.CharField()

# class PasswordResetRequestSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()

# class SetPasswordSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     new_password = serializers.CharField()
#     otp = serializers.CharField()

# class UserProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'first_name', 'last_name', 'phone_number', 'role']
#         read_only_fields = ['id', 'phone_number']
