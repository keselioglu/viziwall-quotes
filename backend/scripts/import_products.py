"""
One-off import of the Viziwall Sep 2026 price list into the database.
Replaces the entire products table (see migration e1908a57cf4d).
Run from backend/: python scripts/import_products.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Product, ProductType

# (product_type, name, description, unit, price_per_day)
# price_per_day is reused generically as "unit price" — the app's line-item
# math is unit_price * quantity * rental_days, and rental_days is left at 1
# for anything not actually billed per rental day.
# Source: Viziwall_price-list_2026_Sep_v1.csv, valid 1/1/2026 - 6/31/2026.
ROWS = [
    # --- Led Wall Panels And Accessories ---
    (ProductType.led_wall, "2.6mm-Flat", "50x50cm panels with 2.6mm pixel pitch, Indoor", "m2", 300.00),
    (ProductType.led_wall, "2.6mm-Flexible", "50x50cm panels with 2.6mm pixel pitch, Indoor", "m2", 350.00),
    (ProductType.led_wall, "2.6mm-Corner", "50x50cm panels with 2.6mm pixel pitch, Indoor", "m2", 300.00),
    (ProductType.led_wall, "1.9mm Flat", "1.95mm pixel pitch, wall mounted, Indoor", "m2", 450.00),
    (ProductType.led_wall, "Led Wall Hanging Accessories", "Rigging bars, safety locks, lifting bolts and hardware", "m2", 35.00),
    (ProductType.led_wall, "Self Stand", "Self stand structure and counter weights", "m2", 20.00),
    (ProductType.led_wall, "NovaStar-TB40", "Self booting media player for ledwalls up to 9sqm", "pcs", 60.00),
    (ProductType.led_wall, "NovaStar-TB60", "Self booting media player for ledwalls up to 15sqm", "pcs", 80.00),
    (ProductType.led_wall, "NovaStar-VX600", "Video processor 3.9 million pixels", "pcs", 160.00),
    (ProductType.led_wall, "NovaStar-VX1000", "Video processor 6.5 million pixels", "pcs", 220.00),
    (ProductType.led_wall, "NovaStar-VX2000", "Video processor 13 million pixels", "pcs", 280.00),

    # --- TV's and Touch Screen Displays ---
    (ProductType.displays, '32" TV', "Smart TV, Full HD with wall mounting", "pcs", 105.00),
    (ProductType.displays, '43" TV', "Smart TV, UHD with wall mounting", "pcs", 125.00),
    (ProductType.displays, '55" TV', "Smart TV, UHD with wall mounting", "pcs", 150.00),
    (ProductType.displays, '65" TV', "Smart TV, UHD with wall mounting", "pcs", 325.00),
    (ProductType.displays, '75" TV', "Smart TV, UHD with wall mounting", "pcs", 450.00),
    (ProductType.displays, '85" TV', "Smart TV, UHD with wall mounting", "pcs", 650.00),
    (ProductType.displays, '98" TV', "Smart TV, UHD with wall mounting", "pcs", 850.00),
    (ProductType.displays, '32" Touch', "Touch Screen Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 175.00),
    (ProductType.displays, '43" Touch', "Touch Screen Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 675.00),
    (ProductType.displays, '75" Touch', "Touch Screen Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 1280.00),
    (ProductType.displays, '85" Touch', "Touch Screen Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 1940.00),
    (ProductType.displays, '55" Vertical', "Vertical Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 250.00),
    (ProductType.displays, '65" Vertical', "Vertical Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 400.00),
    (ProductType.displays, '75" Vertical', "Vertical Display, UHD, Wifi, Hdmi with wall mounting kit", "pcs", 600.00),

    # --- Audio ---
    (ProductType.audio, "RCF ART 710 or 708 Speaker", None, "pcs", 180.00),
    (ProductType.audio, "Shure BLX / SM58 Wireless Microphone", None, "pcs", 225.00),
    (ProductType.audio, "Yamaha MG12XU Mixer", None, "pcs", 180.00),
    (ProductType.audio, "Bluetooth Audio Receiver", None, "pcs", 0.00),
    (ProductType.audio, "Bluetooth speaker 100watt", None, "pcs", 100.00),
    (ProductType.audio, '2 x 5" Active Hi-Fi Speakers wall mounted', None, "pcs", 275.00),

    # --- Laptops & Tablets ---
    (ProductType.it_equipment, "All purpose laptop", "Standard", "pcs", 60.00),
    (ProductType.it_equipment, "Gaming Laptop", "Enhanced display card and processor", "pcs", 125.00),
    (ProductType.it_equipment, 'Apple Ipad 11"', '11" Apple Ipad', "pcs", 125.00),
    (ProductType.it_equipment, 'Samsung Tablet 11"', '10.9" Samsung galaxy tablet', "pcs", 125.00),
    (ProductType.it_equipment, 'Samsung Tablet 13"', '13.1" Samsung galaxy tablet', "pcs", 225.00),
    (ProductType.it_equipment, "Tablet Desk Stand", "Standard desk stand for tablets", "pcs", 40.00),
    (ProductType.it_equipment, "Tablet Charger", "220V charger with 2m Cable", "pcs", 20.00),

    # --- Services ---
    (ProductType.services, "Setup & Dismantling", "Installation, setup, test and dismantling", "m2", 100.00),
    (ProductType.services, "Technician on standby near the venue during event times", "Able to respond within 2 hours if needed", "man", 0.00),
    (ProductType.services, "Technician as operator", "Inside the stand, dedicated like an operator", "day", 200.00),
    (ProductType.services, "Transport", "Transport of rental goods to and from event venue.", "km", 1.20),
    (ProductType.services, "Cross border fee", "Cross Border Documentation for locations outside EU", "pcs", 1400.00),
]


def main():
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        if existing:
            print(f"Deleting {existing} existing product(s)...")
            db.query(Product).delete()

        for product_type, name, description, unit, price in ROWS:
            db.add(Product(
                product_type=product_type,
                name=name,
                description=description,
                unit=unit,
                price_per_day=price,
                is_active=True,
            ))

        db.commit()
        print(f"Imported {len(ROWS)} products.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
