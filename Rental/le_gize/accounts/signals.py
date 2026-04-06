from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_loading_personnel(sender, instance, created, **kwargs):
    """
    Automatically create a LoadingPersonnel record when a user with role='loading' is created.
    This allows users created via Django admin to appear in the Loading Personnel list.
    """
    if created and instance.role == 'loading':
        from personnel.models import LoadingPersonnel
        
        # Check if LoadingPersonnel already exists for this user
        if not hasattr(instance, 'loading_profile'):
            LoadingPersonnel.objects.create(
                user=instance,
                commission_rate=10.00,
                is_active=True
            )


@receiver(post_save, sender=User)
def create_reception(sender, instance, created, **kwargs):
    """
    Automatically create a Reception record when a user with role='reception' is created.
    This allows users created via Django admin to appear in the Reception list.
    """
    if created and instance.role == 'reception':
        from personnel.models import Reception
        
        # Check if Reception already exists for this user
        if not hasattr(instance, 'reception_profile'):
            Reception.objects.create(
                user=instance,
                is_active=True
            )
