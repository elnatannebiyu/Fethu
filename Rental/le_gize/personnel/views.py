from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from core.mixins import admin_required, loading_personnel_required
from .models import LoadingPersonnel
from .forms import LoadingPersonnelForm

# ============================================================================
# Personnel Management Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def personnel_list(request):
    """List all loading personnel (admin only)"""
    personnel = LoadingPersonnel.objects.select_related('user').all().order_by('employee_id')
    
    search_query = request.GET.get('search', '')
    if search_query:
        personnel = personnel.filter(
            Q(employee_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        personnel = personnel.filter(is_active=True)
    elif status_filter == 'inactive':
        personnel = personnel.filter(is_active=False)
    
    context = {
        'personnel': personnel,
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
            messages.success(request, f'Loading personnel "{personnel.name}" created successfully!')
            return redirect('personnel:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoadingPersonnelForm()
    
    return render(request, 'personnel/personnel_form.html', {
        'form': form,
        'title': 'Create Loading Personnel',
        'submit_text': 'Create Personnel'
    })

@login_required
@admin_required
def personnel_edit(request, pk):
    """Edit loading personnel (admin only)"""
    personnel = get_object_or_404(LoadingPersonnel, pk=pk)
    
    if request.method == 'POST':
        form = LoadingPersonnelForm(request.POST, instance=personnel)
        if form.is_valid():
            personnel = form.save()
            messages.success(request, f'Loading personnel "{personnel.name}" updated successfully!')
            return redirect('personnel:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoadingPersonnelForm(instance=personnel)
    
    return render(request, 'personnel/personnel_form.html', {
        'form': form,
        'title': f'Edit Loading Personnel: {personnel.name}',
        'personnel': personnel,
        'submit_text': 'Update Personnel'
    })

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
        messages.success(request, f'Loading personnel "{name}" deleted successfully!')
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
    messages.success(request, f'Loading personnel "{personnel.name}" {status}!')
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
    messages.success(request, f"Assignment for Order {allocation.order.order_number} confirmed!")
    return redirect('personnel:my_assignments')