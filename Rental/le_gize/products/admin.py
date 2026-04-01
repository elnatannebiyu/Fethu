from django.contrib import admin
from .models import Category, Product, Extra

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'product_count')
    search_fields = ('name',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Extra)
class ExtraAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day', 'product_count')
    search_fields = ('name',)
    list_filter = ('products',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Used in Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_per_day', 'available_stock', 'total_stock', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('extras',)
    readonly_fields = ('created_at', 'updated_at', 'reserved_stock')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'image', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_per_day',)
        }),
        ('Inventory', {
            'fields': ('total_stock', 'available_stock', 'reserved_stock')
        }),
        ('Extras', {
            'fields': ('extras',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )