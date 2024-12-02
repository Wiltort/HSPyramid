from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import UserProfile, Verification
from .serializers import UserProfileSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.urls import reverse
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
import time
import requests
from django.conf import settings


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
        try:
            verification, created = Verification.objects.get_or_create(
                phone_number=phone_number
            )
        except:
            return Response({"error": "Database is not connected"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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


class RegisterTemplateView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        phone_number = request.POST.get("phone_number")
        if phone_number:
            url = f"{settings.API_HOST}{reverse('register')}"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "phone_number": phone_number
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                message = response.json().get("message")
                return redirect(
                    f'{reverse("verification_template")}?message={message}&phone_number={phone_number}'
                )
            else:
                error_message = response.json().get("error")
                return render(request, "register.html", {"error": error_message})
        return render(request, "register.html", {"error": "Phone number is required"})


class VerificationTemplateView(View):
    def get(self, request):
        message = request.GET.get('message', '')
        phone_number = request.GET.get('phone_number', '')
        return render(request, 'verification.html', {'message': message, 'phone_number': phone_number})

    def post(self, request):
        verification_code = request.POST.get('verification_code')
        phone_number = request.POST.get('phone_number')
        if not verification_code:
            return render(request, 'verification.html', {'error': 'The code is required'})
        url = f"{settings.API_HOST}{reverse('verify')}"
        response = requests.post(url, json={
            'phone_number': phone_number,
            'verification_code': verification_code
        })
        if response.status_code == 200:
            # Handle successful verification
            token = response.json().get('token')
            request.session['auth_token'] = token
            return redirect(reverse('profile_template'))
        else:
            # Handle errors
            error_message = response.json().get('error', 'Invalid verification code')
            return render(request, 'verification.html', {'error': error_message})
        

class UserProfileTemplateView(View):
    def get(self, request):
        token = request.session.get('auth_token')
        if not token:
            return redirect(reverse('verification_template'))
        url = f"{settings.API_HOST}{reverse('profile')}"
        headers = {
            'Authorization': f'Token {token}'
        }
        # Make a GET request to the profile API
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Handle successful retrieval of profile data
            profile_data = response.json()
            return render(request, 'profile.html', {'profile': profile_data})
        else:
            # Handle errors
            error_message = response.json().get('error', 'Failed to retrieve profile data')
            return render(request, 'profile.html', {'error': error_message})
        
    def post(self, request):
        token = request.session.get('auth_token')
        if not token:
            return redirect(reverse('verification_template'))
        
        invite_code = request.POST.get('invite_code')
        if invite_code:
            url = f"{settings.API_HOST}{reverse('profile')}"
            headers = {
                'Authorization': f'Token {token}'
            }
            response = requests.put(url, json={'invite_code': invite_code}, headers=headers)

            if response.status_code == 200:
                message = "Invite code activated successfully."
                profile_data = response.json()
                return render(request, 'profile.html', {'profile': profile_data, 'message': message})
            else:
                error_message = response.json().get('error', 'Failed to activate invite code')
                return render(request, 'profile.html', {'error': error_message})
        else:
            return render(request, 'profile.html', {'error': 'Invite code is required'})