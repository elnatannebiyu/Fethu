from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from .models import User

class UserCreationForm(BaseUserCreationForm):
    """
    Form for creating new users
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'input-field',
                'placeholder': self.fields[field].label
            })

class UserChangeForm(BaseUserChangeForm):
    """
    Form for editing users
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'input-field',
                'placeholder': self.fields[field].label
            })

class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their own profile
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'input-field',
                'placeholder': self.fields[field].label
            })