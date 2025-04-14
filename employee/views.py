from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model

from rest_framework.permissions import IsAuthenticated
from .serializers import UserSimpleSerializer

User = get_user_model()


# Login API (username orqali)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            })
        return Response({"error": "Username yoki parol noto‘g‘ri"}, status=status.HTTP_401_UNAUTHORIZED)


# Logout API
class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Tokenni qora ro‘yxatga qo‘shish
            return Response({"message": "Logout muvaffaqiyatli!"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Noto‘g‘ri token!"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # faqat autentifikatsiyalangan foydalanuvchining ma'lumotlarini olish
        user = request.user
        serializer = UserSimpleSerializer(user)
        return Response(serializer.data)
