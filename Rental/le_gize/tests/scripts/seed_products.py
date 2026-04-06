"""
Seed products for the Le Gize rental system.

Usage:
    source .venv/bin/activate
    python manage.py shell < tests/scripts/seed_products.py

This script is idempotent – you can run it multiple times and it will keep
product records in sync rather than duplicating them.
"""

import logging
from decimal import Decimal
from random import randint

from django.db.models import Q

from products.models import Category, Extra, Product

logger = logging.getLogger("seed_products")


def get_or_create_category(name):
    """Helper to safely get or create a category."""
    try:
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={"description": f"Rental equipment in the {name} category"}
        )
        if created:
            logger.info(f"Category '{name}' created.")
        else:
            logger.info(f"Category '{name}' already exists.")
        return category
    except Exception as e:
        logger.error(f"Error creating/fetching category {name}: {e}")
        raise


def seed_extras():
    """Create common extras that can be attached to products."""
    extras_data = [
        ("Delivery Service", "Standard delivery within city limits", Decimal("50.00")),
        ("Installation Service", "Professional setup and installation", Decimal("100.00")),
        ("Extended Warranty", "Additional protection coverage for 30 days", Decimal("25.00")),
        ("On-site Technician", "Dedicated technician during rental period", Decimal("75.00")),
        ("Backup Equipment", "Replacement equipment available if needed", Decimal("30.00")),
    ]
    
    created_count = 0
    
    for name, desc, price in extras_data:
        extra, created = Extra.objects.get_or_create(
            name=name,
            defaults={
                "description": desc,
                "price_per_day": price
            }
        )
        if created:
            logger.info(f"Extra '{name}' created.")
            created_count += 1
    
    print(f"\n✓ Created {created_count} new extras")
    return Extra.objects.all()


