from django.contrib import admin
from .models import Customer, Order, OrderItem, OrderExtra, PersonnelAllocation

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderExtraInline(admin.TabularInline):
    model = OrderExtra
    extra = 0

class PersonnelAllocationInline(admin.TabularInline):
    model = PersonnelAllocation
    extra = 0

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'tax_id')
    search_fields = ('full_name', 'phone', 'tax_id')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'estimated_total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__full_name')
    inlines = [OrderItemInline, PersonnelAllocationInline]
    readonly_fields = ('order_number', 'created_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_per_day', 'days_rented', 'subtotal')
    list_filter = ('order__status', 'product')
    search_fields = ('order__order_number', 'product__name')
    readonly_fields = ('subtotal',)

@admin.register(OrderExtra)
class OrderExtraAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'extra', 'quantity', 'price_per_day', 'subtotal')
    list_filter = ('extra',)
    search_fields = ('order_item__order__order_number', 'extra__name')
    readonly_fields = ('subtotal',)

@admin.register(PersonnelAllocation)
class PersonnelAllocationAdmin(admin.ModelAdmin):
    list_display = ('order', 'personnel', 'percentage', 'salary_earned', 'commission_paid')
    list_filter = ('personnel', 'order__status')
    search_fields = ('order__order_number', 'personnel__employee_id', 'personnel__user__username')
    readonly_fields = ('salary_earned', 'commission_paid')
