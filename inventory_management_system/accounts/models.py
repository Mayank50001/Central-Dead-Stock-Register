from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email field is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# Custom User Model
class CustomUser(AbstractUser):
    username = None  # Remove default username field
    email = models.EmailField(unique=True)  # Use email as username
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('department', 'Department'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='department')
    department = models.CharField(max_length=255, blank=True, null=True)
    last_ip_address = models.GenericIPAddressField(null=True, blank=True)  # To track the last IP address
    last_login_device = models.DateTimeField(null=True, blank=True)  # To track when the device was last used
    last_logout_device = models.DateTimeField(null=True, blank=True)  # To track when the device was last used
    last_activity = models.DateTimeField(null=True, blank=True)  # To track when the user was last active

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email and password are required by default

    def __str__(self):
        return self.email
