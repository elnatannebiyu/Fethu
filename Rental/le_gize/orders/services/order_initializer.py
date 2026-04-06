from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.utils import timezone

from personnel.models import LoadingPersonnel
from products.models import Extra, Product
from orders.models import (
    Customer,
    Order,
    OrderExtra,
    OrderItem,
    PersonnelAllocation,
    COMMISSION_RATE,
)
from orders.utils import calculate_order_totals, quantize_currency


class OrderInitializationError(Exception):
    pass


def _format_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        raise OrderInitializationError("Invalid numeric value provided.")


def _validate_personnel_allocations(personnel_data: List[Dict[str, Any]]) -> Decimal:
    total = Decimal('0')
    for entry in personnel_data:
        percentage_raw = entry.get('percentage')
        if percentage_raw is None:
            raise OrderInitializationError("Each personnel allocation needs a percentage.")
        percentage = _format_decimal(percentage_raw)
        if percentage <= 0:
            raise OrderInitializationError("Personnel allocations must be greater than zero.")
        total += percentage
    if total <= 0:
        raise OrderInitializationError("At least one personnel allocation must be greater than zero.")
    return total


def _parse_dates(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        start_date = timezone.datetime.strptime(payload['start_date'], '%Y-%m-%d').date()
        expected_return_date = timezone.datetime.strptime(payload['expected_return_date'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        raise OrderInitializationError("Start and expected return dates are required and must use YYYY-MM-DD format.")
    if expected_return_date <= start_date:
        raise OrderInitializationError("Expected return date must be after the start date.")
    return {'start_date': start_date, 'expected_return_date': expected_return_date}


def _ensure_customer(payload: Dict[str, Any]) -> Customer:
    customer_data = payload.get('customer') or {}
    if not customer_data.get('phone') or not customer_data.get('full_name'):
        raise OrderInitializationError('Customer phone and full name are required.')
    customer, _ = Customer.objects.get_or_create(
        phone=customer_data['phone'],
        defaults={
            'full_name': customer_data['full_name'],
            'tax_id': customer_data.get('tax_id', ''),
        }
    )
    return customer


def _build_items(payload_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not payload_items:
        raise OrderInitializationError('At least one product is required to create an order.')
    return payload_items


def _calculate_prepayment(total: Decimal, percent: Decimal, amount: Optional[Decimal]) -> Dict[str, Decimal]:
    if amount is None or amount <= 0:
        amount = quantize_currency(total * percent / Decimal('100'))
    else:
        if amount > total:
            amount = total
        amount = quantize_currency(amount)
        percent = (amount / total * Decimal('100')) if total > 0 else Decimal('0')
    percent = max(Decimal('0'), min(percent, Decimal('100')))
    return {'amount': amount, 'percent': percent}


def _notify_stakeholders(order: Order) -> None:
    """
    Placeholder for notification logic (email/SMS) that can be expanded later.
    """
    # TODO: Hook into actual notification services (email, SMS, push).
    pass


@dataclass
class OrderCreationResult:
    order: Order
    prepayment_percent: Decimal


class OrderInitializationService:
    @classmethod
    def create_order(cls, user, payload: Dict[str, Any]) -> OrderCreationResult:
        date_data = _parse_dates(payload)
        customer = _ensure_customer(payload)
        items = _build_items(payload.get('items', []))
        personnel_data = payload.get('personnel_allocations', [])
        total_weight = _validate_personnel_allocations(personnel_data) if personnel_data else Decimal('0')

        days = max(1, (date_data['expected_return_date'] - date_data['start_date']).days)
        total, _ = calculate_order_totals(items, days)

        percent = Decimal(str(payload.get('prepayment_percent', '0'))) if payload.get('prepayment_percent') not in [None, ''] else Decimal('0')
        amount_raw = payload.get('prepayment_amount')
        amount = _format_decimal(amount_raw) if amount_raw not in [None, ''] else None
        prepayment = _calculate_prepayment(total, percent, amount)

        commission_pool = quantize_currency(total * COMMISSION_RATE)
        prepayment_commission = quantize_currency(commission_pool * (prepayment['amount'] / total)) if total > 0 else Decimal('0')

        with transaction.atomic():
            order = Order.objects.create(
                order_number=f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                customer=customer,
                created_by=user,
                prepayment_percentage=prepayment['percent'],
                estimated_total=total,
                prepayment_amount=prepayment['amount'],
                penalty_amount=Decimal('0.00'),
                penalty_days=0,
                start_date=date_data['start_date'],
                expected_return_date=date_data['expected_return_date'],
                status='active',
            )

            for item_data in items:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = int(item_data['quantity'])
                row_days = max(1, int(item_data.get('days', days)))

                if not product.reserve_stock(quantity):
                    raise OrderInitializationError(f"Not enough stock for {product.name}.")

                item_subtotal = quantize_currency(product.price_per_day * Decimal(quantity) * Decimal(row_days))
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_per_day=product.price_per_day,
                    days_rented=row_days,
                    subtotal=item_subtotal,
                )

                for extra_id in item_data.get('extras', []):
                    extra = Extra.objects.get(id=extra_id)
                    extra_daily_total = quantize_currency(extra.price_per_day * Decimal(quantity) * Decimal(row_days))
                    extra_one_time_total = quantize_currency(extra.one_time_fee * Decimal(quantity))
                    OrderExtra.objects.create(
                        order_item=order_item,
                        extra=extra,
                        quantity=quantity,
                        price_per_day=extra.price_per_day,
                        one_time_fee=extra.one_time_fee,
                        subtotal=extra_daily_total + extra_one_time_total,
                    )

            if personnel_data:
                if total_weight <= 0:
                    raise OrderInitializationError("Personnel allocation weights must sum to more than zero.")

                for p_data in personnel_data:
                    personnel = LoadingPersonnel.objects.get(id=p_data['personnel_id'])
                    weight = _format_decimal(p_data['percentage'])
                    allocation_commission = quantize_currency(prepayment_commission * (weight / total_weight)) if total_weight > 0 else Decimal('0')
                    PersonnelAllocation.objects.create(
                        order=order,
                        personnel=personnel,
                        percentage=weight,
                        salary_earned=Decimal('0.00'),
                        commission_paid=allocation_commission,
                    )

            _notify_stakeholders(order)

        return OrderCreationResult(order=order, prepayment_percent=prepayment['percent'])
