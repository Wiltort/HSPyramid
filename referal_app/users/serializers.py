from rest_framework import serializers
from .models import UserProfile, Verification


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


class RegisterSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Некорректный номер телефона")
        return value

    def create(self, validated_data):
        phone_number = validated_data["phone_number"]
        verification, created = Verification.objects.get_or_create(phone_number=phone_number)
        if not created:
            verification.save()
        return verification


class VerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    verification_code = serializers.CharField(max_length=6)

    def validate(self, data):
        phone_number = data.get("phone_number")
        code = data.get("verification_code")
        try:
            verification = Verification.objects.get(phone_number=phone_number)
        except Verification.DoesNotExist:
            raise serializers.ValidationError("Verification not found")
        if verification.code != code:
            raise serializers.ValidationError("Invalid verification code")
        data["verification"] = verification
        return data
