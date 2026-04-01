from django import forms
from .models import Product, Category, Extra

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price_per_day', 
                  'total_stock', 'available_stock', 'extras', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter product description...'}),
            'extras': forms.SelectMultiple(attrs={'class': 'select-multiple', 'size': '5'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apply CSS classes to all fields
        for field_name, field in self.fields.items():
            if field_name == 'image':
                field.widget.attrs.update({'class': 'file-input', 'accept': 'image/*'})
            elif field_name == 'is_active':
                field.widget.attrs.update({'class': 'checkbox-input'})
            elif field_name == 'extras':
                field.widget.attrs.update({'class': 'select-multiple input-field'})
            else:
                field.widget.attrs.update({'class': 'input-field'})
        
        # Make image not required
        self.fields['image'].required = False
        
        # For new products, make available_stock read-only
        if not self.instance.pk:
            self.fields['available_stock'].required = False
            self.fields['available_stock'].widget.attrs['readonly'] = True
            self.fields['available_stock'].help_text = "Will be set equal to Total Stock"
        
        # Set help texts
        self.fields['total_stock'].help_text = "Total number of items in inventory"
        self.fields['available_stock'].help_text = "Number of items available for rent"
        self.fields['reserved_stock'].help_text = "Number of items currently reserved"
        self.fields['price_per_day'].help_text = "Price per day in USD"
    
    def clean(self):
        cleaned_data = super().clean()
        total_stock = cleaned_data.get('total_stock')
        price = cleaned_data.get('price_per_day')
        
        # Validate price is positive
        if price and price <= 0:
            self.add_error('price_per_day', 'Price must be greater than zero')
        
        # For new products, set available_stock equal to total_stock
        if not self.instance.pk and total_stock is not None:
            cleaned_data['available_stock'] = total_stock
        elif self.instance.pk:
            # For existing products, ensure available_stock doesn't exceed total_stock
            available = cleaned_data.get('available_stock')
            if available and total_stock and available > total_stock:
                self.add_error('available_stock', 'Available stock cannot exceed total stock')
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter category description...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'input-field'})

class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['name', 'description', 'price_per_day']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter extra description...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'input-field'})
        
        # Add help text
        self.fields['price_per_day'].help_text = "Price per day in USD"
    
    def clean_price_per_day(self):
        price = self.cleaned_data.get('price_per_day')
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than zero')
        return price