from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from core.mixins import admin_required
from .models import Product, Category, Extra
from .forms import ProductForm, CategoryForm, ExtraForm

# ============================================================================
# Product Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def product_list(request):
    """List all products with filtering and search (admin only)"""
    products = Product.objects.all().select_related('category').prefetch_related('extras')
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    
    status = request.GET.get('status', '')
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    stock = request.GET.get('stock', '')
    if stock == 'low':
        products = products.filter(available_stock__lt=5, available_stock__gt=0)
    elif stock == 'out':
        products = products.filter(available_stock=0)
    elif stock == 'in':
        products = products.filter(available_stock__gt=0)
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_id,
        'status_filter': status,
        'stock_filter': stock,
        'total_count': products.count(),
    }
    return render(request, 'products/product_list.html', context)

@login_required
@admin_required
def product_detail(request, pk):
    """View product details (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
@admin_required
def product_create(request):
    """Create a new product (admin only)"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('products:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Create New Product',
        'submit_text': 'Create Product'
    })

@login_required
@admin_required
def product_edit(request, pk):
    """Edit an existing product (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('products:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': f'Edit Product: {product.name}',
        'product': product,
        'submit_text': 'Update Product'
    })

@login_required
@admin_required
def product_delete(request, pk):
    """Delete a product (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted successfully!')
        return redirect('products:list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})

@login_required
@admin_required
def product_toggle_active(request, pk):
    """Toggle product active status (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save()
    
    status = "activated" if product.is_active else "deactivated"
    messages.success(request, f'Product "{product.name}" {status}!')
    return redirect('products:list')

# ============================================================================
# Category Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def category_list(request):
    """List all categories (admin only)"""
    categories = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    return render(request, 'products/category_list.html', {'categories': categories})

@login_required
@admin_required
def category_create(request):
    """Create a new category (admin only)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'title': 'Create New Category',
        'submit_text': 'Create Category'
    })

@login_required
@admin_required
def category_edit(request, pk):
    """Edit a category (admin only)"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'title': f'Edit Category: {category.name}',
        'category': category,
        'submit_text': 'Update Category'
    })

@login_required
@admin_required
def category_delete(request, pk):
    """Delete a category (admin only)"""
    category = get_object_or_404(Category, pk=pk)
    
    if category.products.exists():
        messages.error(request, f'Cannot delete category "{category.name}" because it has associated products.')
        return redirect('products:category_list')
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('products:category_list')
    
    return render(request, 'products/category_confirm_delete.html', {'category': category})

# ============================================================================
# Extra Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def extra_list(request):
    """List all extras (admin only)"""
    extras = Extra.objects.annotate(
        product_count=Count('products')
    ).order_by('name')
    
    return render(request, 'products/extra_list.html', {'extras': extras})

@login_required
@admin_required
def extra_create(request):
    """Create a new extra (admin only)"""
    if request.method == 'POST':
        form = ExtraForm(request.POST)
        if form.is_valid():
            extra = form.save()
            messages.success(request, f'Extra "{extra.name}" created successfully!')
            return redirect('products:extra_list')
    else:
        form = ExtraForm()
    
    return render(request, 'products/extra_form.html', {
        'form': form,
        'title': 'Create New Extra',
        'submit_text': 'Create Extra'
    })

@login_required
@admin_required
def extra_edit(request, pk):
    """Edit an extra (admin only)"""
    extra = get_object_or_404(Extra, pk=pk)
    
    if request.method == 'POST':
        form = ExtraForm(request.POST, instance=extra)
        if form.is_valid():
            extra = form.save()
            messages.success(request, f'Extra "{extra.name}" updated successfully!')
            return redirect('products:extra_list')
    else:
        form = ExtraForm(instance=extra)
    
    return render(request, 'products/extra_form.html', {
        'form': form,
        'title': f'Edit Extra: {extra.name}',
        'extra': extra,
        'submit_text': 'Update Extra'
    })

@login_required
@admin_required
def extra_delete(request, pk):
    """Delete an extra (admin only)"""
    extra = get_object_or_404(Extra, pk=pk)
    
    if extra.products.exists():
        messages.error(request, f'Cannot delete extra "{extra.name}" because it is used by products.')
        return redirect('products:extra_list')
    
    if request.method == 'POST':
        name = extra.name
        extra.delete()
        messages.success(request, f'Extra "{name}" deleted successfully!')
        return redirect('products:extra_list')
    
    return render(request, 'products/extra_confirm_delete.html', {'extra': extra})