# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Role choices
    ROLE_ADMIN = "admin"
    ROLE_ASTROLOGER = "astrologer"
    ROLE_CUSTOMER = "customer"

    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_ASTROLOGER, "Astrologer"),
        (ROLE_CUSTOMER, "Customer"),
    )

    # Language codes
    LANG_EN = "en"
    LANG_TA = "ta"
    LANG_HI = "hi"

    LANGUAGE_CHOICES = (
        (LANG_EN, "English"),
        (LANG_TA, "Tamil"),
        (LANG_HI, "Hindi"),
    )

    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    is_premium = models.BooleanField(default=False)
    plan_type = models.CharField(max_length=50, default='free')  

    # Birth details
    birth_year = models.PositiveIntegerField(null=True, blank=True)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_day = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_hour = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_minute = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_place = models.CharField(max_length=255, null=True, blank=True)  # ✅ New field

    # Profile image
    profile_image = models.URLField(max_length=500, blank=True, null=True)

    # Language preference
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default=LANG_EN
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"] 

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_astrologer(self):
        return self.role == self.ROLE_ASTROLOGER

    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER
