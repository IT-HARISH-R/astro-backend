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

    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    # 🌙 Birth Details
    birth_year = models.PositiveIntegerField(null=True, blank=True)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_day = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_hour = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_minute = models.PositiveSmallIntegerField(null=True, blank=True)

    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

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
