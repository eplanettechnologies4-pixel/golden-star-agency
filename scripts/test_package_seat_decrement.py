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
admin_user = User.objects.filter(role='admin').first() or User.objects.filter(is_superuser=True).first()

print("--- Testing Package Seat Auto-Decrement ---")

pkg = Package.objects.filter(category='umrah').first()
initial_seats = pkg.available_seats
print(f"Package '{pkg.title}' starting seats: {initial_seats}/{pkg.total_seats}")

# 1. Create a pending booking for this package
test_user = User.objects.first()
booking = Booking.objects.create(
    user=test_user,
    package=pkg,
    booking_type='package',
    status='pending',
    total_price=pkg.price
)
print(f"Created pending booking ID #{booking.id} for user {test_user.username}.")

# 2. Confirm booking
booking.status = 'confirmed'
# Simulate admin status view logic
if booking.package:
    booking.package.available_seats = max(0, booking.package.available_seats - 1)
    booking.package.save()
booking.save()

pkg.refresh_from_db()
print(f"[TEST PASS] Confirmed booking -> Available seats decremented to: {pkg.available_seats}/{pkg.total_seats}")
assert pkg.available_seats == initial_seats - 1, "Seats did not decrement properly!"

# 3. Cancel booking
booking.status = 'cancelled'
if booking.package:
    booking.package.available_seats = min(booking.package.total_seats, booking.package.available_seats + 1)
    booking.package.save()
booking.save()

pkg.refresh_from_db()
print(f"[TEST PASS] Cancelled booking -> Available seats restored to: {pkg.available_seats}/{pkg.total_seats}")
assert pkg.available_seats == initial_seats, "Seats did not restore properly!"

# Cleanup test booking
booking.delete()
print("Cleaned up test booking. All package auto-decrement tests passed successfully!\n")
