"""
Seed script — creates sample Platform Reviews with name, stars, email, comment, and photos.
Run: python core_admin/seed_reviews.py
"""
import os
import sys
import shutil
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.content.models import PlatformReview
from django.conf import settings

def seed():
    # Ensure media directory for reviews exists
    reviews_media_dir = os.path.join(settings.MEDIA_ROOT, 'reviews', 'photos')
    os.makedirs(reviews_media_dir, exist_ok=True)

    # Destination paths for seed files
    dest_img1 = os.path.join(reviews_media_dir, 'seed_umrah.png')
    dest_img2 = os.path.join(reviews_media_dir, 'seed_hajj.png')

    # Source files
    src_img1 = os.path.join(settings.BASE_DIR, 'static', 'images', 'umrah_card.png')
    src_img2 = os.path.join(settings.BASE_DIR, 'static', 'images', 'hajj_card.png')

    # Copy files if they exist
    if os.path.exists(src_img1):
        shutil.copy(src_img1, dest_img1)
    if os.path.exists(src_img2):
        shutil.copy(src_img2, dest_img2)

    # Clear existing reviews to populate fresh demo content
    PlatformReview.objects.all().delete()

    # 1. Image Review (Umrah)
    PlatformReview.objects.create(
        name="Asim Raza",
        reviewer_title="B2B Travel Agent (Lahore)",
        email="asim.raza@travelpartners.pk",
        rating=5,
        comment="Seeded via backend: Exceptional response time for Rabi-ul-Awwal packages. The markup adjustment feature in the dashboard saved us time. Our clients returned extremely satisfied with standard premium accommodation close to the Haram.",
        photo="reviews/photos/seed_umrah.png",
        is_approved=True,
        is_featured=True
    )

    # 2. Text Review
    PlatformReview.objects.create(
        name="Dr. Sarah Chishti",
        reviewer_title="Family Pilgrimage 2025",
        email="sarah.chishti@gmail.com",
        rating=5,
        comment="Seeded via backend: High quality VIP Maktab setup in Mina, buffet meals, and comfortable shuttle transfers. Booking through Golden Star simplified our documentation entirely.",
        is_approved=True,
        is_featured=True
    )

    # 3. Standard Text Review
    PlatformReview.objects.create(
        name="Muhammad Bilal",
        reviewer_title="Corporate Travel Coordinator",
        email="bilal@hashoo.com.pk",
        rating=4,
        comment="Excellent portal layout. Ticket status tracking is updated in real-time. Looking forward to more direct integrations with airline systems.",
        is_approved=True,
        is_featured=False
    )

    # 4. Image Review (Hajj)
    PlatformReview.objects.create(
        name="Kashif Siddiqui",
        reviewer_title="Hajj Executive Pilgrim 2025",
        email="kashif@siddiquitrade.com",
        rating=5,
        comment="Unbelievable high-end premium arrangements. Worth every single PKR for executive shift packages. Highly recommend private package customisation.",
        photo="reviews/photos/seed_hajj.png",
        is_approved=True,
        is_featured=False
    )

    print("Success: Seeded 4 platform reviews with photo properties!")

if __name__ == '__main__':
    seed()
