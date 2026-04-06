from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.db import models
from django.core.paginator import Paginator

from core.mixins import admin_required, loading_personnel_required
from core.utils import apply_search_filters, flash_success, flash_error, render_form

from .models import LoadingPersonnel, Reception
from .forms import LoadingPersonnelForm, ReceptionForm
from orders.models import Order

# ============================================================================
# Personnel Management Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def personnel_list(request):
    """List all loading personnel (admin only)"""
    personnel = LoadingPersonnel.objects.select_related('user').all().order_by('employee_id')
    
    search_query = request.GET.get('search', '')
    personnel = apply_search_filters(personnel, search_query, [
        'employee_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'user__phone'
    ])

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        personnel = personnel.filter(is_active=True)
    elif status_filter == 'inactive':
        personnel = personnel.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(personnel, 9)  # 9 items per page (3x3 grid)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'personnel': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'personnel/personnel_list.html', context)

@login_required
@admin_required
def personnel_create(request):
    """Create new loading personnel (admin only)"""
    if request.method == 'POST':
        form = LoadingPersonnelForm(request.POST)
        if form.is_valid():
            personnel = form.save()
            flash_success(request, f'Loading personnel "{personnel.name}"', 'created')
            return redirect('personnel:list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = LoadingPersonnelForm()
    
    return render_form(
        request,
        'personnel/personnel_form.html',
        form,
        'Create Loading Personnel',
        'Create Personnel'
    )

@login_required
@admin_required
def personnel_edit(request, pk):
    """Edit loading personnel (admin only)"""
    personnel = get_object_or_404(LoadingPersonnel, pk=pk)
    
    if request.method == 'POST':
        form = LoadingPersonnelForm(request.POST, instance=personnel)
        if form.is_valid():
            personnel = form.save()
            flash_success(request, f'Loading personnel "{personnel.name}"', 'updated')
            return redirect('personnel:list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = LoadingPersonnelForm(instance=personnel)
    
    return render_form(
        request,
        'personnel/personnel_form.html',
        form,
        f'Edit Loading Personnel: {personnel.name}',
        'Update Personnel',
        {'personnel': personnel}
    )

@login_required
@admin_required
def personnel_delete(request, pk):
    """Delete loading personnel (admin only)"""
    personnel = get_object_or_404(LoadingPersonnel, pk=pk)
    
    if personnel.get_active_order_count() > 0:
        messages.error(request, f'Cannot delete "{personnel.name}" because they have active orders.')
        return redirect('personnel:list')
    
    if request.method == 'POST':
        name = personnel.name
        personnel.delete()
        flash_success(request, f'Loading personnel "{name}"', 'deleted')
        return redirect('personnel:list')
    
    return render(request, 'personnel/personnel_confirm_delete.html', {'personnel': personnel})

@login_required
@admin_required
def personnel_toggle_active(request, pk):
    """Toggle personnel active status (admin only)"""
    personnel = get_object_or_404(LoadingPersonnel, pk=pk)
    personnel.is_active = not personnel.is_active
    personnel.save()
    
    status = "activated" if personnel.is_active else "deactivated"
    flash_success(request, f'Loading personnel "{personnel.name}"', status)
    return redirect('personnel:list')

# ============================================================================
# Loading Personnel Dashboard Views (Loading Personnel Only)
# ============================================================================

@login_required
@loading_personnel_required
def my_assignments(request):
    """View for loading personnel to see their assignments"""
    try:
        personnel = request.user.loading_profile
        
        active = personnel.get_active_allocations()
        completed = personnel.get_completed_allocations()
        total_earned = personnel.get_total_earnings()
        
        context = {
            'active_assignments': active,
            'completed_assignments': completed,
            'total_earned': total_earned,
        }
        return render(request, 'personnel/my_assignments.html', context)
        
    except LoadingPersonnel.DoesNotExist:
        messages.error(request, "No loading personnel profile found.")
        return redirect('core:dashboard')

@login_required
@loading_personnel_required
def confirm_assignment(request, allocation_id):
    """Confirm loading assignment"""
    from orders.models import PersonnelAllocation
    
    allocation = get_object_or_404(PersonnelAllocation, id=allocation_id)
    
    if allocation.personnel.user != request.user:
        messages.error(request, "You don't have permission to confirm this assignment.")
        return redirect('personnel:my_assignments')
    
    # Here you could update a confirmed field
    allocation.confirmed = True
    allocation.save()
    messages.success(request, f"Assignment for Order {allocation.order.order_number} confirmed!")
    return redirect('personnel:my_assignments')

# ============================================================================
# Reception Management Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def reception_dashboard(request):
    """Reception management dashboard (admin only)"""
    reception = Reception.objects.select_related('user').all().order_by('employee_id')
    
    # Stats
    total_reception = reception.count()
    active_reception = reception.filter(is_active=True).count()
    inactive_reception = reception.filter(is_active=False).count()
    
    # Total orders created by all reception staff
    from orders.models import Order
    total_orders = Order.objects.filter(created_by__reception_profile__isnull=False).count()
    
    # Top reception staff by orders (limit to 5)
    top_reception = reception.annotate(
        order_count=models.Count('user__order_created_by')
    ).order_by('-order_count')[:5]
    
    # Recent reception staff (last 5 created)
    recent_reception = reception.order_by('-created_at')[:5]
    
    context = {
        'total_reception': total_reception,
        'active_reception': active_reception,
        'inactive_reception': inactive_reception,
        'total_orders': total_orders,
        'top_reception': top_reception,
        'recent_reception': recent_reception,
    }
    return render(request, 'personnel/reception_dashboard.html', context)

@login_required
@admin_required
def reception_list(request):
    """List all reception staff (admin only)"""
    reception = Reception.objects.select_related('user').all().order_by('employee_id')
    
    search_query = request.GET.get('search', '')
    reception = apply_search_filters(reception, search_query, [
        'employee_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'user__phone'
    ])

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        reception = reception.filter(is_active=True)
    elif status_filter == 'inactive':
        reception = reception.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(reception, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reception': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'personnel/reception_list.html', context)

@login_required
@admin_required
def reception_create(request):
    """Create new reception staff (admin only) - automatically creates User and Reception profile"""
    if request.method == 'POST':
        form = ReceptionForm(request.POST)
        if form.is_valid():
            reception = form.save()
            flash_success(request, f'Reception staff "{reception.name}"', 'created')
            return redirect('personnel:reception_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ReceptionForm()
    
    return render_form(
        request,
        'personnel/reception_form.html',
        form,
        'Create Reception Staff',
        'Create Reception'
    )

@login_required
@admin_required
def reception_edit(request, pk):
    """Edit reception staff (admin only)"""
    reception = get_object_or_404(Reception, pk=pk)
    
    if request.method == 'POST':
        form = ReceptionForm(request.POST, instance=reception)
        if form.is_valid():
            reception = form.save()
            flash_success(request, f'Reception staff "{reception.name}"', 'updated')
            return redirect('personnel:reception_list')
        flash_error(request, 'Please correct the errors below.')
    else:
        form = ReceptionForm(instance=reception)
    
    return render_form(
        request,
        'personnel/reception_form.html',
        form,
        f'Edit Reception Staff: {reception.name}',
        'Update Reception',
        {'reception': reception}
    )

@login_required
@admin_required
def reception_delete(request, pk):
    """Delete reception staff (admin only)"""
    reception = get_object_or_404(Reception, pk=pk)
    
    if request.method == 'POST':
        name = reception.name
        reception.delete()
        flash_success(request, f'Reception staff "{name}"', 'deleted')
        return redirect('personnel:reception_list')
    
    return render(request, 'personnel/reception_confirm_delete.html', {'reception': reception})

@login_required
@admin_required
def reception_toggle_active(request, pk):
    """Toggle reception active status (admin only)"""
    reception = get_object_or_404(Reception, pk=pk)
    reception.is_active = not reception.is_active
    reception.save()
    
    status = "activated" if reception.is_active else "deactivated"
    flash_success(request, f'Reception staff "{reception.name}"', status)
    return redirect('personnel:reception_list')

# ============================================================================
# Reception User Dashboard Views (Reception Staff Only)
# ============================================================================

@login_required
def reception_user_dashboard(request):
    """Dashboard for reception staff to see their own data"""
    from orders.models import PersonnelAllocation
    
    try:
        reception = request.user.reception_profile
    except Reception.DoesNotExist:
        messages.error(request, "No reception profile found for your account.")
        return redirect('orders:list')
    
    # Get all orders created by this reception staff
    orders = Order.objects.filter(created_by=request.user).select_related('customer')
    
    # Calculate statistics
    total_orders = orders.count()
    
    # Calculate total collected minus loading personnel commissions
    total_gross = 0
    total_commissions = 0
    
    for order in orders:
        order_amount = order.final_total or order.estimated_total
        if order_amount:
            total_gross += order_amount
            # Calculate commissions paid to loading personnel
            allocations = PersonnelAllocation.objects.filter(order=order)
            for allocation in allocations:
                commission = (order_amount * allocation.percentage) / 100
                total_commissions += commission
    
    total_collected = total_gross - total_commissions
    average_value = total_collected / total_orders if total_orders > 0 else 0
    
    # Get recent orders (last 10)
    recent_orders = orders.order_by('-created_at')[:10]
    
    context = {
        'reception': reception,
        'total_orders': total_orders,
        'total_collected': total_collected,
        'average_value': average_value,
        'recent_orders': recent_orders,
    }
    return render(request, 'personnel/reception_user_dashboard.html', context)