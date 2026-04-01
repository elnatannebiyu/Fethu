from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """Ensure superusers automatically get the admin role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('loading', 'Loading Personnel'),
        ('reception', 'Reception'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='reception')
    phone = models.CharField(max_length=15, blank=True)

    objects = CustomUserManager()
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    class Meta:
        app_label = 'accounts'
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)