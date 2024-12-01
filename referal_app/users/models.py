from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
import random
import string


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError("Users must have a phone number")
        user = self.model(phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None):
        user = self.create_user(phone_number, password)
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser):
    phone_number = models.CharField(max_length=15, unique=True)
    invite_code = models.CharField(max_length=6, unique=True, blank=True)
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
    )
    is_active = models.BooleanField(default=True)
    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = "".join(
                random.choices(string.ascii_letters + string.digits, k=6)
            )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.phone_number


class Verification(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    code = models.CharField(max_length=4, blank=True)

    def save(self, *args, **kwargs):
        self.code = "".join(random.choices(string.digits, k=4))
        # тут нужно добавить отправку СМС с кодом
        super().save(*args, **kwargs)