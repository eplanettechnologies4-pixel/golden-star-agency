import sys
import os

# Add core_admin folder to sys.path so we can import django settings correctly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core_admin', 'apps'))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.content.models import PlatformReview

# Clear existing platform reviews to avoid duplicates
PlatformReview.objects.all().delete()

# Create dummy reviews
dummy_reviews = [
    {
        'name': 'Asim Raza',
        'email': 'asim@example.com',
        'rating': 5,
        'comment': 'Golden Star Agency made my Umrah booking incredibly simple! The packages are highly detailed and customer service is outstanding.'
    },
    {
        'name': 'Khadija Bibi',
        'email': 'khadija@example.com',
        'rating': 5,
        'comment': 'I highly recommend this platform for anyone seeking smooth flight ticketing and fast visit visa processing. Real-time tracking is excellent!'
    },
    {
        'name': 'Tariq Mehmood',
        'email': 'tariq@example.com',
        'rating': 4,
        'comment': 'Very reliable service. The AI chatbot gave accurate visa answers instantly, and the booking was verified within hours.'
    },
    {
        'name': 'Ayesha Khan',
        'email': 'ayesha@example.com',
        'rating': 5,
        'comment': 'A state-of-the-art platform for travel bookings in Pakistan. Highly secure document handling and transparent commission tracking.'
    },
    {
        'name': 'Bilal Siddiqui',
        'email': 'bilal@example.com',
        'rating': 4,
        'comment': 'Excellent B2B features. As an agent, I set custom markups and resell packages easily. Highly recommended!'
    }
]

for review in dummy_reviews:
    PlatformReview.objects.create(
        name=review['name'],
        email=review['email'],
        rating=review['rating'],
        comment=review['comment'],
        is_approved=True
    )

print('Dummy reviews seeded successfully!')