def seed_products(extras):
    """Create products across all categories with realistic data."""
    
    product_data = [
        # Lighting & Electrical
        {"name": "LED Flood Light 1000W", "category": "Lighting & Electrical", "price": Decimal("120.00"), "stock": 25, "extras": ["Delivery Service"]},
        {"name": "PAR Can Light 575W", "category": "Lighting & Electrical", "price": Decimal("85.00"), "stock": 30, "extras": []},
        {"name": "Stage Lighting Controller", "category": "Lighting & Electrical", "price": Decimal("45.00"), "stock": 15, "extras": ["Installation Service"]},
        
        # Sound Systems
        {"name": "PA Speaker System 12\"", "category": "Sound Systems", "price": Decimal("65.00"), "stock": 40, "extras": ["Delivery Service"]},
        {"name": "Wireless Microphone Set", "category": "Sound Systems", "price": Decimal("35.00"), "stock": 20, "extras": []},
        {"name": "Audio Mixer Console 16-Channel", "category": "Sound Systems", "price": Decimal("95.00"), "stock": 10, "extras": ["Installation Service"]},
        
        # Staging & Platforms
        {"name": "Modular Stage Platform 4x8ft", "category": "Staging & Platforms", "price": Decimal("200.00"), "stock": 15, "extras": []},
        {"name": "Aluminum Truss System 10ft", "category": "Staging & Platforms", "price": Decimal("180.00"), "stock": 12, "extras": ["Installation Service"]},
        
        # Seating & Furniture
        {"name": "Folding Chair (Standard)", "category": "Seating & Furniture", "price": Decimal("5.00"), "stock": 200, "extras": []},
        {"name": "Round Table 6ft Diameter", "category": "Seating & Furniture", "price": Decimal("45.00"), "stock": 30, "extras": ["Delivery Service"]},
        
        # Climate Control
        {"name": "Portable Air Conditioner 12000BTU", "category": "Climate Control", "price": Decimal("75.00"), "stock": 18, "extras": []},
        {"name": "Industrial Floor Fan", "category": "Climate Control", "price": Decimal("35.00"), "stock": 25, "extras": []},
        
        # Projection & Video
        {"name": "HD Projector 4000 Lumens", "category": "Projection & Video", "price": Decimal("150.00"), "stock": 12, "extras": ["Installation Service"]},
        {"name": "LED Display Wall 3x2m", "category": "Projection & Video", "price": Decimal("800.00"), "stock": 5, "extras": ["On-site Technician"]},
        
        # Power Distribution
        {"name": "Generator 10kW Diesel", "category": "Power Distribution", "price": Decimal("250.00"), "stock": 8, "extras": []},
        {"name": "Power Strip 20 Outlet", "category": "Power Distribution", "price": Decimal("45.00"), "stock": 35, "extras": ["Delivery Service"]},
        
        # Safety & Security
        {"name": "Fire Extinguisher ABC Type", "category": "Safety & Security", "price": Decimal("25.00"), "stock": 50, "extras": []},
        {"name": "Event Barrier System", "category": "Safety & Security", "price": Decimal("35.00"), "stock": 40, "extras": ["Installation Service"]},
        
        # Decor & Drapery
        {"name": "Velvet Backdrop Red 20ft", "category": "Decor & Drapery", "price": Decimal("85.00"), "stock": 15, "extras": []},
        {"name": "Pipe and Drape System", "category": "Decor & Drapery", "price": Decimal("65.00"), "stock": 20, "extras": ["Installation Service"]},
        
        # Tools & Equipment
        {"name": "Power Drill Set Professional", "category": "Tools & Equipment", "price": Decimal("45.00"), "stock": 30, "extras": []},
        {"name": "Extension Ladder 24ft", "category": "Tools & Equipment", "price": Decimal("65.00"), "stock": 18, "extras": ["Delivery Service"]},
        
        # Medical & First Aid
        {"name": "First Aid Kit Large", "category": "Medical & First Aid", "price": Decimal("35.00"), "stock": 25, "extras": []},
        {"name": "Portable Defibrillator (AED)", "category": "Medical & First Aid", "price": Decimal("150.00"), "stock": 8, "extras": ["Extended Warranty"]},
        
        # Cleaning Supplies
        {"name": "Floor Buffer Machine", "category": "Cleaning Supplies", "price": Decimal("95.00"), "stock": 12, "extras": []},
        {"name": "Commercial Vacuum Cleaner", "category": "Cleaning Supplies", "price": Decimal("75.00"), "stock": 18, "extras": ["Delivery Service"]},
        
        # Office & IT Equipment
        {"name": "Laptop Computer i5/8GB", "category": "Office & IT Equipment", "price": Decimal("55.00"), "stock": 20, "extras": []},
        {"name": "Network Switch 24-Port", "category": "Office & IT Equipment", "price": Decimal("120.00"), "stock": 10, "extras": ["Installation Service"]},
        
        # Transportation & Lifting
        {"name": "Forklift Electric 5000lbs", "category": "Transportation & Lifting", "price": Decimal("450.00"), "stock": 6, "extras": []},
        {"name": "Pallet Jack Manual 5500lbs", "category": "Transportation & Lifting", "price": Decimal("85.00"), "stock": 15, "extras": ["Delivery Service"]},
        
        # Communication Systems
        {"name": "Two-Way Radio Set (10-pack)", "category": "Communication Systems", "price": Decimal("250.00"), "stock": 10, "extras": []},
        {"name": "PA System with Microphone", "category": "Communication Systems", "price": Decimal("350.00"), "stock": 8, "extras": ["Installation Service"]},
        
        # Photography & Video
        {"name": "DSLR Camera Professional Kit", "category": "Photography & Video", "price": Decimal("125.00"), "stock": 15, "extras": []},
        {"name": "Video Tripod Heavy Duty", "category": "Photography & Video", "price": Decimal("65.00"), "stock": 25, "extras": []},
        
        # Outdoor & Camping
        {"name": "Event Tent 10x20ft", "category": "Outdoor & Camping", "price": Decimal("350.00"), "stock": 10, "extras": ["Installation Service"]},
        {"name": "Camping Table Aluminum", "category": "Outdoor & Camping", "price": Decimal("45.00"), "stock": 30, "extras": []},
        
        # Special Effects
        {"name": "Smoke Machine Professional", "category": "Special Effects", "price": Decimal("180.00"), "stock": 12, "extras": []},
        {"name": "Confetti Cannon (Large)", "category": "Special Effects", "price": Decimal("95.00"), "stock": 18, "extras": []},
        
        # Storage & Organization
        {"name": "Storage Container 20ft", "category": "Storage & Organization", "price": Decimal("450.00"), "stock": 5, "extras": ["Delivery Service"]},
        {"name": "Industrial Shelving Unit", "category": "Storage & Organization", "price": Decimal("180.00"), "stock": 12, "extras": []},
        
        # Miscellaneous Equipment
        {"name": "Extension Cord 100ft Heavy Duty", "category": "Miscellaneous Equipment", "price": Decimal("55.00"), "stock": 40, "extras": []},
        {"name": "Tool Chest Rolling", "category": "Miscellaneous Equipment", "price": Decimal("280.00"), "stock": 10, "extras": []},
    ]
    
    created_count = 0
    
    for item in product_data:
        try:
            category = get_or_create_category(item["category"])
            
            # Randomize stock slightly for realism (±10%)
            base_stock = item["stock"]
            actual_stock = max(5, base_stock + randint(-base_stock//10, base_stock//10))
            
            product, created = Product.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": f"High-quality {item['name']} for professional events",
                    "category": category,
                    "price_per_day": item["price"],
                    "total_stock": actual_stock,
                    "available_stock": actual_stock,
                    "reserved_stock": 0,
                    "is_active": True
                }
            )
            
            # Assign extras if specified
            for extra_name in item.get("extras", []):
                try:
                    extra = Extra.objects.get(name=extra_name)
                    if extra not in product.extras.all():
                        product.extras.add(extra)
                        logger.info(f"Added extra '{extra_name}' to {product.name}")
                except Extra.DoesNotExist:
                    logger.warning(f"Extra '{extra_name}' not found for {product.name}")
            
            if created:
                logger.info(f"Product '{item['name']}' created in category '{category.name}'.")
                created_count += 1
            
        except Exception as e:
            logger.error(f"Error creating product '{item['name']}': {e}")
            continue
    
    print(f"\n✓ Created {created_count} new products across all categories")
    return Product.objects.all()


def main():
    logging.basicConfig(
        level=logging.INFO, 
        format="[%(levelname)s] %(message)s"
    )
    
    try:
        logger.info("Starting product seeding process...")
        
        # First create extras
        extras = seed_extras()
        
        # Then create products using those extras
        products = seed_products(extras)
        
        print(f"\n{'='*60}")
        print("✓ Product seeding completed successfully!")
        print(f"{'='*60}")
        print(f"Total categories: {Category.objects.count()}")
        print(f"Total extras: {Extra.objects.count()}")
        print(f"Total products: {Product.objects.count()}")
        
    except Exception as e:
        logger.error(f"Error during product seeding: {e}")
        raise


if __name__ == "__main__":
    main()

# Execute when run via Django shell
main()
