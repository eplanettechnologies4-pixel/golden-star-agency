import os
import sys
import json
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core_admin'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from apps.packages.models import Package, CustomPackageInquiry
from apps.bookings.models import Booking
from apps.accounts.views import submit_custom_inquiry_api
from apps.packages.views import book_package_api

def run_tests():
    print("--- 1. Testing Contact Us Form Submission API ---")
    factory = RequestFactory()
    contact_payload = {
        'name': 'Test Pilgrim User',
        'email': 'testpilgrim@example.com',
        'phone': '+92 300 9876543',
        'package_type': 'contact',
        'additional_notes': 'Inquiry about Umrah package dates for November 2026.'
    }
    req = factory.post(
        '/api/packages/custom-inquiry/',
        data=json.dumps(contact_payload),
        content_type='application/json'
    )
    res = submit_custom_inquiry_api(req)
    res_data = json.loads(res.content.decode('utf-8'))
    print(f"Contact API Response: Status {res.status_code}, Data: {res_data}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res_data.get('success') is True, "Expected success: True"
    
    inquiry = CustomPackageInquiry.objects.get(id=res_data['id'])
    assert inquiry.name == 'Test Pilgrim User'
    assert inquiry.email == 'testpilgrim@example.com'
    assert inquiry.phone == '+92 300 9876543'
    assert inquiry.package_type == 'contact'
    print("[PASS] Contact Us Form submission verified successfully!\n")

    print("--- 2. Testing Package Booking API & Guest String Representation ---")
    # Fetch an existing package from DB
    pkg = Package.objects.first()
    if not pkg:
        pkg = Package.objects.create(
            title='Economy Umrah Package 2026 Test',
            price=210000.0,
            available_seats=20
        )
    initial_seats = pkg.available_seats

    booking_payload = {
        'package_id': pkg.id,
        'full_name': 'Guest Pilgrim Test',
        'email': 'guestpilgrim@example.com',
        'phone_number': '+92 300 1112233',
        'sharing_category': 'quad',
        'adults_count': 2,
        'children_count': 1,
        'children_with_bed_count': 1,
        'children_no_bed_count': 0,
        'infants_count': 0
    }

    req_book = factory.post(
        '/api/packages/book/',
        data=json.dumps(booking_payload),
        content_type='application/json'
    )
    res_book = book_package_api(req_book)
    res_book_data = json.loads(res_book.content.decode('utf-8'))
    print(f"Booking API Response: Status {res_book.status_code}, Data: {res_book_data}")
    assert res_book.status_code == 200
    assert res_book_data.get('success') is True

    # Verify Booking record and guest string representation
    booking_id = res_book_data.get('tracking_id')
    booking = Booking.objects.get(pnr=booking_id)
    assert booking.user is None
    str_repr = str(booking)
    print(f"Guest Booking __str__: {str_repr}")
    assert 'Guest Pilgrim Test' in str_repr or 'guestpilgrim@example.com' in str_repr

    # Verify seat decrement
    pkg.refresh_from_db()
    assert pkg.available_seats == initial_seats - 3, f"Expected {initial_seats - 3}, got {pkg.available_seats}"
    print("[PASS] Package booking submission & seat decrement verified successfully!\n")

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
