"""
Script to seed sample orders for testing
Run with: python manage.py shell < tests/scripts/seed_orders.py
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from accounts.models import User
from orders.models import Order, OrderItem, Customer
from products.models import Product

# Get or create reception1 user
reception_user = User.objects.filter(username='reception1').first()
if not reception_user:
    print("❌ reception1 user not found. Please create it first.")
    exit()

print(f"✓ Found reception1 user: {reception_user.get_full_name()}")

# Get active products
products = Product.objects.filter(is_active=True, available_stock__gt=0)
if not products.exists():
    print("❌ No active products found. Please create products first.")
    exit()

print(f"✓ Found {products.count()} active products")

# Create sample customers
customers_data = [
    {'full_name': 'Ahmed Hassan', 'phone': '+251911234567', 'tax_id': 'TAX001'},
    {'full_name': 'Fatima Mohamed', 'phone': '+251922345678', 'tax_id': 'TAX002'},
    {'full_name': 'Yohannes Tekle', 'phone': '+251933456789', 'tax_id': 'TAX003'},
    {'full_name': 'Marta Abebe', 'phone': '+251944567890', 'tax_id': 'TAX004'},
    {'full_name': 'Dawit Assefa', 'phone': '+251955678901', 'tax_id': 'TAX005'},
]

customers = []
for cust_data in customers_data:
    customer, created = Customer.objects.get_or_create(
        full_name=cust_data['full_name'],
        phone=cust_data['phone'],
        defaults={'tax_id': cust_data['tax_id']}
    )
    customers.append(customer)
    status = "Created" if created else "Exists"
    print(f"  {status}: {customer.full_name}")

print(f"✓ {len(customers)} customers ready")

# Create sample orders
orders_created = 0
today = timezone.now().date()

order_statuses = ['active', 'completed', 'cancelled']
status_idx = 0

for i, customer in enumerate(customers):
    # Create 2-3 orders per customer
    num_orders = 2 + (i % 2)
    
    for j in range(num_orders):
        # Vary the dates
        days_ago = (i * 3) + (j * 2)
        order_date = today - timedelta(days=days_ago)
        start_date = order_date
        expected_return_date = start_date + timedelta(days=7)
        
        # Generate unique order number
        order_number = f"ORD-{today.strftime('%Y%m%d')}-{status_idx:04d}"
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            customer=customer,
            created_by=reception_user,
            status=order_statuses[status_idx % len(order_statuses)],
            prepayment_percentage=Decimal('50.00'),
            estimated_total=Decimal('0.00'),
            final_total=Decimal('0.00'),
            prepayment_amount=Decimal('0.00'),
            start_date=start_date,
            expected_return_date=expected_return_date,
            created_at=timezone.make_aware(
                datetime.combine(order_date, datetime.min.time())
            )
        )
        status_idx += 1
        
        # Add items to order
        num_items = 1 + (j % 3)
        total = Decimal('0.00')
        
        for k in range(num_items):
            product = products[k % products.count()]
            quantity = 1 + (k % 3)
            days_rented = 7
            item_total = Decimal(str(product.price_per_day)) * quantity * days_rented
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                days_rented=days_rented,
                price_per_day=product.price_per_day,
                subtotal=item_total
            )
            total += item_total
        
        # Update order totals
        order.estimated_total = total
        order.final_total = total
        order.prepayment_amount = total * Decimal('0.5')  # 50% prepayment
        order.save()
        
        orders_created += 1
        print(f"  Created order #{order.order_number} - {customer.full_name} - Status: {order.status}")

print(f"\n✅ Successfully created {orders_created} sample orders for reception1 user!")
print(f"   Orders are ready to view at: /orders/list/")
