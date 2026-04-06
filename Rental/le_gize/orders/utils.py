from datetime import datetime
from decimal import Decimal

from products.models import Product, Extra

CURRENCY_QUANTIZE = Decimal('0.01')
DATE_FORMAT = '%Y-%m-%d'


def quantize_currency(value):
    if value is None:
        return Decimal('0.00')
    return Decimal(value).quantize(CURRENCY_QUANTIZE)


def _calculate_days_from_dates(item, default_days):
    start = item.get('start_date')
    end = item.get('expected_return_date')
    if not start or not end:
        return max(1, int(default_days))
    try:
        start_dt = datetime.strptime(start, DATE_FORMAT).date()
        end_dt = datetime.strptime(end, DATE_FORMAT).date()
        days = (end_dt - start_dt).days
        return max(1, days) if days else 1
    except (ValueError, TypeError):
        return max(1, int(default_days))


def calculate_order_totals(items, default_days):
    from django.core.exceptions import ObjectDoesNotExist

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

        item_days = _calculate_days_from_dates(item, default_days)
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
                'one_time_fee': float(extra.one_time_fee),
                'subtotal': float(extra_amount),
                'one_time_total': float(one_time_amount),
            })

        subtotal = quantize_currency(base_total + extras_total + extras_one_time_total)
        total += subtotal

        details.append({
            'product_id': product.id,
            'name': product.name,
            'quantity': int(quantity),
            'days': item_days,
            'price_per_day': float(product.price_per_day),
            'subtotal': float(subtotal),
            'extras': extras_details,
            'extras_one_time_total': float(extras_one_time_total),
            'extras_total': float(extras_total),
            'start_date': item.get('start_date') or '',
            'expected_return_date': item.get('expected_return_date') or '',
        })

    return quantize_currency(total), details
