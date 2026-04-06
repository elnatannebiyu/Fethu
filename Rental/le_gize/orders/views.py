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
from core.utils import apply_search_filters
from products.models import Product, Extra
from personnel.models import LoadingPersonnel
from orders.models import PersonnelAllocation, Order, OrderItem, OrderExtra, Customer, COMMISSION_RATE
from orders.utils import calculate_order_totals, quantize_currency

logger = logging.getLogger(__name__)
COMMISSION_RATE = Decimal('0.10')
CUSTOM_LATE_PENALTY_PERCENT = Decimal('12.5')
CURRENCY_QUANTIZE = Decimal('0.01')

ORDER_STATUS_CHOICES = [
    ('active', 'Active'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


def calculate_order_totals(items, default_days):
    """Sum up product + extras totals over the requested rental days."""
    default_days = max(1, int(default_days))

    total = Decimal('0.00')
    details = []
    for item in items:
        product_id = item.get('product_id')
        if not product_id:
            raise ValueError('Product ID is required for each item.')

        product = Product.objects.get(id=product_id)
        quantity = Decimal(str(item.get('quantity', 0)))
        if quantity <= 0:
            raise ValueError(f'Quantity must be greater than zero for {product.name}.')

        item_days = item.get('days')
        try:
            item_days = max(1, int(item_days))
        except (TypeError, ValueError):
            item_days = default_days

        days_decimal = Decimal(item_days)
        base_total = product.price_per_day * quantity * days_decimal
        extras_details = []
        extras_total = Decimal('0.00')
        extras_one_time_total = Decimal('0.00')

        for extra_id in item.get('extras', []):
            extra = Extra.objects.get(id=extra_id)
            extra_amount = quantize_currency(extra.price_per_day * quantity * days_decimal)
            extras_total += extra_amount
            one_time_amount = quantize_currency(extra.one_time_fee * quantity)
            extras_one_time_total += one_time_amount
            extras_details.append({
                'id': extra.id,
                'name': extra.name,
                'price_per_day': float(extra.price_per_day),
                'subtotal': float(extra_amount),
                'one_time_fee': float(extra.one_time_fee),
                'one_time_total': float(one_time_amount),
                'days': item_days
            })

        subtotal = quantize_currency(base_total + extras_total + extras_one_time_total)
        total += subtotal

        details.append({
            'product_id': product.id,
            'name': product.name,
            'quantity': int(quantity),
            'days': item_days,
            'price_per_day': float(product.price_per_day),
            'start_date': item.get('start_date'),
            'expected_return_date': item.get('expected_return_date'),
            'subtotal': float(subtotal),
            'extras': extras_details,
            'extras_one_time_total': float(extras_one_time_total),
            'extras_total': float(extras_total)
        })

    return quantize_currency(total), details

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_role_based_orders(user):
    if user.role == 'loading':
        return Order.objects.filter(personnelallocation_set__personnel__user=user)
    elif user.role == 'reception':
        return Order.objects.filter(created_by=user)
    elif user.role == 'admin' or user.is_superuser:
        return Order.objects.all()
    return Order.objects.none()

def get_allocation_for_request(request, allocation_id):
    """Fetch allocation and ensure the current user can act on it."""
    allocation = get_object_or_404(
        PersonnelAllocation.objects.select_related('personnel__user', 'order'),
        id=allocation_id
    )

    if allocation.personnel.user != request.user and not request.user.is_superuser:
        return None, "You don't have permission to confirm this assignment."

    return allocation, None

def validate_allocation_request(request, allocation_id):
    """Shared helper used by template and API confirm views."""
    allocation, error = get_allocation_for_request(request, allocation_id)
    if error:
        return None, error
    if allocation.order.status != 'active':
        return None, "This order is no longer active."
    return allocation, None

@login_required
@reception_required
def order_page(request):
    """Main order creation page (reception and admin only)"""
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    default_rental_days = (next_week - today).days

    products = list(Product.objects.filter(
        is_active=True,
        available_stock__gt=0
    ).select_related('category').prefetch_related('extras'))
    for product in products:
        product.extras_json = json.dumps([
            {
                'id': extra.id,
                'name': extra.name,
                'price_per_day': float(extra.price_per_day),
                'one_time_fee': float(extra.one_time_fee),
            }
            for extra in product.extras.all()
        ])

    context = {
        'products': products,
        'personnel': LoadingPersonnel.objects.filter(
            is_active=True
        ).select_related('user'),
        'today': today,
        'next_week': next_week,
        'default_rental_days': default_rental_days,
        'status_choices': ORDER_STATUS_CHOICES,
    }
    return render(request, 'orders/order_page.html', context)

@login_required
def order_list(request):
    """
    List all orders with filters (role-based access)
    """
    from django.core.paginator import Paginator
    
    orders = get_role_based_orders(request.user).select_related(
        'customer', 'created_by'
    ).prefetch_related(
        'items', 'personnelallocation_set__personnel__user'
    )
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    search = request.GET.get('search', '')
    orders = apply_search_filters(orders, search, [
        'order_number', 'customer__full_name', 'customer__phone'
    ])
    
    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'order_number':
        orders = orders.order_by('order_number')
    elif sort_by == 'order_number_reverse':
        orders = orders.order_by('-order_number')
    elif sort_by == 'newest':
        orders = orders.order_by('-created_at')
    elif sort_by == 'oldest':
        orders = orders.order_by('created_at')
    elif sort_by == 'total_high':
        orders = orders.order_by('-estimated_total')
    elif sort_by == 'total_low':
        orders = orders.order_by('estimated_total')
    else:
        orders = orders.order_by('-created_at')
    
    # Annotate with item count
    orders = orders.annotate(item_count=Count('items'))
    
    # Pagination
    paginator = Paginator(orders, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'status_choices': ORDER_STATUS_CHOICES,
        'current_status': status,
        'search_query': search or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'sort_by': sort_by,
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
            'personnelallocation_set__personnel__user'
        ),
        id=order_id
    )
    
    # Permission check
    if request.user.role == 'loading':
        if not order.personnelallocation_set.filter(
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
    """Confirm loading assignment (HTML flow)."""
    allocation, error = validate_allocation_request(request, allocation_id)
    if error:
        messages.error(request, error)
        return redirect('orders:assigned_orders')

    messages.success(request, f"Loading confirmed for Order {allocation.order.order_number}!")
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
            'price_per_day': float(e.price_per_day),
            'one_time_fee': float(e.one_time_fee)
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
        days = max(1, int(data.get('days', 1)))
        start_date_str = data.get('start_date')
        return_date_str = data.get('expected_return_date')
        if start_date_str and return_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
                parsed_days = max(1, (return_date - start_date).days)
                days = parsed_days
            except ValueError:
                logger.warning("Invalid date format received for rental total calculation")
        prepayment_percent = Decimal(str(data.get('prepayment_percent', 50)))
        prepayment_percent = max(Decimal('0'), min(prepayment_percent, Decimal('100')))
        late_days = max(0, int(data.get('late_days', 0)))
        penalty_percent = Decimal(str(data.get('penalty_percent', CUSTOM_LATE_PENALTY_PERCENT)))
        penalty_percent = max(Decimal('0'), min(penalty_percent, Decimal('100')))

        total, details = calculate_order_totals(items, days)
        prepayment_amount_raw = data.get('prepayment_amount')
        prepayment_amount = None
        if prepayment_amount_raw not in [None, '']:
            prepayment_amount = Decimal(str(prepayment_amount_raw))
        if prepayment_amount is None or prepayment_amount <= 0:
            prepayment_amount = quantize_currency(total * prepayment_percent / Decimal('100'))
        else:
            if prepayment_amount > total:
                prepayment_amount = total
            prepayment_amount = quantize_currency(prepayment_amount)
        prepayment = prepayment_amount

        collateral_amount_raw = data.get('collateral_amount')
        collateral_amount = Decimal('0.00')
        if collateral_amount_raw not in [None, '']:
            try:
                collateral_amount = Decimal(str(collateral_amount_raw))
            except (ValueError, TypeError):
                collateral_amount = Decimal('0.00')
        collateral_amount = max(Decimal('0.00'), collateral_amount)
        penalty_amount = Decimal('0.00')
        if late_days > 0 and total > 0:
            penalty_amount = quantize_currency(
                total * penalty_percent / Decimal('100') * Decimal(late_days)
            )
        total_with_penalty = quantize_currency(total + penalty_amount)
        if total_with_penalty > 0:
            prepayment_percent = min(Decimal('100'), (prepayment / total_with_penalty) * Decimal('100'))
        else:
            prepayment_percent = Decimal('0')
        remaining_amount = quantize_currency(total_with_penalty - prepayment)
        client_payment = quantize_currency(prepayment + remaining_amount + collateral_amount)
        collateral_percent = Decimal('0.00')
        if total_with_penalty > 0:
            collateral_percent = min(Decimal('100'), (collateral_amount / total_with_penalty) * Decimal('100'))

        def _to_float(value):
            return float(round(value, 2))

        return JsonResponse({
            'success': True,
            'total': _to_float(total_with_penalty),
            'subtotal': _to_float(total),
            'prepayment': _to_float(prepayment),
            'remaining': _to_float(remaining_amount),
            'prepayment_percent': float(prepayment_percent),
            'rental_days': days,
            'penalty_amount': _to_float(penalty_amount),
            'penalty_days': late_days,
            'penalty_percent': float(penalty_percent),
            'collateral_amount': _to_float(collateral_amount),
            'collateral_percent': float(collateral_percent),
            'client_payment': _to_float(client_payment),
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
@csrf_exempt
@login_required
@reception_required
@require_http_methods(["POST"])
def initiate_order_api(request):
    try:
        data = json.loads(request.body)
        result = OrderInitializationService.create_order(request.user, data)
        logger.info(f"Order {result.order.order_number} created by {request.user.username}")
        return JsonResponse({
            'success': True,
            'order_id': result.order.id,
            'order_number': result.order.order_number,
            'message': 'Order created successfully!'
        })
    except OrderInitializationError as exc:
        logger.error(f"Order initialization failed: {exc}")
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
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
    
    orders = apply_search_filters(orders, search_term, [
        'order_number', 'customer__full_name', 'customer__phone'
    ])
    
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
       
        late_days = max(0, (actual_return_date - order.expected_return_date).days)
        penalty_amount = Decimal('0.00')
        if late_days > 0:
            penalty_amount = quantize_currency(
                final_total * CUSTOM_LATE_PENALTY_PERCENT / Decimal('100') * Decimal(late_days)
            )
            final_total += penalty_amount

        # Calculate remaining amount
        remaining_amount = final_total - order.prepayment_amount
       
        # Update order
        order.actual_return_date = actual_return_date
        order.final_total = final_total
        order.penalty_amount = penalty_amount
        order.penalty_days = late_days
        order.remaining_amount = remaining_amount
        order.status = 'completed'
        order.save()
        
        # Calculate salaries for loading personnel
        commission_pool = quantize_currency(final_total * COMMISSION_RATE)
        allocations = list(order.personnel_allocations.all())
        total_weight = sum((allocation.percentage or Decimal('0')) for allocation in allocations)
        for allocation in allocations:
            weight = allocation.percentage or Decimal('0')
            share = (weight / total_weight) if total_weight > 0 else Decimal('0')
            commission_total = quantize_currency(commission_pool * share)
            allocation.salary_earned = commission_total
            paid_so_far = allocation.commission_paid or Decimal('0')
            if paid_so_far < commission_total:
                allocation.commission_paid = commission_total
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
    """API endpoint for loading personnel to confirm loading."""
    allocation, error = validate_allocation_request(request, allocation_id)
    if error:
        status = 403 if "permission" in error.lower() else 400
        return JsonResponse({'success': False, 'message': error}, status=status)

    return JsonResponse({'success': True, 'message': 'Loading confirmed successfully.'})
