from django.db import models
from django.conf import settings
from products.models import Product, Extra
from personnel.models import LoadingPersonnel
from personnel.models import LoadingPersonnel

class Customer(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    tax_id = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return self.full_name

class Order(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    prepayment_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2)
    prepayment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    start_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    
    final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order {self.order_number}"

class PersonnelAllocation(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    personnel = models.ForeignKey(LoadingPersonnel, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    salary_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    days_rented = models.IntegerField(default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

class OrderExtra(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='extras')
    extra = models.ForeignKey(Extra, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)