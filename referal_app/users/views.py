from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import UserProfile, Verification
from .serializers import UserProfileSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
import time


class RegisterView(APIView):
    """
    Регистрация / вход по номеру телефона
    """

    def post(self, request):
        phone_number = request.data.get("phone_number")
        if not phone_number:
            return Response(
                {"error": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Делаем вид, что послали код верификации
        time.sleep(2)
        verification, created = Verification.objects.get_or_create(
            phone_number=phone_number
        )
        if not created:
            # Если уже были попытки подтвердить номер, верификация есть в базе
            verification.save()
        return Response(
            {"message": f"Verification code sent - {verification.code}"},
            status=status.HTTP_200_OK,
        )

    # После добавления отправки СМС убрать код


class CustomAuthToken(APIView):
    def post(self, request):
        """
        Ввод кода подтверждения
        """
        phone_number = request.data.get("phone_number")
        verification_code = request.data.get("verification_code")
        if not phone_number:
            return Response(
                {"error": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        verification = get_object_or_404(Verification, phone_number=phone_number)
        if not verification_code:
            return Response(
                {"error": "verification_code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if verification_code == verification.code:
            user = UserProfile.objects.filter(phone_number=phone_number).first()
            if not user:
                user = UserProfile.objects.create_user(phone_number=phone_number)
                user.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Invalid verification code"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        invite_code = request.data.get("invite_code")
        if invite_code:
            try:
                with transaction.atomic():
                    inviter = UserProfile.objects.get(invite_code=invite_code)
                    user = request.user
                    if user.referred_by is not None:
                        return Response(
                            {"error": "The user has already activated the invite code"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    if inviter == user:
                        return Response(
                            {"error": "Self-invitation is not allowed"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    user.referred_by = inviter
                    inviter.referrals.add(user)
                    inviter.save()
                    user.save()
                    return Response(
                        UserProfileSerializer(user).data,
                        status=status.HTTP_200_OK
                    )
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "Invalid invite code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {"error": "Invite code is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
