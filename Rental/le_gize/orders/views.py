import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.mixins import reception_required, loading_personnel_required, admin_required
from products.models import Product, Extra
from personnel.models import LoadingPersonnel
from personnel.models import LoadingPersonnel
from orders.models import PersonnelAllocation  # Import from orders.models

# Configure logger
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

ORDER_STATUS_CHOICES = [
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_role_based_orders(user):
    """
    Get orders based on user role
    """
    if user.role == 'loading':
        try:
            personnel = user.loading_profile
            return Order.objects.filter(
                personnel_allocations__personnel=personnel
            ).distinct()
        except LoadingPersonnel.DoesNotExist:
            return Order.objects.none()
    else:
        return Order.objects.all()


def calculate_order_totals(items, days):
    """
    Calculate order totals from items and days
    """
    total = Decimal('0.00')
    details = []
    
    for item in items:
        try:
            product = Product.objects.get(id=item['product_id'])
            quantity = int(item['quantity'])
            product_total = product.price_per_day * quantity * days
            
            extras_list = []
            extras_total = Decimal('0.00')
            
            for extra_id in item.get('extras', []):
                extra = Extra.objects.get(id=extra_id)
                extra_total = extra.price_per_day * quantity * days
                extras_total += extra_total
                extras_list.append({
                    'id': extra.id,
                    'name': extra.name,
                    'price': float(extra.price_per_day),
                    'total': float(extra_total)
                })
            
            item_total = product_total + extras_total
            total += item_total
            
            details.append({
                'product_id': product.id,
                'product_name': product.name,
                'quantity': quantity,
                'price_per_day': float(product.price_per_day),
                'extras': extras_list,
                'subtotal': float(item_total)
            })
            
        except (Product.DoesNotExist, Extra.DoesNotExist) as e:
            logger.error(f"Error calculating totals: {e}")
            continue
    
    return float(total), details


def validate_personnel_allocations(personnel_data):
    """
    Validate personnel allocations sum to 100%
    """
    if not personnel_data:
        return True, 0
    
    total = sum(float(p.get('percentage', 0)) for p in personnel_data)
    return abs(total - 100.0) < 0.01, total

# ============================================================================
# ORDER PAGE VIEWS
# ============================================================================

@login_required
@reception_required
def order_page(request):
    """
    Main order creation page (reception and admin only)
    """
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    
    context = {
        'products': Product.objects.filter(
            is_active=True, 
            available_stock__gt=0
        ).select_related('category').prefetch_related('extras'),
        'personnel': LoadingPersonnel.objects.filter(
            is_active=True
        ).select_related('user'),
        'today': today,
        'next_week': next_week,
        'status_choices': ORDER_STATUS_CHOICES,
    }
    return render(request, 'orders/order_page.html', context)


@login_required
def order_list(request):
    """
    List all orders with filters (role-based access)
    """
    orders = get_role_based_orders(request.user).select_related(
        'customer', 'created_by'
    ).prefetch_related(
        'items', 'personnel_allocations__personnel__user'
    ).order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__full_name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Annotate with item count
    orders = orders.annotate(item_count=Count('items'))
    
    context = {
        'orders': orders,
        'status_choices': ORDER_STATUS_CHOICES,
        'current_status': status,
        'search_query': search or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'is_loading': request.user.role == 'loading',
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """
    View order details with permission checks
    """
    order = get_object_or_404(
        Order.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related(
            'items__product',
            'items__extras__extra',
            'personnel_allocations__personnel__user'
        ),
        id=order_id
    )
    
    # Permission check
    if request.user.role == 'loading':
        if not order.personnel_allocations.filter(
            personnel__user=request.user
        ).exists():
            messages.error(request, "You don't have permission to view this order.")
            return redirect('orders:list')
    elif request.user.role not in ['admin', 'reception'] and not request.user.is_superuser:
        messages.error(request, "You don't have permission to view this order.")
        return redirect('core:dashboard')
    
    # Calculate totals
    order.item_count = order.items.count()
    
    context = {
        'order': order,
        'can_cancel': order.status == 'active' and request.user.role == 'admin',
        'can_process_return': order.status == 'active' and request.user.role in ['admin', 'reception'],
    }
    return render(request, 'orders/order_detail.html', context)

# ============================================================================
# RETURN PAGE VIEWS
# ============================================================================

@login_required
@reception_required
def return_page(request):
    """
    Return page for processing order returns (reception and admin only)
    """
    today = timezone.now().date()
    
    context = {
        'today': today,
        'active_orders_count': Order.objects.filter(status='active').count(),
    }
    return render(request, 'orders/return_page.html', context)

# ============================================================================
# LOADING PERSONNEL VIEWS
# ============================================================================

@login_required
@loading_personnel_required
def assigned_orders(request):
    """
    View for loading personnel to see their assigned orders
    """
    try:
        personnel = request.user.loading_profile
        
        active_assignments = PersonnelAllocation.objects.filter(
            personnel=personnel,
            order__status='active'
        ).select_related(
            'order', 'order__customer'
        ).order_by('order__expected_return_date')
        
        completed_assignments = PersonnelAllocation.objects.filter(
            personnel=personnel,
            order__status='completed'
        ).select_related(
            'order', 'order__customer'
        ).order_by('-order__actual_return_date')[:20]
        
        # Calculate stats
        total_earned = completed_assignments.aggregate(
            total=Sum('salary_earned')
        )['total'] or 0
        
        context = {
            'active_assignments': active_assignments,
            'completed_assignments': completed_assignments,
            'total_earned': total_earned,
            'active_count': active_assignments.count(),
            'completed_count': completed_assignments.count(),
        }
        
    except LoadingPersonnel.DoesNotExist:
        context = {
            'active_assignments': [],
            'completed_assignments': [],
            'total_earned': 0,
            'active_count': 0,
            'completed_count': 0,
            'error': 'No loading personnel profile found.'
        }
    
    return render(request, 'orders/assigned_orders.html', context)


@login_required
@loading_personnel_required
def confirm_loading(request, allocation_id):
    """
    Confirm loading assignment
    """
    allocation = get_object_or_404(
        PersonnelAllocation.objects.select_related('order', 'personnel__user'),
        id=allocation_id
    )
    
    if allocation.personnel.user != request.user:
        messages.error(request, "You don't have permission to confirm this assignment.")
        return redirect('orders:assigned_orders')
    
    if allocation.order.status != 'active':
        messages.error(request, "This order is no longer active.")
        return redirect('orders:assigned_orders')
    
    # Here you could add a confirmed field to the model
    # For now, just show success message
    messages.success(
        request, 
        f"Loading confirmed for Order {allocation.order.order_number}! "
        f"Your estimated salary: ${allocation.order.estimated_total * allocation.percentage / 100:.2f}"
    )
    
    return redirect('orders:assigned_orders')

# ============================================================================
# ADMIN ONLY VIEWS
# ============================================================================

@login_required
@admin_required
@transaction.atomic
def cancel_order(request, order_id):
    """
    Cancel an active order (admin only)
    """
    order = get_object_or_404(Order, id=order_id, status='active')
    
    if request.method == 'POST':
        # Release reserved stock
        for item in order.items.all():
            item.product.release_stock(item.quantity)
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        messages.success(request, f'Order {order.order_number} has been cancelled.')
        logger.info(f"Order {order.order_number} cancelled by {request.user.username}")
        
        return redirect('orders:list')
    
    return render(request, 'orders/cancel_confirm.html', {'order': order})

# ============================================================================
# API ENDPOINTS - ORDER CREATION
# ============================================================================

@login_required
@reception_required
def get_product_extras(request):
    """
    API endpoint to get extras for a specific product
    """
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'extras': []})
    
    try:
        product = Product.objects.prefetch_related('extras').get(id=product_id)
        extras = [{
            'id': e.id,
            'name': e.name,
            'price_per_day': float(e.price_per_day)
        } for e in product.extras.all()]
        
        return JsonResponse({'extras': extras})
    except Product.DoesNotExist:
        return JsonResponse({'extras': []})


