import os
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import UserProfile, Verification
from .serializers import UserProfileSerializer, RegisterSerializer, VerificationSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
import time


class RegisterView(APIView):
    """
    Регистрация / вход по номеру телефона
    """
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            verification = serializer.save()
            time.sleep(2) # имитация отправки кода
            return Response(
                {"message": f"Verification code sent - {verification.code}"},
                # После добавления отправки СМС убрать код отсюда!
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomAuthToken(APIView):
    serializer_class = VerificationSerializer
    def post(self, request):
        """
        Ввод кода подтверждения
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data["phone_number"]
            user = UserProfile.objects.filter(phone_number=phone_number).first()
            if not user:
                user = UserProfile.objects.create_user(phone_number=phone_number)
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if inviter == user:
                        return Response(
                            {"error": "Self-invitation is not allowed"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    user.referred_by = inviter
                    inviter.referrals.add(user)
                    inviter.save()
                    user.save()
                    return Response(
                        UserProfileSerializer(user).data, status=status.HTTP_200_OK
                    )
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "Invalid invite code"}, status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {"error": "Invite code is required"}, status=status.HTTP_400_BAD_REQUEST
        )