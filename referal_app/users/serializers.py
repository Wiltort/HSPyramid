from rest_framework import serializers
from .models import UserProfile


class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["phone_number"]


class UserProfileSerializer(serializers.ModelSerializer):
    referrals = ReferralSerializer(many=True, read_only=True)
    referred_by = ReferralSerializer(read_only=True)
    activated_invite_code = serializers.SerializerMethodField()


    class Meta:
        model = UserProfile
        fields = ["phone_number", "invite_code", "referred_by", "referrals", "activated_invite_code"]
        extra_kwargs = {
            'phone_number': {'required': False},
            'invite_code': {'required': False},
        }

    def get_activated_invite_code(self, obj):
        if obj.referred_by:
            return obj.referred_by.invite_code
        return None