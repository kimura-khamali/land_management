# views.py

import json
import logging
import random
import requests
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView

from users.models import RegistrationCode
from .serializers import (
    CustomUserCreationSerializer,
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    SetPasswordSerializer,
    UserProfileSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(phone_number, otp):
    headers = {
        "Authorization": f"Basic {settings.SMSLEOPARD_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "source": "Akirachix",
        "message": f"Your OTP code is {otp}",
        "destination": [{"number": phone_number}],
    }
    try:
        response = requests.post(settings.SMSLEOPARD_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"OTP sent successfully to {phone_number}. Response: {response.json()}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to send OTP: {str(e)}")
        return {"error": str(e)}

class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = CustomUserCreationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)  # Set user as inactive initially
            
            # Generate and send OTP
            otp = generate_otp()
            RegistrationCode.objects.create(
                phone_number=user.phone_number,
                code=otp,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            send_otp(user.phone_number, otp)

            return Response({
                "message": "User registered successfully. OTP sent to your phone.",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
            }, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Registration failed with errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        password = data.get('password')

        if not phone_number or not password:
            return JsonResponse({"message": "Phone number and password are required"}, status=400)

        user = authenticate(username=phone_number, password=password)
        if user:
            if user.is_active:
                django_login(request, user)
                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    "message": "Login successful. Welcome!",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=200)
            else:
                otp = generate_otp()
                RegistrationCode.objects.create(
                    phone_number=user.phone_number,
                    code=otp,
                    expires_at=timezone.now() + timedelta(minutes=10)
                )
                send_otp(user.phone_number, otp)
                return JsonResponse({"message": "Account not verified. OTP sent for verification."}, status=200)
        else:
            return JsonResponse({"message": "Invalid phone number or password"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"message": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return JsonResponse({"message": f"An error occurred during login: {str(e)}"}, status=500)

@api_view(['POST'])
def otp_verification(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        otp = serializer.validated_data['otp']
        try:
            registration_code = RegistrationCode.objects.get(phone_number=user.phone_number, code=otp)
            if registration_code.expires_at < timezone.now():
                return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.save()
            registration_code.delete()

            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "OTP Verified Successfully. You can now access the system.",
                "first_name": user.first_name,
                "last_name": user.last_name,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        except RegistrationCode.DoesNotExist:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        try:
            user = User.objects.get(phone_number=phone_number)
            otp = generate_otp()
            RegistrationCode.objects.create(
                phone_number=user.phone_number,
                code=otp,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            send_otp(user.phone_number, f"Password reset verification OTP is: {otp}")

            return Response({"message": "Password reset OTP sent to your phone"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@require_http_methods(["POST"])
@api_view(['POST'])
def password_reset_confirm(request):
    serializer = SetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        new_password = serializer.validated_data['new_password']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(phone_number=phone_number)
            registration_code = RegistrationCode.objects.get(phone_number=phone_number, code=otp)
            
            if registration_code.expires_at < timezone.now():
                return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            registration_code.delete()

            return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except RegistrationCode.DoesNotExist:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class RegisteredUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'admin':
            users = User.objects.all()
        elif request.user.role == 'lawyer':
            self.permission_classes = [HasLawyerPermissions]
            users = User.objects.filter(role__in=['buyer', 'seller'])
        elif request.user.role == 'buyer':
            self.permission_classes = [HasBuyerPermissions]
            users = User.objects.filter(role='seller')
        elif request.user.role == 'seller':
            self.permission_classes = [HasSellerPermissions]
            users = User.objects.filter(role='buyer')
        else:
            users = User.objects.none()

        user_data = [
            {
                'id': user.id,
                'phone_number': user.phone_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'role': user.role
            }
            for user in users
        ]
        return Response(user_data)

@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    try:
        logout(request)
        return JsonResponse({"message": "Logged out successfully"}, status=200)
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return JsonResponse({"message": f"An error occurred during logout: {str(e)}"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def home(request):
    return Response({'message': 'Welcome to the home page!'}, status=status.HTTP_200_OK)



































# # views.py

# import json
# import logging
# from datetime import timedelta

# from django.conf import settings
# from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
# from django.http import JsonResponse
# from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods

# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.views import APIView

# from users.permisions import HasBuyerPermissions, HasLawyerPermissions, HasSellerPermissions

# from .serializers import (
#     CustomUserCreationSerializer,
#     OTPVerificationSerializer,
#     PasswordResetRequestSerializer,
#     SetPasswordSerializer,
#     UserProfileSerializer,
# )
# from users.models import RegistrationCode
# # from api.utils import send_otp, generate_otp, format_phone_number

# User = get_user_model()
# logger = logging.getLogger(__name__)

# def generate_otp():
#     return str(random.randint(100000, 999999))

# def send_otp(phone_number, otp):
#     headers = {
#         "Authorization": f"Basic {settings.SMSLEOPARD_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "source": "Akirachix",
#         "message": f"Your OTP code is {otp}",
#         "destination": [{"number": phone_number}],
#     }
#     try:
#         response = requests.post(settings.SMSLEOPARD_API_URL, json=payload, headers=headers)
#         response.raise_for_status()
#         logger.info(f"OTP sent successfully to {phone_number}. Response: {response.json()}")
#         return response.json()
#     except requests.RequestException as e:
#         logger.error(f"Failed to send OTP: {str(e)}")
#         return {"error": str(e)}



# class UserCreateAPIView(generics.CreateAPIView):
#     serializer_class = CustomUserCreationSerializer

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save(is_active=False)
#             return Response({
#                 "message": "User registered successfully. OTP sent to your phone.",
#                 "user_id": user.id,
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "phone_number": user.phone_number,
#             }, status=status.HTTP_201_CREATED)
#         else:
#             logger.error(f"Registration failed with errors: {serializer.errors}")
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # class UserCreateAPIView(generics.CreateAPIView):
# #     serializer_class = CustomUserCreationSerializer

# #     def create(self, request, *args, **kwargs):
# #         serializer = self.get_serializer(data=request.data)
# #         if serializer.is_valid():
# #             user = serializer.save(is_active=False)  # Set is_active to False initially
            
# #             otp = generate_otp()
# #             RegistrationCode.objects.create(
# #                 phone_number=user.phone_number,
# #                 code=otp,
# #                 expires_at=timezone.now() + timedelta(minutes=10)
# #             )

# #             send_otp(user.phone_number, otp)

# #             return Response({
# #                 "message": "User registered successfully. OTP sent to your phone.",
# #                 "user_id": user.id,
# #                 "first_name": user.first_name,
# #                 "last_name": user.last_name,
# #                 "phone_number": user.phone_number,
# #             }, status=status.HTTP_201_CREATED)
# #         else:
# #             logger.error(f"Registration failed with errors: {serializer.errors}")
# #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# def login_user(request):
#     try:
#         data = json.loads(request.body)
#         phone_number = data.get('phone_number')
#         password = data.get('password')

#         if not phone_number or not password:
#             return JsonResponse({"message": "Phone number and password are required"}, status=400)

#         formatted_number = format_phone_number(phone_number)
#         if not formatted_number:
#             return JsonResponse({"message": "Invalid phone number format"}, status=400)

#         user = authenticate(username=formatted_number, password=password)
#         if user:
#             if user.is_active:
#                 django_login(request, user)
#                 refresh = RefreshToken.for_user(user)
#                 return JsonResponse({
#                     "message": "Login successful. Welcome!",
#                     "first_name": user.first_name,
#                     "last_name": user.last_name,
#                     "refresh": str(refresh),
#                     "access": str(refresh.access_token),
#                 }, status=200)
#             else:
#                 return JsonResponse({"message": "Account not verified. Please complete OTP verification."}, status=403)
#         else:
#             return JsonResponse({"message": "Invalid phone number or password"}, status=400)
#     except json.JSONDecodeError:
#         return JsonResponse({"message": "Invalid JSON data"}, status=400)
#     except Exception as e:
#         logger.error(f"Error during login: {str(e)}")
#         return JsonResponse({"message": f"An error occurred during login: {str(e)}"}, status=500)

# @api_view(['POST'])
# def otp_verification(request, user_id):
#     try:
#         user = User.objects.get(pk=user_id)
#     except User.DoesNotExist:
#         return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

#     serializer = OTPVerificationSerializer(data=request.data)
#     if serializer.is_valid():
#         otp = serializer.validated_data['otp']
#         try:
#             registration_code = RegistrationCode.objects.get(phone_number=user.phone_number, code=otp)
#             if registration_code.expires_at < timezone.now():
#                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

#             user.is_active = True
#             user.save()
#             registration_code.delete()

#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 "message": "OTP Verified Successfully. You can now access the system.",
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }, status=status.HTTP_200_OK)
#         except RegistrationCode.DoesNotExist:
#             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# @api_view(['POST'])
# def password_reset_request(request):
#     serializer = PasswordResetRequestSerializer(data=request.data)
#     if serializer.is_valid():
#         phone_number = serializer.validated_data['phone_number']
#         try:
#             user = User.objects.get(phone_number=phone_number)
#             otp = generate_otp()
#             RegistrationCode.objects.create(
#                 phone_number=user.phone_number,
#                 code=otp,
#                 expires_at=timezone.now() + timedelta(minutes=10)
#             )
#             send_otp(user.phone_number, f"Password reset verification OTP is: {otp}")

#             return Response({"message": "Password reset OTP sent to your phone"}, status=status.HTTP_200_OK)
#         except User.DoesNotExist:
#             return Response({"message": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# @api_view(['POST'])
# def password_reset_confirm(request):
#     serializer = SetPasswordSerializer(data=request.data)
#     if serializer.is_valid():
#         phone_number = serializer.validated_data['phone_number']
#         new_password = serializer.validated_data['new_password']
#         otp = serializer.validated_data['otp']

#         try:
#             user = User.objects.get(phone_number=phone_number)
#             registration_code = RegistrationCode.objects.get(phone_number=phone_number, code=otp)
            
#             if registration_code.expires_at < timezone.now():
#                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

#             user.set_password(new_password)
#             user.save()
#             registration_code.delete()

#             return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
#         except User.DoesNotExist:
#             return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#         except RegistrationCode.DoesNotExist:
#             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UserProfileAPIView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user

# class RegisteredUsersView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role == 'admin':
#             users = User.objects.all()
#         elif request.user.role == 'lawyer':
#             self.permission_classes = [HasLawyerPermissions]
#             users = User.objects.filter(role__in=['buyer', 'seller'])
#         elif request.user.role == 'buyer':
#             self.permission_classes = [HasBuyerPermissions]
#             users = User.objects.filter(role='seller')
#         elif request.user.role == 'seller':
#             self.permission_classes = [HasSellerPermissions]
#             users = User.objects.filter(role='buyer')
#         else:
#             users = User.objects.none()

#         user_data = [
#             {
#                 'id': user.id,
#                 'phone_number': user.phone_number,
#                 'first_name': user.first_name,
#                 'last_name': user.last_name,
#                 'is_active': user.is_active,
#                 'date_joined': user.date_joined,
#                 'role': user.role
#             }
#             for user in users
#         ]
#         return Response(user_data)

# @csrf_exempt
# @require_http_methods(["POST"])
# def logout_user(request):
#     try:
#         logout(request)
#         return JsonResponse({"message": "Logged out successfully"}, status=200)
#     except Exception as e:
#         logger.error(f"Error during logout: {str(e)}")
#         return JsonResponse({"message": f"An error occurred during logout: {str(e)}"}, status=500)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def home(request):
#     return Response({'message': 'Welcome to the home page!'}, status=status.HTTP_200_OK)








































# # # views.py

# # import json
# # import logging
# # from datetime import timedelta

# # from django.conf import settings
# # from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
# # from django.http import JsonResponse
# # from django.utils import timezone
# # from django.views.decorators.csrf import csrf_exempt
# # from django.views.decorators.http import require_http_methods

# # from rest_framework import generics, status
# # from rest_framework.response import Response
# # from rest_framework.decorators import api_view, permission_classes
# # from rest_framework.permissions import IsAuthenticated
# # from rest_framework_simplejwt.tokens import RefreshToken
# # from rest_framework.views import APIView

# # from users.permisions import HasBuyerPermissions, HasLawyerPermissions, HasSellerPermissions

# # from .serializers import (
# #     CustomUserCreationSerializer,
# #     OTPVerificationSerializer,
# #     PasswordResetRequestSerializer,
# #     SetPasswordSerializer,
# #     UserProfileSerializer,
# # )
# # from users.models import RegistrationCode
# # # from users.permissions import HasBuyerPermissions, HasLawyerPermissions, HasSellerPermissions
# # # from .utils import send_otp, generate_otp, format_phone_number

# # User = get_user_model()
# # logger = logging.getLogger(__name__)



# # class UserCreateAPIView(generics.CreateAPIView):
# #     serializer_class = CustomUserCreationSerializer

# #     def create(self, request, *args, **kwargs):
# #         serializer = self.get_serializer(data=request.data)
# #         if serializer.is_valid():
# #             user = serializer.save()
            
# #             otp = generate_otp()
# #             RegistrationCode.objects.create(
# #                 phone_number=user.phone_number,
# #                 code=otp,
# #                 expires_at=timezone.now() + timedelta(minutes=10)
# #             )

# #             send_otp(user.phone_number, otp)

# #             return Response({
# #                 "message": "User registered successfully. OTP sent to your phone.",
# #                 "user_id": user.id,
# #                 "first_name": user.first_name,
# #                 "last_name": user.last_name,
# #                 "phone_number": user.phone_number,
# #             }, status=status.HTTP_201_CREATED)
# #         else:
# #             logger.error(f"Registration failed with errors: {serializer.errors}")
# #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # # class UserCreateAPIView(generics.CreateAPIView):
# # #     serializer_class = CustomUserCreationSerializer

# # #     def create(self, request, *args, **kwargs):
# # #         serializer = self.get_serializer(data=request.data)
# # #         if serializer.is_valid():
# # #             user = serializer.save()
# # #             user.is_active = False
# # #             user.save()

# # #             otp = generate_otp()
# # #             RegistrationCode.objects.create(
# # #                 phone_number=user.phone_number,
# # #                 code=otp,
# # #                 expires_at=timezone.now() + timedelta(minutes=10)
# # #             )

# # #             send_otp(user.phone_number, otp)

# # #             return Response({
# # #                 "message": "User registered successfully. OTP sent to your phone.",
# # #                 "user_id": user.id,
# # #                 "first_name": user.first_name,
# # #                 "last_name": user.last_name,
# # #                 "phone_number": user.phone_number,
# # #             }, status=status.HTTP_201_CREATED)
# # #         else:
# # #             logger.error(f"Registration failed with errors: {serializer.errors}")
# # #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # @csrf_exempt
# # @require_http_methods(["POST"])
# # def login_user(request):
# #     try:
# #         data = json.loads(request.body)
# #         phone_number = data.get('phone_number')
# #         password = data.get('password')

# #         if not phone_number or not password:
# #             return JsonResponse({"message": "Phone number and password are required"}, status=400)

# #         formatted_number = format_phone_number(phone_number)
# #         if not formatted_number:
# #             return JsonResponse({"message": "Invalid phone number format"}, status=400)

# #         user = authenticate(username=formatted_number, password=password)
# #         if user:
# #             if user.is_active:
# #                 django_login(request, user)
# #                 refresh = RefreshToken.for_user(user)
# #                 return JsonResponse({
# #                     "message": "Login successful. Welcome!",
# #                     "first_name": user.first_name,
# #                     "last_name": user.last_name,
# #                     "refresh": str(refresh),
# #                     "access": str(refresh.access_token),
# #                 }, status=200)
# #             else:
# #                 otp = generate_otp()
# #                 RegistrationCode.objects.create(
# #                     phone_number=user.phone_number,
# #                     code=otp,
# #                     expires_at=timezone.now() + timedelta(minutes=10)
# #                 )
# #                 send_otp(user.phone_number, otp)
# #                 return JsonResponse({"message": "Account not verified. OTP sent for verification."}, status=200)
# #         else:
# #             return JsonResponse({"message": "Invalid phone number or password"}, status=400)
# #     except json.JSONDecodeError:
# #         return JsonResponse({"message": "Invalid JSON data"}, status=400)
# #     except Exception as e:
# #         logger.error(f"Error during login: {str(e)}")
# #         return JsonResponse({"message": f"An error occurred during login: {str(e)}"}, status=500)

# # @api_view(['POST'])
# # def otp_verification(request, user_id):
# #     try:
# #         user = User.objects.get(pk=user_id)
# #     except User.DoesNotExist:
# #         return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# #     serializer = OTPVerificationSerializer(data=request.data)
# #     if serializer.is_valid():
# #         otp = serializer.validated_data['otp']
# #         try:
# #             registration_code = RegistrationCode.objects.get(phone_number=user.phone_number, code=otp)
# #             if registration_code.expires_at < timezone.now():
# #                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

# #             user.is_active = True
# #             user.save()
# #             registration_code.delete()

# #             refresh = RefreshToken.for_user(user)
# #             return Response({
# #                 "message": "OTP Verified Successfully. You can now access the system.",
# #                 "first_name": user.first_name,
# #                 "last_name": user.last_name,
# #                 "refresh": str(refresh),
# #                 "access": str(refresh.access_token),
# #             }, status=status.HTTP_200_OK)
# #         except RegistrationCode.DoesNotExist:
# #             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
# #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# # @csrf_exempt
# # @require_http_methods(["POST"])
# # @api_view(['POST'])
# # def password_reset_request(request):
# #     serializer = PasswordResetRequestSerializer(data=request.data)
# #     if serializer.is_valid():
# #         phone_number = serializer.validated_data['phone_number']
# #         try:
# #             user = User.objects.get(phone_number=phone_number)
# #             otp = generate_otp()
# #             RegistrationCode.objects.create(
# #                 phone_number=user.phone_number,
# #                 code=otp,
# #                 expires_at=timezone.now() + timedelta(minutes=10)
# #             )
# #             send_otp(user.phone_number, f"Password reset verification OTP is: {otp}")

# #             return Response({"message": "Password reset OTP sent to your phone"}, status=status.HTTP_200_OK)
# #         except User.DoesNotExist:
# #             return Response({"message": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
# #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# # @csrf_exempt
# # @require_http_methods(["POST"])
# # @api_view(['POST'])
# # def password_reset_confirm(request):
# #     serializer = SetPasswordSerializer(data=request.data)
# #     if serializer.is_valid():
# #         phone_number = serializer.validated_data['phone_number']
# #         new_password = serializer.validated_data['new_password']
# #         otp = serializer.validated_data['otp']

# #         try:
# #             user = User.objects.get(phone_number=phone_number)
# #             registration_code = RegistrationCode.objects.get(phone_number=phone_number, code=otp)
            
# #             if registration_code.expires_at < timezone.now():
# #                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

# #             user.set_password(new_password)
# #             user.save()
# #             registration_code.delete()

# #             return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
# #         except User.DoesNotExist:
# #             return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
# #         except RegistrationCode.DoesNotExist:
# #             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
# #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






# # @csrf_exempt
# # @require_http_methods(["POST"])
# # @api_view(['POST'])
# # def password_reset_confirm(request):
# #     serializer = SetPasswordSerializer(data=request.data)
# #     if serializer.is_valid():
# #         phone_number = serializer.validated_data['phone_number']
# #         new_password = serializer.validated_data['new_password']
# #         otp = serializer.validated_data['otp']

# #         try:
# #             user = User.objects.get(phone_number=phone_number)
# #             registration_code = RegistrationCode.objects.get(phone_number=phone_number, code=otp)
            
# #             if registration_code.expires_at < timezone.now():
# #                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

# #             user.set_password(new_password)
# #             user.save()
# #             registration_code.delete()

# #             return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
# #         except User.DoesNotExist:
# #             return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
# #         except RegistrationCode.DoesNotExist:
# #             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUE

# # ST)
# #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UserProfileAPIView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user

# class RegisteredUsersView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role == 'admin':
#             users = User.objects.all()
#         elif request.user.role == 'lawyer':
#             self.permission_classes = [HasLawyerPermissions]
#             users = User.objects.filter(role__in=['buyer', 'seller'])
#         elif request.user.role == 'buyer':
#             self.permission_classes = [HasBuyerPermissions]
#             users = User.objects.filter(role='seller')
#         elif request.user.role == 'seller':
#             self.permission_classes = [HasSellerPermissions]
#             users = User.objects.filter(role='buyer')
#         else:
#             users = User.objects.none()

#         user_data = [
#             {
#                 'id': user.id,
#                 'phone_number': user.phone_number,
#                 'first_name': user.first_name,
#                 'last_name': user.last_name,
#                 'is_active': user.is_active,
#                 'date_joined': user.date_joined,
#                 'role': user.role
#             }
#             for user in users
#         ]
#         return Response(user_data)

# @csrf_exempt
# @require_http_methods(["POST"])
# def logout_user(request):
#     try:
#         logout(request)
#         return JsonResponse({"message": "Logged out successfully"}, status=200)
#     except Exception as e:
#         logger.error(f"Error during logout: {str(e)}")
#         return JsonResponse({"message": f"An error occurred during logout: {str(e)}"}, status=500)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def home(request):
#     return Response({'message': 'Welcome to the home page!'}, status=status.HTTP_200_OK)


































# import json
# import logging
# import random
# import phonenumbers
# import requests
# from datetime import timedelta

# from django.conf import settings
# from django.contrib.auth import authenticate, login as django_login, logout, get_user_model
# from django.http import JsonResponse
# from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods

# from rest_framework import generics, status
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.views import APIView

# from api.serializers import (
#     CustomUserCreationSerializer,
#     OTPVerificationSerializer,
#     PasswordResetRequestSerializer,
#     SetPasswordSerializer,
#     UserProfileSerializer,
# )
# from users.models import RegistrationCode
# from users.permisions import HasBuyerPermissions, HasLawyerPermissions, HasSellerPermissions

# User = get_user_model()
# logger = logging.getLogger(__name__)

# def generate_otp():
#     return str(random.randint(100000, 999999))

# def send_otp(phone_number, otp):
#     headers = {
#         "Authorization": f"Basic {settings.SMSLEOPARD_ACCESS_TOKEN}",
#         "Content-Type": "application/json",
#     }
#     payload = {
#         "source": "Akirachix",
#         "message": f"Your OTP code is {otp}",
#         "destination": [{"number": phone_number}],
#     }
#     try:
#         response = requests.post(settings.SMSLEOPARD_API_URL, json=payload, headers=headers)
#         response.raise_for_status()
#         logger.info(f"OTP sent successfully to {phone_number}. Response: {response.json()}")
#         return response.json()
#     except requests.RequestException as e:
#         logger.error(f"Failed to send OTP: {str(e)}")
#         return {"error": str(e)}

# class UserCreateAPIView(generics.CreateAPIView):
#     serializer_class = CustomUserCreationSerializer

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             user.is_active = False
#             user.save()

#             otp = generate_otp()
#             RegistrationCode.objects.create(
#                 phone_number=user.phone_number,
#                 code=otp,
#                 expires_at=timezone.now() + timedelta(minutes=10)
#             )

#             send_otp(user.phone_number, otp)

#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 "message": "User registered successfully. OTP sent to your phone.",
#                 "user_id": user.id,
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "phone_number": user.phone_number,
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }, status=status.HTTP_201_CREATED)
#         else:
#             logger.error(f"Registration failed with errors: {serializer.errors}")
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# def login_user(request):
#     try:
#         data = json.loads(request.body)
#         phone_number = data.get('phone_number')
#         password = data.get('password')

#         if not phone_number or not password:
#             return JsonResponse({"message": "Phone number and password are required"}, status=400)

#         try:
#             parsed_number = phonenumbers.parse(phone_number, "KE")
#             if not phonenumbers.is_valid_number(parsed_number):
#                 return JsonResponse({"message": "Invalid phone number format"}, status=400)
#             formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
#         except phonenumbers.NumberParseException:
#             return JsonResponse({"message": "Invalid phone number format"}, status=400)

#         user = authenticate(username=formatted_number, password=password)
#         if user:
#             if user.is_active:
#                 django_login(request, user)
#                 refresh = RefreshToken.for_user(user)
#                 return JsonResponse({
#                     "message": "Login successful. Welcome!",
#                     "first_name": user.first_name,
#                     "last_name": user.last_name,
#                     "refresh": str(refresh),
#                     "access": str(refresh.access_token),
#                 }, status=200)
#             else:
#                 otp = generate_otp()
#                 RegistrationCode.objects.create(
#                     phone_number=user.phone_number,
#                     code=otp,
#                     expires_at=timezone.now() + timedelta(minutes=10)
#                 )
#                 send_otp(user.phone_number, otp)
#                 return JsonResponse({"message": "OTP sent. Please verify your OTP."}, status=200)
#         else:
#             return JsonResponse({"message": "Invalid phone number or password"}, status=400)
#     except json.JSONDecodeError:
#         return JsonResponse({"message": "Invalid JSON data"}, status=400)
#     except Exception as e:
#         logger.error(f"Error during login: {str(e)}")
#         return JsonResponse({"message": f"An error occurred during login: {str(e)}"}, status=500)

# @api_view(['POST'])
# def otp_verification(request, user_id):
#     try:
#         user = User.objects.get(pk=user_id)
#     except User.DoesNotExist:
#         return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

#     serializer = OTPVerificationSerializer(data=request.data)
#     if serializer.is_valid():
#         otp = serializer.validated_data['otp']
#         try:
#             registration_code = RegistrationCode.objects.get(phone_number=user.phone_number, code=otp)
#             if registration_code.expires_at < timezone.now():
#                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

#             user.is_active = True
#             user.save()
#             registration_code.delete()

#             refresh = RefreshToken.for_user(user)
#             return Response({
#                 "message": "OTP Verified Successfully. You can now access the system.",
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#             }, status=status.HTTP_200_OK)
#         except RegistrationCode.DoesNotExist:
#             return Response({"message": "Invalid OTP or user not found"}, status=status.HTTP_400_BAD_REQUEST)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# @api_view(['POST'])
# def password_reset_request(request):
#     serializer = PasswordResetRequestSerializer(data=request.data)
#     if serializer.is_valid():
#         phone_number = serializer.validated_data['phone_number']
#         try:
#             user = User.objects.get(phone_number=phone_number)
#             otp = generate_otp()
#             RegistrationCode.objects.create(
#                 phone_number=user.phone_number,
#                 code=otp,
#                 expires_at=timezone.now() + timedelta(minutes=10)
#             )
#             send_otp(user.phone_number, f"Password reset verification OTP is: {otp}")

#             return Response({"message": "Password reset OTP sent to your phone"}, status=status.HTTP_200_OK)
#         except User.DoesNotExist:
#             return Response({"message": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @csrf_exempt
# @require_http_methods(["POST"])
# @api_view(['POST'])
# def password_reset_confirm(request):
#     serializer = SetPasswordSerializer(data=request.data)
#     if serializer.is_valid():
#         phone_number = serializer.validated_data['phone_number']
#         new_password = serializer.validated_data['new_password']
#         otp = serializer.validated_data['otp']

#         try:
#             user = User.objects.get(phone_number=phone_number)
#             registration_code = RegistrationCode.objects.get(phone_number=phone_number, code=otp)
            
#             if registration_code.expires_at < timezone.now():
#                 return Response({"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

#             user.set_password(new_password)
#             user.save()
#             registration_code.delete()

#             return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
#         except User.DoesNotExist:
#             return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#         except RegistrationCode.DoesNotExist:
#             return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UserProfileAPIView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         return self.request.user

# class RegisteredUsersView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role == 'admin':
#             users = User.objects.all()
#         elif request.user.role == 'lawyer':
#             self.permission_classes = [HasLawyerPermissions]
#             users = User.objects.filter(role__in=['buyer', 'seller'])
#         elif request.user.role == 'buyer':
#             self.permission_classes = [HasBuyerPermissions]
#             users = User.objects.filter(role='seller')
#         elif request.user.role == 'seller':
#             self.permission_classes = [HasSellerPermissions]
#             users = User.objects.filter(role='buyer')
#         else:
#             users = User.objects.none()

#         user_data = [
#             {
#                 'id': user.id,
#                 'phone_number': user.phone_number,
#                 'first_name': user.first_name,
#                 'last_name': user.last_name,
#                 'is_active': user.is_active,
#                 'date_joined': user.date_joined,
#                 'role': user.role
#             }
#             for user in users
#         ]
#         return Response(user_data)

# @csrf_exempt
# @require_http_methods(["POST"])
# def logout_user(request):
#     try:
#         logout(request)
#         return JsonResponse({"message": "Logged out successfully"}, status=200)
#     except Exception as e:
#         logger.error(f"Error during logout: {str(e)}")
#         return JsonResponse({"message": f"An error occurred during logout: {str(e)}"}, status=500)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def home(request):
#     return Response({'message': 'Welcome to the home page!'}, status=status.HTTP_200_OK)










