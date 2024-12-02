"""
URL configuration for referal_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from users.views import RegisterTemplateView, VerificationTemplateView, UserProfileTemplateView
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView

urlpatterns = [
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/v1/', include('users.urls')),
    path('', RegisterTemplateView.as_view(), name='register_template'),
    path('verify/', VerificationTemplateView.as_view(), name='verification_template'),
    path('profile/', UserProfileTemplateView.as_view(), name='profile_template'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),]
