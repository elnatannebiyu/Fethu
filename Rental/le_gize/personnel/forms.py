from django import forms
from .models import LoadingPersonnel
from accounts.models import User

class LoadingPersonnelForm(forms.ModelForm):
    class Meta:
        model = LoadingPersonnel
        fields = [
            'user', 'employee_id', 'commission_rate', 'phone_extension',
            'emergency_contact', 'emergency_phone', 'address', 'notes', 'is_active'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'is_active':
                field.widget.attrs.update({'class': 'checkbox-input'})
            elif field_name in ['address', 'notes']:
                field.widget.attrs.update({'class': 'input-field', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'input-field'})
        
        # For new personnel, only show users with role='loading' that aren't already assigned
        if not self.instance.pk:
            assigned_users = LoadingPersonnel.objects.values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='loading',
                is_active=True
            ).exclude(id__in=assigned_users)
            self.fields['user'].empty_label = "Select a user..."
        
        # Add help texts
        self.fields['employee_id'].help_text = "Unique employee identification number"
        self.fields['commission_rate'].help_text = "Percentage of order value (0-100)"
        self.fields['phone_extension'].help_text = "Internal phone extension (optional)"
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            # Check if employee_id already exists (excluding current instance)
            queryset = LoadingPersonnel.objects.filter(employee_id__iexact=employee_id)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("This Employee ID is already in use.")
        return employee_id.upper() if employee_id else employee_id
    
    def clean_commission_rate(self):
        rate = self.cleaned_data.get('commission_rate')
        if rate and (rate < 0 or rate > 100):
            raise forms.ValidationError("Commission rate must be between 0 and 100.")
        return rate