@login_required
@reception_required
@require_http_methods(["POST"])
def check_availability_api(request):
    """
    API endpoint to check product availability
    """
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        
        availability = []
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'])
                requested_qty = int(item['quantity'])
                
                availability.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'available': product.available_stock,
                    'requested': requested_qty,
                    'short_by': max(0, requested_qty - product.available_stock),
                    'is_available': requested_qty <= product.available_stock
                })
            except Product.DoesNotExist:
                continue
        
        return JsonResponse({'availability': availability})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@reception_required
@require_http_methods(["POST"])
def calculate_order_total(request):
    """
    API endpoint to calculate order total
    """
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        days = int(data.get('days', 1))
        prepayment_percent = float(data.get('prepayment_percent', 50))
        
        total, details = calculate_order_totals(items, days)
        prepayment = total * prepayment_percent / 100
        
        return JsonResponse({
            'success': True,
            'total': round(total, 2),
            'prepayment': round(prepayment, 2),
            'remaining': round(total - prepayment, 2),
            'details': details
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error calculating total: {e}")
        return JsonResponse({'error': 'Calculation failed'}, status=500)


@csrf_exempt
@login_required
@reception_required
@transaction.atomic
@require_http_methods(["POST"])
def initiate_order_api(request):
    """
    API endpoint to create a new order
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['customer', 'items', 'start_date', 'expected_return_date']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)
        
        # Create or get customer
        customer_data = data.get('customer', {})
        if not customer_data.get('phone') or not customer_data.get('full_name'):
            return JsonResponse({
                'success': False,
                'error': 'Customer phone and name are required'
            }, status=400)
        
        customer, created = Customer.objects.get_or_create(
            phone=customer_data['phone'],
            defaults={
                'full_name': customer_data['full_name'],
                'tax_id': customer_data.get('tax_id', ''),
            }
        )
        
        # Calculate days
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        return_date = datetime.strptime(data['expected_return_date'], '%Y-%m-%d').date()
        days = max(1, (return_date - start_date).days)
        
        # Calculate totals
        total, _ = calculate_order_totals(data.get('items', []), days)
        prepayment_percent = float(data.get('prepayment_percentage', 50))
        prepayment = total * prepayment_percent / 100
        
        # Create order
        order = Order.objects.create(
            order_number=f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            customer=customer,
            created_by=request.user,
            prepayment_percentage=prepayment_percent,
            estimated_total=total,
            prepayment_amount=prepayment,
            start_date=start_date,
            expected_return_date=return_date,
            status='active'
        )
        
        # Create order items and reserve stock
        for item_data in data.get('items', []):
            product = Product.objects.get(id=item_data['product_id'])
            quantity = int(item_data['quantity'])
            
            # Reserve stock
            if not product.reserve_stock(quantity):
                raise Exception(f"Not enough stock for {product.name}")
            
            # Create order item
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_per_day=product.price_per_day,
                days_rented=days,
                subtotal=float(product.price_per_day) * quantity * days
            )
            
            # Add extras
            for extra_id in item_data.get('extras', []):
                extra = Extra.objects.get(id=extra_id)
                OrderExtra.objects.create(
                    order_item=order_item,
                    extra=extra,
                    quantity=quantity,
                    price_per_day=extra.price_per_day,
                    subtotal=float(extra.price_per_day) * quantity * days
                )
        
        # Create personnel allocations
        personnel_data = data.get('personnel_allocations', [])
        is_valid, total_percentage = validate_personnel_allocations(personnel_data)
        
        if personnel_data and not is_valid:
            raise Exception(f"Personnel allocation must total 100% (currently {total_percentage}%)")
        
        for p_data in personnel_data:
            personnel = LoadingPersonnel.objects.get(id=p_data['personnel_id'])
            PersonnelAllocation.objects.create(
                order=order,
                personnel=personnel,
                percentage=float(p_data['percentage']),
                salary_earned=0
            )
        
        logger.info(f"Order {order.order_number} created by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'message': 'Order created successfully!'
        })
        
    except Product.DoesNotExist as e:
        return JsonResponse({'success': False, 'error': f'Product not found'}, status=400)
    except LoadingPersonnel.DoesNotExist as e:
        return JsonResponse({'success': False, 'error': f'Personnel not found'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ============================================================================
# API ENDPOINTS - RETURNS
# ============================================================================

@login_required
@reception_required
def search_active_orders_api(request):
    """
    API endpoint to search for active orders
    """
    search_term = request.GET.get('q', '').strip()
    
    orders = Order.objects.filter(
        status='active'
    ).select_related('customer').order_by('-created_at')
    
    if search_term:
        orders = orders.filter(
            Q(order_number__icontains=search_term) |
            Q(customer__full_name__icontains=search_term) |
            Q(customer__phone__icontains=search_term)
        )
    
    orders = orders[:10]
    
    data = [{
        'id': order.id,
        'order_number': order.order_number,
        'customer_name': order.customer.full_name,
        'customer_phone': order.customer.phone,
        'start_date': order.start_date.strftime('%Y-%m-%d'),
        'expected_return_date': order.expected_return_date.strftime('%Y-%m-%d'),
        'prepayment_amount': float(order.prepayment_amount),
        'estimated_total': float(order.estimated_total),
    } for order in orders]
    
    return JsonResponse({'orders': data})


@login_required
@reception_required
def get_order_details_api(request, order_id):
    """
    API endpoint to get detailed order information for return
    """
    order = get_object_or_404(
        Order.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related(
            'items__product',
            'items__extras__extra',
            'personnel_allocations__personnel__user'
        ),
        id=order_id,
        status='active'
    )
    
    # Build response data
    items = []
    for item in order.items.all():
        item_data = {
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price_per_day': float(item.price_per_day),
            'days_rented': item.days_rented,
            'subtotal': float(item.subtotal),
            'extras': []
        }
        
        for extra in item.extras.all():
            item_data['extras'].append({
                'id': extra.extra.id,
                'name': extra.extra.name,
                'quantity': extra.quantity,
                'price_per_day': float(extra.price_per_day),
                'subtotal': float(extra.subtotal)
            })
        
        items.append(item_data)
    
    personnel = [{
        'id': a.id,
        'personnel_id': a.personnel.id,
        'name': a.personnel.name,
        'percentage': float(a.percentage),
        'salary_earned': float(a.salary_earned)
    } for a in order.personnel_allocations.all()]
    
    data = {
        'id': order.id,
        'order_number': order.order_number,
        'customer': {
            'id': order.customer.id,
            'full_name': order.customer.full_name,
            'phone': order.customer.phone,
            'tax_id': order.customer.tax_id or '',
        },
        'start_date': order.start_date.strftime('%Y-%m-%d'),
        'expected_return_date': order.expected_return_date.strftime('%Y-%m-%d'),
        'prepayment_percentage': float(order.prepayment_percentage),
        'prepayment_amount': float(order.prepayment_amount),
        'estimated_total': float(order.estimated_total),
        'items': items,
        'personnel': personnel,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        'created_by': order.created_by.get_full_name() or order.created_by.username,
    }
    
    return JsonResponse(data)


@csrf_exempt
@login_required
@reception_required
@transaction.atomic
@require_http_methods(["POST"])
def finalize_return_api(request):
    """
    API endpoint to finalize an order return
    """
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        actual_return_date = datetime.strptime(
            data.get('actual_return_date'), 
            '%Y-%m-%d'
        ).date()
        
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'items__product',
                'items__extras',
                'personnel_allocations'
            ),
            id=order_id,
            status='active'
        )
        
        # Calculate actual days rented
        days_rented = max(1, (actual_return_date - order.start_date).days)
        
        # Recalculate final total
        final_total = Decimal('0.00')
        
        for item in order.items.all():
            item.days_rented = days_rented
            item.subtotal = item.price_per_day * item.quantity * days_rented
            item.save()
            
            final_total += item.subtotal
            
            for extra in item.extras.all():
                extra.subtotal = extra.price_per_day * extra.quantity * days_rented
                extra.save()
                final_total += extra.subtotal
        
        # Calculate remaining amount
        remaining_amount = final_total - order.prepayment_amount
        
        # Update order
        order.actual_return_date = actual_return_date
        order.final_total = final_total
        order.remaining_amount = remaining_amount
        order.status = 'completed'
        order.save()
        
        # Calculate salaries for loading personnel
        for allocation in order.personnel_allocations.all():
            salary = (final_total * allocation.percentage) / 100
            allocation.salary_earned = salary
            allocation.save()
        
        # Confirm stock usage (remove from reserved)
        for item in order.items.all():
            item.product.confirm_rental(item.quantity)
        
        logger.info(f"Return processed for order {order.order_number} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'final_total': float(final_total),
            'remaining_amount': float(remaining_amount),
            'message': 'Return processed successfully!'
        })
        
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing return: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# API ENDPOINTS - DASHBOARD STATS
# ============================================================================

@login_required
def dashboard_stats_api(request):
    """
    API endpoint for dashboard statistics (role-based)
    """
    today = timezone.now().date()
    
    if request.user.role == 'loading':
        # Loading personnel stats
        try:
            personnel = request.user.loading_profile
            allocations = PersonnelAllocation.objects.filter(personnel=personnel)
            
            stats = {
                'active_assignments': allocations.filter(order__status='active').count(),
                'completed_assignments': allocations.filter(order__status='completed').count(),
                'total_earned': float(allocations.filter(
                    order__status='completed'
                ).aggregate(Sum('salary_earned'))['salary_earned__sum'] or 0),
            }
        except LoadingPersonnel.DoesNotExist:
            stats = {
                'active_assignments': 0,
                'completed_assignments': 0,
                'total_earned': 0,
            }
    
    elif request.user.role == 'reception':
        # Reception stats
        stats = {
            'orders_today': Order.objects.filter(
                created_by=request.user,
                created_at__date=today
            ).count(),
            'returns_today': Order.objects.filter(
                status='completed',
                actual_return_date=today
            ).count(),
            'active_orders': Order.objects.filter(status='active').count(),
        }
    
    else:
        # Admin stats
        stats = {
            'total_orders': Order.objects.count(),
            'active_orders': Order.objects.filter(status='active').count(),
            'completed_orders': Order.objects.filter(status='completed').count(),
            'revenue_today': float(Order.objects.filter(
                status='completed',
                created_at__date=today
            ).aggregate(Sum('final_total'))['final_total__sum'] or 0),
        }
    
    return JsonResponse(stats)
@login_required
@loading_personnel_required
@require_http_methods(["POST"])
def confirm_loading_api(request, allocation_id):
    """
    API endpoint for loading personnel to confirm loading
    """
    try:
        allocation = get_object_or_404(
            PersonnelAllocation.objects.select_related('order', 'personnel__user'),
            id=allocation_id
        )
        
        if allocation.personnel.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Unauthorized'
            }, status=403)
        
        if allocation.order.status != 'active':
            return JsonResponse({
                'success': False,
                'error': 'This order is no longer active'
            }, status=400)
        
        # Here you could add logic to mark as confirmed
        # For now, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Loading confirmed successfully!',
            'order_number': allocation.order.order_number,
            'estimated_salary': float(allocation.order.estimated_total * allocation.percentage / 100)
        })
        
    except PersonnelAllocation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Allocation not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error confirming loading: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)