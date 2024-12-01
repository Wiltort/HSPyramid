from rest_framework import serializers
from .models import UserProfile


class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone_number"]


class UserProfileSerializer(serializers.ModelSerializer):
    referrals = ReferralSerializer(many=True, read_only=True)
    referred_by = ReferralSerializer(read_only=True)


    class Meta:
        model = UserProfile
        fields = ["phone_number", "invite_code", "referred_by", "referrals"]
        extra_kwargs = {
            'phone_number': {'required': False},
            'invite_code': {'required': False},
        }
