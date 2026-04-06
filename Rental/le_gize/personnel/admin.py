from django.contrib import admin
from django import forms
from .models import LoadingPersonnel, Reception
from .forms import LoadingPersonnelForm

class LoadingPersonnelAdminForm(LoadingPersonnelForm):
    """Custom admin form that properly renders user fields"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ensure all custom user fields have proper widgets for admin rendering
        if 'username' in self.fields:
            self.fields['username'].widget = forms.TextInput(attrs={'class': 'vTextField'})
        if 'first_name' in self.fields:
            self.fields['first_name'].widget = forms.TextInput(attrs={'class': 'vTextField'})
        if 'last_name' in self.fields:
            self.fields['last_name'].widget = forms.TextInput(attrs={'class': 'vTextField'})
        if 'email' in self.fields:
            self.fields['email'].widget = forms.EmailInput(attrs={'class': 'vTextField'})
        if 'phone' in self.fields:
            self.fields['phone'].widget = forms.TextInput(attrs={'class': 'vTextField'})
        if 'password' in self.fields:
            self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'vTextField'})
        if 'confirm_password' in self.fields:
            self.fields['confirm_password'].widget = forms.PasswordInput(attrs={'class': 'vTextField'})
    
    def get_form_field_names(self):
        """Return all field names including custom ones"""
        return list(self.fields.keys())

@admin.register(LoadingPersonnel)
class LoadingPersonnelAdmin(admin.ModelAdmin):
    form = LoadingPersonnelAdminForm
    list_display = ('employee_id', 'user', 'is_active', 'commission_rate')
    list_filter = ('is_active',)
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('employee_id', 'hire_date', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle user creation properly"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Admin save_model called - change={change}, obj.pk={obj.pk}, obj.user={obj.user}")
        
        # The form.save(commit=False) has already:
        # 1. Created/updated the user and saved it to DB
        # 2. Set obj.user to the user instance
        # 3. Returned the unsaved personnel instance
        
        # We just need to save the personnel object once
        try:
            obj.save()
            logger.info(f"Personnel saved successfully with ID: {obj.id}")
        except Exception as e:
            logger.error(f"Error saving personnel in admin: {str(e)}")
            raise
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:  # Creating new personnel
            return (
                ('User Account', {
                    'fields': ('username', 'password', 'confirm_password', 'first_name', 'last_name', 'email', 'phone'),
                    'description': 'Create a new user account for this loading personnel. Password and confirmation must match.'
                }),
                ('Personnel Information', {
                    'fields': ('commission_rate', 'is_active')
                }),
                ('Contact Information', {
                    'fields': ('emergency_contact', 'emergency_phone', 'address')
                }),
                ('Additional Information', {
                    'fields': ('notes',)
                }),
            )
        else:  # Editing existing personnel
            return (
                ('User Account', {
                    'fields': ('username', 'first_name', 'last_name', 'email', 'phone', 'password', 'confirm_password'),
                    'description': 'Edit user information. Leave password fields blank to keep current password. If changing password, both fields must match.'
                }),
                ('Personnel Information', {
                    'fields': ('employee_id', 'commission_rate', 'is_active')
                }),
                ('Contact Information', {
                    'fields': ('emergency_contact', 'emergency_phone', 'address')
                }),
                ('Additional Information', {
                    'fields': ('notes',)
                }),
                ('Timestamps', {
                    'fields': ('hire_date', 'created_at', 'updated_at'),
                    'classes': ('collapse',)
                }),
            )

@admin.register(Reception)
class ReceptionAdmin(admin.ModelAdmin):
    form = LoadingPersonnelAdminForm
    list_display = ('employee_id', 'user', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('employee_id', 'hire_date', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle user creation properly"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Admin save_model called - change={change}, obj.pk={obj.pk}, obj.user={obj.user}")
        
        try:
            obj.save()
            logger.info(f"Reception saved successfully with ID: {obj.id}")
        except Exception as e:
            logger.error(f"Error saving reception in admin: {str(e)}")
            raise
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:  # Creating new reception
            return (
                ('User Account', {
                    'fields': ('username', 'password', 'confirm_password', 'first_name', 'last_name', 'email', 'phone'),
                    'description': 'Create a new user account for this reception staff.'
                }),
                ('Reception Information', {
                    'fields': ('is_active',)
                }),
                ('Contact Information', {
                    'fields': ('emergency_contact', 'emergency_phone', 'address')
                }),
                ('Additional Information', {
                    'fields': ('notes',)
                }),
            )
        else:  # Editing existing reception
            return (
                ('User Account', {
                    'fields': ('username', 'first_name', 'last_name', 'email', 'phone', 'password', 'confirm_password'),
                    'description': 'Edit user information. Leave password fields blank to keep current password.'
                }),
                ('Reception Information', {
                    'fields': ('employee_id', 'is_active')
                }),
                ('Contact Information', {
                    'fields': ('emergency_contact', 'emergency_phone', 'address')
                }),
                ('Additional Information', {
                    'fields': ('notes',)
                }),
                ('Timestamps', {
                    'fields': ('hire_date', 'created_at', 'updated_at'),
                    'classes': ('collapse',)
                }),
            )