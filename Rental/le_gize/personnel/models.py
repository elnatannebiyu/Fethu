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
    employee_id = models.CharField(max_length=50, unique=True, editable=False)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Deprecated: Use user.commission_rate instead"
    )
    emergency_contact = models.CharField(max_length=100, blank=True, default='')
    emergency_phone = models.CharField(max_length=20, blank=True, default='')
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

    def save(self, *args, **kwargs):
        """Auto-generate employee_id if not set"""
        if not self.employee_id:
            # Get the next employee number
            last_personnel = LoadingPersonnel.objects.all().order_by('-id').first()
            if last_personnel:
                # Extract number from last employee_id (e.g., "LP-001" -> 1)
                last_num = int(last_personnel.employee_id.split('-')[1])
                next_num = last_num + 1
            else:
                next_num = 1
            # Format as LP-001, LP-002, etc.
            self.employee_id = f"LP-{next_num:03d}"
        super().save(*args, **kwargs)

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


class Reception(models.Model):
    """
    Model for reception staff who manage customer orders and inquiries
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reception_profile'
    )
    employee_id = models.CharField(max_length=50, unique=True, editable=False)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=100, blank=True, default='')
    emergency_phone = models.CharField(max_length=20, blank=True, default='')
    address = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reception"
        verbose_name_plural = "Reception"
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    def save(self, *args, **kwargs):
        """Auto-generate employee_id if not set"""
        if not self.employee_id:
            last_reception = Reception.objects.all().order_by('-id').first()
            if last_reception:
                last_num = int(last_reception.employee_id.split('-')[1])
                next_num = last_num + 1
            else:
                next_num = 1
            self.employee_id = f"RC-{next_num:03d}"
        super().save(*args, **kwargs)

    def get_created_orders_count(self):
        """Get number of orders created by this reception"""
        from orders.models import Order
        return Order.objects.filter(created_by=self.user).count()

    def get_active_orders_count(self):
        """Get number of active orders created by this reception"""
        from orders.models import Order
        return Order.objects.filter(created_by=self.user, status='active').count()