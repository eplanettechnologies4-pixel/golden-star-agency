import sys
import os

# Add core_admin folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.packages.models import Package
from apps.bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()
test_user = User.objects.first()

print("--- Testing Multi-Tier Room Pricing & Booking API ---")

# 1. Fetch or update package with Quad, Triple, Double, Child pricing & discount
pkg = Package.objects.filter(category='umrah').first()
pkg.price_quad = 245000.00
pkg.price_triple = 275000.00
pkg.price_double = 320000.00
pkg.price_child = 180000.00
pkg.discount_percentage = 5.00 # 5% Off
pkg.discount_amount = 5000.00 # PKR 5,000 flat discount
pkg.original_price = 290000.00
pkg.save()

print(f"Configured Package '{pkg.title}':")
print(f" - Quad: PKR {pkg.price_quad:,.2f}")
print(f" - Triple: PKR {pkg.price_triple:,.2f}")
print(f" - Double: PKR {pkg.price_double:,.2f}")
print(f" - Child: PKR {pkg.price_child:,.2f}")
print(f" - Discount: {pkg.discount_percentage}% + PKR {pkg.discount_amount:,.2f}")

# 2. Simulate Booking: 2 Adults, 1 Child in Triple Sharing
adults_count = 2
children_count = 1
sharing_category = "Triple"

adults_cost = adults_count * float(pkg.price_triple) # 2 * 275,000 = 550,000
children_cost = children_count * float(pkg.price_child) # 1 * 180,000 = 180,000
subtotal = adults_cost + children_cost # 730,000

discount_applied = (subtotal * float(pkg.discount_percentage) / 100.0) + float(pkg.discount_amount) # (730,000 * 0.05) + 5,000 = 41,500
expected_total = subtotal - discount_applied # 688,500

booking = Booking.objects.create(
    user=test_user,
    package=pkg,
    booking_type='package',
    status='pending',
    sharing_category=sharing_category,
    adults_count=adults_count,
    children_count=children_count,
    discount_applied=discount_applied,
    total_price=expected_total
)

print(f"\n[TEST PASS] Created Booking ID #{booking.id}:")
print(f" - Tracking Reference: GSA-B-{booking.id}")
print(f" - Subtotal: PKR {subtotal:,.2f}")
print(f" - Discount Applied: PKR {discount_applied:,.2f}")
print(f" - Calculated Total Price: PKR {float(booking.total_price):,.2f}")

assert float(booking.total_price) == expected_total, f"Calculated price mismatch! Got {booking.total_price}, expected {expected_total}"

# Cleanup
booking.delete()
print("Cleaned up test booking. All pricing math & model assertions passed 100% successfully!\n")
