"""
Seed categories for the Le Gize rental system.

Usage:
    source .venv/bin/activate
    python manage.py shell < tests/scripts/seed_categories.py

This script is idempotent – you can run it multiple times and it will keep
category records in sync rather than duplicating them.
"""

import logging
from decimal import Decimal

from django.db.models import Q

from products.models import Category, Extra, Product

logger = logging.getLogger("seed_categories")


def seed_categories():
    """Create 20 equipment rental categories with common items."""
    
    category_data = [
        {
            "name": "Lighting & Electrical",
            "description": "Stage lighting, floodlights, generators, and electrical equipment"
        },
        {
            "name": "Sound Systems",
            "description": "Speakers, microphones, mixers, and audio equipment for events"
        },
        {
            "name": "Staging & Platforms",
            "description": "Stage platforms, risers, trusses, and support structures"
        },
        {
            "name": "Seating & Furniture",
            "description": "Chairs, tables, sofas, and event furniture for venues"
        },
        {
            "name": "Climate Control",
            "description": "Air conditioners, heaters, fans, and climate management systems"
        },
        {
            "name": "Projection & Video",
            "description": "Projectors, screens, LED walls, and video display equipment"
        },
        {
            "name": "Power Distribution",
            "description": "Generators, power strips, cables, and electrical distribution systems"
        },
        {
            "name": "Safety & Security",
            "description": "Fire extinguishers, barriers, signage, and safety equipment"
        },
        {
            "name": "Decor & Drapery",
            "description": "Backdrops, curtains, decorative elements, and stage dressing"
        },
        {
            "name": "Tools & Equipment",
            "description": "Power tools, hand tools, ladders, and construction equipment"
        },
        {
            "name": "Medical & First Aid",
            "description": "First aid kits, defibrillators, medical supplies for events"
        },
        {
            "name": "Cleaning Supplies",
            "description": "Janitorial equipment, cleaning chemicals, and maintenance tools"
        },
        {
            "name": "Office & IT Equipment",
            "description": "Computers, printers, scanners, networking gear for events"
        },
        {
            "name": "Transportation & Lifting",
            "description": "Forklifts, pallet jacks, dollies, and material handling equipment"
        },
        {
            "name": "Communication Systems",
            "description": "Two-way radios, intercom systems, PA systems for coordination"
        },
        {
            "name": "Photography & Video",
            "description": "Cameras, tripods, lighting stands, and video production gear"
        },
        {
            "name": "Outdoor & Camping",
            "description": "Tents, canopies, outdoor furniture, and camping equipment"
        },
        {
            "name": "Special Effects",
            "description": "Smoke machines, foggers, confetti cannons, and entertainment effects"
        },
        {
            "name": "Storage & Organization",
            "description": "Storage containers, shelving units, and organizational systems"
        },
        {
            "name": "Miscellaneous Equipment",
            "description": "Various other rental items not covered in specific categories"
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for cat_data in category_data:
        category, created = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={
                "description": cat_data["description"]
            }
        )
        
        if created:
            logger.info(f"Created category: {category.name}")
            created_count += 1
        else:
            # Update description if it changed
            old_desc = category.description
            if old_desc != cat_data["description"]:
                category.description = cat_data["description"]
                category.save()
                logger.info(f"Updated description for {category.name}")
            updated_count += 1
    
    print(f"\nSeed completed:")
    print(f"- Created: {created_count} new categories")
    print(f"- Updated: {updated_count} existing categories")
    print(f"- Total categories now: {Category.objects.count()}")
    
    return created_count, updated_count


def main():
    logging.basicConfig(
        level=logging.INFO, 
        format="[%(levelname)s] %(message)s"
    )
    
    try:
        create_count, update_count = seed_categories()
        
        print("\n✓ Category seeding successful!")
        print(f"\nTotal categories in system: {Category.objects.count()}")
        
    except Exception as e:
        logger.error(f"Error during category seeding: {e}")
        raise


if __name__ == "__main__":
    main()

# Execute when run via Django shell
main()
