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

    # Fields
    username = models.CharField(max_length=150, unique=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)

    # Optional profile image
    profile_image = models.ImageField(
        upload_to='profile_images/',  # folder inside MEDIA_ROOT
        null=True,  # not required
        blank=True  # not required
    )

    # Login using email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.role})"

    # Helper methods for checking roles
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_astrologer(self):
        return self.role == self.ROLE_ASTROLOGER

    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER
