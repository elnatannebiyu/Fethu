import csv
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone

from core.mixins import admin_required
from orders.models import Order, Customer
from products.models import Product
from personnel.models import LoadingPersonnel
from orders.models import PersonnelAllocation  # Import from orders.models

# ============================================================================
# Report Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def report_dashboard(request):
    """Main reporting dashboard (admin only)"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_orders = Order.objects.count()
    active_orders = Order.objects.filter(status='active').count()
    completed_orders = Order.objects.filter(status='completed').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    completed_orders_qs = Order.objects.filter(status='completed')
    total_revenue = completed_orders_qs.aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    
    weekly_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
    weekly_revenue = Order.objects.filter(
        status='completed', 
        created_at__date__gte=week_ago
    ).aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    top_products = Product.objects.annotate(
        rental_count=Count('orderitem')
    ).order_by('-rental_count')[:5]
    
    personnel_earnings = LoadingPersonnel.objects.annotate(
        total_earned=Sum('allocations__salary_earned')
    ).filter(total_earned__isnull=False).order_by('-total_earned')[:5]
    
    context = {
        'total_orders': total_orders,
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_customers': total_customers,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'weekly_orders': weekly_orders,
        'weekly_revenue': weekly_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'personnel_earnings': personnel_earnings,
    }
    
    return render(request, 'reports/dashboard.html', context)

@login_required
@admin_required
def orders_report(request):
    """Orders report page with filters (admin only)"""
    orders = Order.objects.select_related('customer').all().order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    customer = request.GET.get('customer')
    if customer:
        orders = orders.filter(customer__full_name__icontains=customer)
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'total_amount': orders.aggregate(Sum('final_total'))['final_total__sum'] or 0,
        'filter_applied': bool(status or date_from or date_to or customer),
    }
    
    return render(request, 'reports/orders_report.html', context)

@login_required
@admin_required
def orders_report_csv(request):
    """Generate CSV report for orders (admin only)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="orders_report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order Number', 'Customer', 'Phone', 'Date', 'Status', 'Total', 'Prepayment', 'Remaining'])
    
    orders = Order.objects.select_related('customer').all().order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    for order in orders:
        writer.writerow([
            order.order_number,
            order.customer.full_name,
            order.customer.phone,
            order.created_at.strftime('%Y-%m-%d'),
            order.status,
            f"{order.final_total or order.estimated_total:.2f}",
            f"{order.prepayment_amount:.2f}",
            f"{order.remaining_amount or 0:.2f}"
        ])
    
    return response

@login_required
@admin_required
def products_report(request):
    """Product usage report (admin only)"""
    products = Product.objects.annotate(
        rental_count=Count('orderitem'),
        total_revenue=Sum('orderitem__subtotal')
    ).order_by('-rental_count')
    
    context = {
        'products': products,
        'total_products': products.count(),
        'total_revenue': products.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0,
    }
    
    return render(request, 'reports/products_report.html', context)

@login_required
@admin_required
def products_report_csv(request):
    """Generate CSV report for products (admin only)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="products_report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Product', 'Category', 'Price/Day', 'Total Stock', 'Available', 'Reserved', 'Rental Count', 'Total Revenue'])
    
    products = Product.objects.annotate(
        rental_count=Count('orderitem'),
        total_revenue=Sum('orderitem__subtotal')
    ).order_by('-rental_count')
    
    for product in products:
        writer.writerow([
            product.name,
            product.category.name if product.category else 'Uncategorized',
            f"{product.price_per_day:.2f}",
            product.total_stock,
            product.available_stock,
            product.reserved_stock,
            product.rental_count or 0,
            f"{product.total_revenue or 0:.2f}"
        ])
    
    return response

@login_required
@admin_required
def personnel_report(request):
    """Personnel salary report (admin only)"""
    personnel = LoadingPersonnel.objects.filter(is_active=True).annotate(
        total_earned=Sum('allocations__salary_earned'),
        orders_count=Count('allocations')
    ).order_by('-total_earned')
    
    context = {
        'personnel': personnel,
        'total_paid': personnel.aggregate(Sum('total_earned'))['total_earned__sum'] or 0,
    }
    
    return render(request, 'reports/personnel_report.html', context)

@login_required
@admin_required
def personnel_report_csv(request):
    """Generate CSV report for personnel salaries (admin only)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="personnel_report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'Name', 'Email', 'Phone', 'Orders Participated', 'Total Earned'])
    
    personnel = LoadingPersonnel.objects.filter(is_active=True).annotate(
        total_earned=Sum('allocations__salary_earned'),
        orders_count=Count('allocations')
    ).order_by('-total_earned')
    
    for p in personnel:
        writer.writerow([
            p.employee_id,
            p.user.get_full_name() or p.user.username,
            p.user.email,
            p.user.phone,
            p.orders_count or 0,
            f"{p.total_earned or 0:.2f}"
        ])
    
    return response

@login_required
@admin_required
def financial_report(request):
    """Financial summary report (admin only)"""
    today = timezone.now().date()
    
    daily_revenue = Order.objects.filter(
        status='completed',
        actual_return_date=today
    ).aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    week_ago = today - timedelta(days=7)
    weekly_revenue = Order.objects.filter(
        status='completed',
        actual_return_date__gte=week_ago
    ).aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    month_ago = today - timedelta(days=30)
    monthly_revenue = Order.objects.filter(
        status='completed',
        actual_return_date__gte=month_ago
    ).aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(Sum('final_total'))['final_total__sum'] or 0
    
    total_salaries = PersonnelAllocation.objects.filter(
        order__status='completed'
    ).aggregate(Sum('salary_earned'))['salary_earned__sum'] or 0
    
    context = {
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'total_salaries': total_salaries,
        'net_profit': total_revenue - total_salaries,
    }
    
    return render(request, 'reports/financial_report.html', context)