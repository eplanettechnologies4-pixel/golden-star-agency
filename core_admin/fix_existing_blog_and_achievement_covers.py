import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.blog.models import BlogPost
from apps.content.models import Achievement

print("=== FIXING BLOG POST COVERS ===")
blogs = BlogPost.objects.all()
fixed_blogs = 0
for b in blogs:
    if not b.cover_image and not b.static_cover:
        b.static_cover = 'blog_banner.png'
        b.save()
        fixed_blogs += 1
        print(f"Fixed Blog #{b.id}: {b.title} -> static_cover='blog_banner.png'")

print(f"Total Blogs updated: {fixed_blogs}")

print("\n=== FIXING ACHIEVEMENTS PHOTOS ===")
achievements = Achievement.objects.all()
fixed_achs = 0
for a in achievements:
    if not a.photo:
        if a.category == 'video':
            a.photo = 'achievements/Video.png'
        elif a.category == 'meeting':
            a.photo = 'achievements/Meeting.png'
        elif a.category == 'review':
            a.photo = 'achievements/Screenshot_2026-07-29_060658.png'
        else:
            a.photo = 'achievements/TDA_Award.png'
        a.save()
        fixed_achs += 1
        print(f"Fixed Achievement #{a.id}: {a.title} -> photo='{a.photo}'")

print(f"Total Achievements updated: {fixed_achs}")
