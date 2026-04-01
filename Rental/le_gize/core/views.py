from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from orders.models import Order, PersonnelAllocation  # Added PersonnelAllocation from orders
from products.models import Product
from personnel.models import LoadingPersonnel

@login_required
@staff_member_required
def admin_dashboard(request):
    context = {
        'total_orders': Order.objects.count(),
        'active_orders': Order.objects.filter(status='active').count(),
        'completed_orders': Order.objects.filter(status='completed').count(),
        'total_products': Product.objects.count(),
        'low_stock_products': Product.objects.filter(available_stock__lt=5).count(),
        'recent_orders': Order.objects.order_by('-created_at')[:10],
    }
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def loading_dashboard(request):
    # Get loading personnel profile
    try:
        personnel = request.user.loading_profile
        allocations = PersonnelAllocation.objects.filter(
            personnel=personnel,
            order__status='active'
        ).select_related('order')
        
        completed = PersonnelAllocation.objects.filter(
            personnel=personnel,
            order__status='completed'
        ).select_related('order')[:20]
        
        total_earned = sum(a.salary_earned for a in completed)
    except:
        allocations = []
        completed = []
        total_earned = 0
    
    context = {
        'allocations': allocations,
        'completed': completed,
        'total_earned': total_earned,
    }
    return render(request, 'core/loading_dashboard.html', context)

@login_required
def reception_dashboard(request):
    return render(request, 'core/reception_dashboard.html')