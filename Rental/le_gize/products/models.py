from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category_list')

class Extra(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    one_time_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        parts = [f"{self.name} - ${self.price_per_day}/day"]
        if self.one_time_fee and self.one_time_fee > 0:
            parts.append(f"+ ${self.one_time_fee} one-time")
        return " ".join(parts)

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='products'
    )
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    total_stock = models.PositiveIntegerField(default=0)
    available_stock = models.PositiveIntegerField(default=0)
    reserved_stock = models.PositiveIntegerField(default=0)
    extras = models.ManyToManyField(Extra, blank=True, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (${self.price_per_day}/day)"
    
    def get_absolute_url(self):
        return reverse('products:detail', args=[str(self.id)])
    
    def reserve_stock(self, quantity):
        """Reserve stock for an order"""
        if quantity <= self.available_stock:
            self.available_stock -= quantity
            self.reserved_stock += quantity
            self.save()
            return True
        return False
    
    def release_stock(self, quantity):
        """Release reserved stock (when order is cancelled)"""
        if quantity <= self.reserved_stock:
            self.reserved_stock -= quantity
            self.available_stock += quantity
            self.save()
            return True
        return False
    
    def confirm_rental(self, quantity):
        """Confirm rental and remove from reserved stock"""
        if quantity <= self.reserved_stock:
            self.reserved_stock -= quantity
            self.save()
            return True
        return False
    
    @property
    def is_low_stock(self):
        return self.available_stock < 5
    
    @property
    def is_out_of_stock(self):
        return self.available_stock == 0
    
    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return 'Out of Stock'
        elif self.is_low_stock:
            return 'Low Stock'
        else:
            return 'In Stock'
