from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator

from core.mixins import admin_required
from core.utils import apply_search_filters, flash_success, flash_error, render_form

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
    products = apply_search_filters(products, search_query, [
        'name', 'description', 'category__name'
    ])
    
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
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'name_reverse':
        products = products.order_by('-name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'oldest':
        products = products.order_by('created_at')
    elif sort_by == 'price_high':
        products = products.order_by('-price_per_day')
    elif sort_by == 'price_low':
        products = products.order_by('price_per_day')
    elif sort_by == 'stock_high':
        products = products.order_by('-available_stock')
    elif sort_by == 'stock_low':
        products = products.order_by('available_stock')
    else:
        products = products.order_by('name')
    
    paginator = Paginator(products, 12)
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
        'sort_by': sort_by,
        'total_count': products.count(),
    }
    return render(request, 'products/product_list.html', context)

@login_required
@admin_required
def product_detail(request, pk):
    """View product details (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    
    # Paginate extras
    extras = product.extras.all()
    paginator = Paginator(extras, 4)
    extras_page_number = request.GET.get('extras_page')
    extras_page = paginator.get_page(extras_page_number)
    
    context = {
        'product': product,
        'extras_page': extras_page,
    }
    return render(request, 'products/product_detail.html', context)

@login_required
@admin_required
def product_create(request):
    """Create a new product (admin only)"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            flash_success(request, f'Product "{product.name}"', 'created')
            return redirect('products:list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    return render_form(
        request,
        'products/product_form.html',
        form,
        'Create New Product',
        'Create Product'
    )

@login_required
@admin_required
def product_edit(request, pk):
    """Edit an existing product (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            flash_success(request, f'Product "{product.name}"', 'updated')
            return redirect('products:list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    return render_form(
        request,
        'products/product_form.html',
        form,
        f'Edit Product: {product.name}',
        'Update Product',
        {'product': product}
    )

@login_required
@admin_required
def product_delete(request, pk):
    """Delete a product (admin only)"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        name = product.name
        product.delete()
        flash_success(request, f'Product "{name}"', 'deleted')
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
    flash_success(request, f'Product "{product.name}"', status)
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
    )
    
    search_query = request.GET.get('search', '')
    if search_query:
        categories = apply_search_filters(categories, search_query, [
            'name', 'description'
        ])
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        categories = categories.order_by('name')
    elif sort_by == 'name_reverse':
        categories = categories.order_by('-name')
    elif sort_by == 'newest':
        categories = categories.order_by('-created_at')
    elif sort_by == 'oldest':
        categories = categories.order_by('created_at')
    elif sort_by == 'products_high':
        categories = categories.order_by('-product_count')
    elif sort_by == 'products_low':
        categories = categories.order_by('product_count')
    else:
        categories = categories.order_by('name')
    
    paginator = Paginator(categories, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/category_list.html', {
        'page_obj': page_obj, 
        'categories': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    })

@login_required
@admin_required
def category_detail(request, pk):
    """View category details with paginated products (admin only)"""
    category = get_object_or_404(Category, pk=pk)
    
    # Paginate products
    products = category.products.all().select_related('category').prefetch_related('extras')
    paginator = Paginator(products, 8)
    products_page_number = request.GET.get('products_page')
    products_page = paginator.get_page(products_page_number)
    
    context = {
        'category': category,
        'products_page': products_page,
    }
    return render(request, 'products/category_detail.html', context)

@login_required
@admin_required
def category_create(request):
    """Create a new category (admin only)"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            flash_success(request, f'Category "{category.name}"', 'created')
            return redirect('products:category_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()
    
    return render_form(
        request,
        'products/category_form.html',
        form,
        'Create New Category',
        'Create Category'
    )

@login_required
@admin_required
def category_edit(request, pk):
    """Edit a category (admin only)"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            flash_success(request, f'Category "{category.name}"', 'updated')
            return redirect('products:category_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm(instance=category)
    
    return render_form(
        request,
        'products/category_form.html',
        form,
        f'Edit Category: {category.name}',
        'Update Category',
        {'category': category}
    )

@login_required
@admin_required
def category_delete(request, pk):
    """Delete a category (admin only)"""
    category = get_object_or_404(Category, pk=pk)
    
    if category.products.exists():
        flash_error(request, f'Cannot delete category "{category.name}" because it has associated products.')
        return redirect('products:category_list')
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        flash_success(request, f'Category "{name}"', 'deleted')
        return redirect('products:category_list')
    
    return render(request, 'products/category_confirm_delete.html', {'category': category})

@login_required
@admin_required
def extra_list(request):
    """List all extras (admin only)"""
    extras = Extra.objects.annotate(
        product_count=Count('products')
    )
    
    search_query = request.GET.get('search', '')
    if search_query:
        extras = apply_search_filters(extras, search_query, [
            'name', 'description'
        ])
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        extras = extras.order_by('name')
    elif sort_by == 'name_reverse':
        extras = extras.order_by('-name')
    elif sort_by == 'newest':
        extras = extras.order_by('-created_at')
    elif sort_by == 'oldest':
        extras = extras.order_by('created_at')
    elif sort_by == 'price_high':
        extras = extras.order_by('-price_per_day')
    elif sort_by == 'price_low':
        extras = extras.order_by('price_per_day')
    elif sort_by == 'product_count_high':
        extras = extras.order_by('-product_count')
    elif sort_by == 'product_count_low':
        extras = extras.order_by('product_count')
    else:
        extras = extras.order_by('name')
    
    paginator = Paginator(extras, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/extra_list.html', {
        'page_obj': page_obj,
        'extras': page_obj,
        'search_query': search_query,
        'sort_by': sort_by,
    })

@login_required
@admin_required
def extra_create(request):
    """Create a new extra (admin only)"""
    if request.method == 'POST':
        form = ExtraForm(request.POST)
        if form.is_valid():
            extra = form.save()
            flash_success(request, f'Extra "{extra.name}"', 'created')
            return redirect('products:extra_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ExtraForm()
    
    return render_form(
        request,
        'products/extra_form.html',
        form,
        'Create New Extra',
        'Create Extra'
    )

@login_required
@admin_required
def extra_edit(request, pk):
    """Edit an extra (admin only)"""
    extra = get_object_or_404(Extra, pk=pk)
    
    if request.method == 'POST':
        form = ExtraForm(request.POST, instance=extra)
        if form.is_valid():
            extra = form.save()
            flash_success(request, f'Extra "{extra.name}"', 'updated')
            return redirect('products:extra_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ExtraForm(instance=extra)
    
    return render_form(
        request,
        'products/extra_form.html',
        form,
        f'Edit Extra: {extra.name}',
        'Update Extra',
        {'extra': extra}
    )

@login_required
@admin_required
def extra_delete(request, pk):
    """Delete an extra (admin only)"""
    extra = get_object_or_404(Extra, pk=pk)
    
    if extra.products.exists():
        flash_error(request, f'Cannot delete extra "{extra.name}" because it is used by products.')
        return redirect('products:extra_list')
    
    if request.method == 'POST':
        name = extra.name
        extra.delete()
        flash_success(request, f'Extra "{name}"', 'deleted')
        return redirect('products:extra_list')
    
    return render(request, 'products/extra_confirm_delete.html', {'extra': extra})