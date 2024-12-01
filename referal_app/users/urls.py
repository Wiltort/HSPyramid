from django.urls import path, include
from .views import UserProfileView, RegisterView, CustomAuthToken


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', CustomAuthToken.as_view(), name='verify'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
