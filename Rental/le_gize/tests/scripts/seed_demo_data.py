"""
Seed demo data for the Le Gize rental system.

Usage:
    source .venv/bin/activate
    python manage.py shell < tests/seed_demo_data.py

This script is idempotent – you can run it multiple times and it will keep
records in sync rather than duplicating them.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from accounts.models import User
from orders.models import Customer, Order, OrderItem, OrderExtra, PersonnelAllocation
from personnel.models import LoadingPersonnel
from products.models import Category, Extra, Product


logger = logging.getLogger("seed_demo_data")


def ensure_superadmin():
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created or not admin_user.is_superuser:
        admin_user.set_password("12345")
        admin_user.role = "admin"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        logger.info("Superadmin 'admin' created/updated with default password.")
    else:
        logger.info("Superadmin 'admin' already present.")
    return admin_user


def ensure_loading_personnel():
    loader_user, created = User.objects.get_or_create(
        username="loader1",
        defaults={
            "email": "loader1@example.com",
            "role": "loading",
            "is_staff": True,
        },
    )
    if created or not loader_user.check_password("loaderpass"):
        loader_user.set_password("loaderpass")
        loader_user.save()
        logger.info("Loader user 'loader1' created/updated with default password.")

    personnel, created = LoadingPersonnel.objects.get_or_create(
        user=loader_user,
        defaults={
            "commission_rate": Decimal("10.00"),
            "is_active": True,
        },
    )
    if created:
        logger.info("Loading personnel %s created and linked to user loader1.", personnel.employee_id)
    else:
        logger.info("Loading personnel %s already exists for user loader1.", personnel.employee_id)
    return personnel


def ensure_reception_user():
    reception_user, _ = User.objects.get_or_create(
        username="reception1",
        defaults={
            "email": "reception@example.com",
            "role": "reception",
            "is_staff": True,
        },
    )
    if not reception_user.check_password("receptionpass"):
        reception_user.set_password("receptionpass")
        reception_user.save()
        logger.info("Reception user password reset to default.")
    logger.info("Reception staff user 'reception1' ready.")
    return reception_user


def seed_inventory():
    category, _ = Category.objects.get_or_create(
        name="Lighting",
        defaults={"description": "Indoor & outdoor lighting equipment"},
    )
    extra, _ = Extra.objects.get_or_create(
        name="Delivery Service",
        defaults={
            "description": "Delivery within city limits",
            "price_per_day": Decimal("50.00"),
        },
    )
    product, _ = Product.objects.get_or_create(
        name="LED Flood Light",
        defaults={
            "description": "High-power LED lights",
            "category": category,
            "price_per_day": Decimal("120.00"),
            "total_stock": 20,
            "available_stock": 20,
            "reserved_stock": 0,
            "is_active": True,
        },
    )
    if product.category != category:
        product.category = category
        product.save()

    product.extras.add(extra)
    logger.info("Inventory ready: category '%s', product '%s', extra '%s'.", category.name, product.name, extra.name)
    return product, extra


def seed_customer():
    customer, _ = Customer.objects.get_or_create(
        full_name="John Doe",
        defaults={"phone": "555-0100", "tax_id": "JD-1001"},
    )
    logger.info("Customer '%s' ready with phone %s.", customer.full_name, customer.phone)
    return customer


def seed_order(admin_user, product, extra, customer, personnel):
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=3)

    order, _ = Order.objects.get_or_create(
        order_number="ORD-1001",
        defaults={
            "customer": customer,
            "created_by": admin_user,
            "prepayment_percentage": Decimal("50.00"),
            "estimated_total": Decimal("1800.00"),
            "prepayment_amount": Decimal("900.00"),
            "start_date": start_date,
            "expected_return_date": end_date,
            "status": "active",
        },
    )

    OrderItem.objects.update_or_create(
        order=order,
        product=product,
        defaults={
            "quantity": 5,
            "price_per_day": product.price_per_day,
            "days_rented": 3,
            "subtotal": Decimal("1800.00"),
        },
    )
    order_item = OrderItem.objects.get(order=order, product=product)

    OrderExtra.objects.update_or_create(
        order_item=order_item,
        extra=extra,
        defaults={
            "quantity": 1,
            "price_per_day": extra.price_per_day,
            "subtotal": extra.price_per_day,
        },
    )

    PersonnelAllocation.objects.update_or_create(
        order=order,
        personnel=personnel,
        defaults={
            "percentage": Decimal("100.00"),
            "salary_earned": Decimal("180.00"),
            "commission_paid": Decimal("90.00"),
        },
    )
    logger.info("Order %s populated with items, extras, and personnel allocations.", order.order_number)
    return order


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    admin_user = ensure_superadmin()
    personnel = ensure_loading_personnel()
    ensure_reception_user()
    product, extra = seed_inventory()
    customer = seed_customer()
    order = seed_order(admin_user, product, extra, customer, personnel)

    print("Seed data ready:")
    print(f"- Admin: {admin_user.username}")
    print(f"- Product: {product.name}")
    print(f"- Customer: {customer.full_name}")
    print(f"- Order: {order.order_number}")
    print("Use reception1/receptionpass or loader1/loaderpass to test role guards.")


main()
