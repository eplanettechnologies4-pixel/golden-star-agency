import pytest
import json
from django.urls import reverse
from django.test import Client
from apps.packages.models import CustomPackageInquiry
from apps.accounts.models import User

@pytest.mark.django_db
def test_custom_inquiry_creation():
    client = Client()
    user = User.objects.create_user(username='danish_inquirer', email='danish@gmail.com', password='password')
    client.force_login(user)

    url = reverse('submit_custom_inquiry_api')
    payload = {
        'name': 'Danish Inquirer',
        'email': 'danish@gmail.com',
        'phone': '1234567890',
        'package_type': 'hajj',
        'days': 21,
        'makkah_distance': 400,
        'madinah_distance': 250,
        'airline': 'Saudi Airlines',
        'additional_notes': 'Wheelchair required please.'
    }
    
    # POST request
    response = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    assert response.json()['success'] is True
    
    # Verify DB persistence
    assert CustomPackageInquiry.objects.count() == 1
    inquiry = CustomPackageInquiry.objects.first()
    assert inquiry.name == 'Danish Inquirer'
    assert inquiry.email == 'danish@gmail.com'
    assert inquiry.days == 21
    assert inquiry.makkah_distance == 400
    assert inquiry.airline == 'Saudi Airlines'
    assert inquiry.additional_notes == 'Wheelchair required please.'
    assert inquiry.is_contacted is False


@pytest.mark.django_db
def test_admin_list_and_contact():
    client = Client()
    # Create superuser
    admin = User.objects.create_superuser(username='admin_test', email='admin@test.com', password='password')
    client.force_login(admin)

    # Create dummy custom inquiry
    inquiry = CustomPackageInquiry.objects.create(
        name='Test Client',
        email='client@test.com',
        phone='999999',
        package_type='umrah',
        days=10,
        makkah_distance=200,
        madinah_distance=150,
        airline='PIA'
    )

    # Fetch list
    list_url = reverse('admin_custom_inquiries_list_api')
    response = client.get(list_url)
    assert response.status_code == 200
    assert len(response.json()['inquiries']) == 1
    assert response.json()['inquiries'][0]['name'] == 'Test Client'

    # Toggle Contact Status
    contact_url = reverse('admin_custom_inquiry_contact_api', kwargs={'pk': inquiry.id})
    response = client.post(contact_url)
    assert response.status_code == 200
    assert response.json()['success'] is True
    assert response.json()['is_contacted'] is True

    # Check updated DB
    inquiry.refresh_from_db()
    assert inquiry.is_contacted is True
