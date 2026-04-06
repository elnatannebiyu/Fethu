from django import forms
from .models import LoadingPersonnel, Reception
from accounts.models import User
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class DebugDecimalField(forms.DecimalField):
    """DecimalField with debug logging"""
    def to_python(self, value):
        logger.info(f"DebugDecimalField.to_python called with value: {value!r}, type: {type(value)}")
        if value in self.empty_values:
            logger.info(f"Value is in empty_values: {self.empty_values}")
            return None
        try:
            result = Decimal(str(value))
            logger.info(f"Successfully converted to Decimal: {result}")
            return result
        except (InvalidOperation, ValueError) as e:
            logger.error(f"Failed to convert to Decimal: {e}")
            raise forms.ValidationError(f"Invalid decimal value: {value}")

class LoadingPersonnelForm(forms.ModelForm):
    # User creation fields
    username = forms.CharField(
        max_length=150,
        required=False,
        help_text="Username for the loading personnel account"
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="First name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Last name"
    )
    email = forms.EmailField(
        required=False,
        help_text="Email address"
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        help_text="Phone number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Password for the account"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Confirm password"
    )
    commission_rate = DebugDecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0',
            'max': '100',
            'inputmode': 'decimal',
            'pattern': '[0-9]*[.,]?[0-9]*'
        }),
        help_text="Commission rate percentage (0-100)"
    )
    
    class Meta:
        model = LoadingPersonnel
        fields = ['is_active', 'emergency_contact', 'emergency_phone', 'address', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        logger.info(f"Form __init__ called - Instance PK: {self.instance.pk}")
        logger.info(f"Form is bound: {self.is_bound}")
        if self.data:
            logger.info(f"Form data keys: {list(self.data.keys())}")
            if 'commission_rate' in self.data:
                logger.info(f"Commission rate in POST data: {self.data.get('commission_rate', '')}")
        
        # Pre-populate user fields when editing (only if form is NOT bound)
        if not self.is_bound and self.instance.pk and self.instance.user:
            logger.info(f"Editing mode - pre-populating user fields from instance")
            logger.info(f"Instance user commission_rate: {self.instance.user.commission_rate}")
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['commission_rate'].initial = self.instance.user.commission_rate
            logger.info(f"Set commission_rate initial to: {self.fields['commission_rate'].initial}")
        
        # Apply CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'checkbox-input'})
            elif field_name in ['address', 'notes']:
                field.widget.attrs.update({'class': 'textarea-field'})
            else:
                field.widget.attrs.update({'class': 'input-field'})
        
        # Add help texts
        self.fields['commission_rate'].help_text = "Percentage of order value (0-100)"
    
    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"Form clean() called - Instance PK: {self.instance.pk}")
        logger.info(f"Cleaned data: {cleaned_data}")
        logger.info(f"Commission rate field errors: {self.errors.get('commission_rate', 'None')}")
        
        # Check if we're creating a new personnel (not editing)
        if not self.instance.pk:
            logger.info("Creating new personnel")
            username = cleaned_data.get('username')
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('confirm_password')
            
            logger.info(f"Username: {username}, Password provided: {bool(password)}, Confirm provided: {bool(password_confirm)}")
            
            if not username or not password:
                logger.error("Username or password missing")
                raise forms.ValidationError("Username and password are required for new personnel.")
            
            # Check password confirmation on creation
            if password != password_confirm:
                logger.error("Passwords do not match on creation")
                raise forms.ValidationError("Passwords do not match.")
            
            # Check if username already exists and if it's linked to a LoadingPersonnel
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                logger.error(f"Username '{username}' already exists")
                # Check if this user is already linked to a LoadingPersonnel
                if hasattr(existing_user, 'loading_profile'):
                    logger.error(f"User is already linked to LoadingPersonnel ID: {existing_user.loading_profile.id}")
                    raise forms.ValidationError(f"Username '{username}' is already linked to another loading personnel.")
                else:
                    logger.error(f"Username '{username}' exists but not linked to personnel - will reuse")
                    raise forms.ValidationError(f"Username '{username}' is already in use.")
        else:
            # Editing mode - check password confirmation only if password is being changed
            logger.info(f"Editing personnel ID: {self.instance.pk}")
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('confirm_password')
            
            logger.info(f"Password provided: {bool(password)}, Password confirm provided: {bool(password_confirm)}")
            
            # Only validate password confirmation if password field has a value
            # If password is empty, ignore confirm_password (user is not changing password)
            if password:
                if password != password_confirm:
                    logger.error("Passwords do not match on edit")
                    raise forms.ValidationError("Passwords do not match.")
            else:
                # Password not being changed, clear confirm_password so it doesn't cause issues
                cleaned_data['confirm_password'] = ''
                logger.info("Password not being changed, clearing confirm_password")
        
        logger.info("Form validation passed")
        return cleaned_data
    
    def save(self, commit=True):
        logger.info(f"Form save() called - Instance PK: {self.instance.pk}, Commit: {commit}")
        logger.info(f"Instance user before save: {self.instance.user if self.instance.pk else 'N/A (new instance)'}")
        
        # Create user if we're creating new personnel
        if not self.instance.pk:
            logger.info("Creating new user and personnel")
            username = self.cleaned_data['username']
            email = self.cleaned_data.get('email', '')
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            phone = self.cleaned_data.get('phone', '')
            
            # Get or create user
            # NOTE: Do NOT set role='loading' here because it triggers the signal
            # that auto-creates a LoadingPersonnel record. We'll set the role after.
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'role': 'user',  # Temporary role to avoid signal
                    'commission_rate': self.cleaned_data.get('commission_rate') or 10.00
                }
            )
            
            if created:
                logger.info(f"User created with ID: {user.id}")
                # Set password for newly created user
                user.set_password(self.cleaned_data['password'])
                user.save()
                logger.info(f"User password set and saved")
            else:
                logger.info(f"User with username '{username}' already exists! User ID: {user.id}")
                # Check if this user is already linked to a LoadingPersonnel
                if hasattr(user, 'loading_profile'):
                    logger.error(f"This user is already linked to LoadingPersonnel ID: {user.loading_profile.id}")
                    raise forms.ValidationError(f"User with username '{username}' is already linked to another loading personnel.")
                else:
                    logger.info(f"User exists but is not linked to any LoadingPersonnel yet - will reuse")
            
            self.instance.user = user
            logger.info(f"Instance user set to: {user.id}")
        else:
            # Editing mode - update user data
            logger.info(f"Updating existing personnel ID: {self.instance.pk}")
            user = self.instance.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.email = self.cleaned_data.get('email', '')
            user.phone = self.cleaned_data.get('phone', '')
            
            logger.info(f"User updated: first_name={user.first_name}, last_name={user.last_name}, email={user.email}, phone={user.phone}")
            
            # Update password if provided
            password = self.cleaned_data.get('password')
            if password:
                logger.info("Password is being changed")
                user.set_password(password)
            else:
                logger.info("Password not changed")
            
            # Handle commission_rate on user
            commission_rate = self.cleaned_data.get('commission_rate')
            logger.info(f"Commission rate from cleaned_data: {commission_rate}")
            
            if commission_rate is not None:
                user.commission_rate = commission_rate
                logger.info(f"Setting user commission_rate to: {commission_rate}")
            else:
                logger.info(f"Keeping existing user commission_rate: {user.commission_rate}")
            
            user.save()
            logger.info(f"User saved with ID: {user.id} with commission_rate: {user.commission_rate}")
        
        logger.info(f"Saving personnel instance with user_id: {self.instance.user.id if self.instance.user else 'None'}, commit: {commit}")
        
        try:
            result = super().save(commit=commit)
            if commit:
                logger.info(f"Personnel saved successfully with ID: {result.id}, Employee ID: {result.employee_id}")
            else:
                logger.info(f"Commit=False, personnel instance prepared but not saved to DB")
            return result
        except Exception as e:
            logger.error(f"Error saving personnel: {str(e)}")
            raise
    
    def save_m2m(self):
        """Handle many-to-many relationships (if any)"""
        if hasattr(super(), 'save_m2m'):
            super().save_m2m()
        logger.info("save_m2m() called")
    
    def clean_commission_rate(self):
        rate = self.cleaned_data.get('commission_rate')
        logger.info(f"clean_commission_rate called - rate value: {rate}, type: {type(rate)}")
        
        if rate is not None:
            # Validate it's a valid decimal number
            if not isinstance(rate, (int, float, Decimal)):
                raise forms.ValidationError("Commission rate must be a valid number.")
            
            # Validate range
            if rate < 0 or rate > 100:
                raise forms.ValidationError("Commission rate must be between 0 and 100.")
        
        return rate


