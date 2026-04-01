from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class LoadingPersonnel(models.Model):
    """
    Model for loading personnel who handle order fulfillment
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='loading_profile'
    )
    employee_id = models.CharField(max_length=50, unique=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    phone_extension = models.CharField(max_length=10, blank=True, default='')
    emergency_contact = models.CharField(max_length=100, blank=True, default='')
    emergency_phone = models.CharField(max_length=15, blank=True, default='')
    address = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Loading Personnel"
        verbose_name_plural = "Loading Personnel"
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    def get_active_allocations(self):
        """Get current active order allocations"""
        from orders.models import PersonnelAllocation
        return PersonnelAllocation.objects.filter(
            personnel=self,
            order__status='active'
        ).select_related('order')

    def get_completed_allocations(self):
        """Get completed order allocations"""
        from orders.models import PersonnelAllocation
        return PersonnelAllocation.objects.filter(
            personnel=self,
            order__status='completed'
        ).select_related('order')

    def get_total_earnings(self):
        """Calculate total earnings from all completed orders"""
        from orders.models import PersonnelAllocation
        total = PersonnelAllocation.objects.filter(
            personnel=self,
            order__status='completed'
        ).aggregate(total=models.Sum('salary_earned'))['total'] or 0
        return float(total)

    def get_active_order_count(self):
        """Get number of active orders"""
        return self.get_active_allocations().count()

    def get_completed_order_count(self):
        """Get number of completed orders"""
        return self.get_completed_allocations().count()