class ReceptionForm(forms.ModelForm):
    """Form for creating and editing Reception staff - automatically creates User and Reception profile"""
    
    # User creation fields
    username = forms.CharField(
        max_length=150,
        required=False,
        help_text="Username for the reception account"
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="First name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Last name"
    )
    email = forms.EmailField(
        required=False,
        help_text="Email address"
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        help_text="Phone number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Password for the account"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Confirm password"
    )
    
    class Meta:
        model = Reception
        fields = ['is_active', 'emergency_contact', 'emergency_phone', 'address', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-populate user fields when editing
        if not self.is_bound and self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = self.instance.user.phone
        
        # Apply CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'checkbox-input'})
            elif field_name in ['address', 'notes']:
                field.widget.attrs.update({'class': 'textarea-field'})
            else:
                field.widget.attrs.update({'class': 'input-field'})
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if we're creating a new reception (not editing)
        if not self.instance.pk:
            username = cleaned_data.get('username')
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('confirm_password')
            
            if not username or not password:
                raise forms.ValidationError("Username and password are required for new reception staff.")
            
            # Check password confirmation on creation
            if password != password_confirm:
                raise forms.ValidationError("Passwords do not match.")
            
            # Check if username already exists
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                # Check if this user is already linked to a Reception
                if hasattr(existing_user, 'reception_profile'):
                    raise forms.ValidationError(f"Username '{username}' is already linked to another reception staff.")
                else:
                    raise forms.ValidationError(f"Username '{username}' is already in use.")
        else:
            # Editing mode - check password confirmation only if password is being changed
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('confirm_password')
            
            if password:
                if password != password_confirm:
                    raise forms.ValidationError("Passwords do not match.")
            else:
                cleaned_data['confirm_password'] = ''
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save both User and Reception profile automatically"""
        
        # Create user if we're creating new reception
        if not self.instance.pk:
            username = self.cleaned_data['username']
            email = self.cleaned_data.get('email', '')
            first_name = self.cleaned_data.get('first_name', '')
            last_name = self.cleaned_data.get('last_name', '')
            phone = self.cleaned_data.get('phone', '')
            
            # Create user with role='reception'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'role': 'reception',
                    'commission_rate': 0.00  # Reception staff have no commission
                }
            )
            
            if created:
                # Set password for newly created user
                user.set_password(self.cleaned_data['password'])
                user.save()
            else:
                if hasattr(user, 'reception_profile'):
                    raise forms.ValidationError(f"User with username '{username}' is already linked to another reception staff.")
            
            self.instance.user = user
        else:
            # Editing mode - update user data
            user = self.instance.user
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.email = self.cleaned_data.get('email', '')
            user.phone = self.cleaned_data.get('phone', '')
            
            # Update password if provided
            password = self.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            # Ensure role stays reception and commission is 0
            user.role = 'reception'
            user.commission_rate = 0.00
            user.save()
        
        # Save Reception instance
        return super().save(commit=commit)