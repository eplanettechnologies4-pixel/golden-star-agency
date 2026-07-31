from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from .models import PlatformReview, Achievement
import json

def get_approved_reviews_api(request):
    """
    GET: Get approved platform reviews with photo attachment.
    """
    reviews = PlatformReview.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')
    reviews_data = []
    for r in reviews:
        reviews_data.append({
            'id':              r.id,
            'name':            r.name,
            'reviewer_title':  r.reviewer_title or '',
            'rating':          r.rating,
            'comment':         r.comment,
            'photo_url':       r.photo.url if r.photo else None,
            'is_featured':     r.is_featured,
            'created_at':      r.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'success': True, 'reviews': reviews_data})


@csrf_exempt
def submit_review_api(request):
    """
    POST: Submit a platform review.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST requests allowed.'}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    name = str(data.get('name') or '').strip()
    email = str(data.get('email') or '').strip()
    comment = str(data.get('comment') or '').strip()
    rating_val = data.get('rating')

    if not name or not comment:
        return JsonResponse({'success': False, 'message': 'Name and review comment are required.'}, status=400)

    try:
        rating = int(rating_val) if rating_val is not None else 5
        if rating < 1 or rating > 5:
            rating = 5
    except Exception:
        rating = 5

    review = PlatformReview.objects.create(
        name=name,
        email=email,
        rating=rating,
        comment=comment,
        is_approved=True
    )

    return JsonResponse({
        'success': True,
        'message': 'Review submitted successfully!',
        'review': {
            'id': review.id,
            'name': review.name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or getattr(user, 'role', '') in ['super_admin', 'admin']

@user_passes_test(is_admin)
def admin_reviews_list_api(request):
    """
    GET: Get all reviews for admin dashboard.
    """
    reviews = PlatformReview.objects.all().order_by('-created_at')
    reviews_data = []
    for r in reviews:
        reviews_data.append({
            'id': r.id,
            'name': r.name,
            'email': r.email or 'N/A',
            'rating': r.rating,
            'comment': r.comment,
            'is_approved': r.is_approved,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'success': True, 'reviews': reviews_data})

@csrf_exempt
@user_passes_test(is_admin)
def admin_review_toggle_api(request, review_id):
    """
    POST: Toggle approval status of a review.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST requests allowed.'}, status=405)
    
    try:
        review = PlatformReview.objects.get(id=review_id)
        review.is_approved = not review.is_approved
        review.save()
        return JsonResponse({'success': True, 'is_approved': review.is_approved})
    except PlatformReview.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found.'}, status=404)

@csrf_exempt
@user_passes_test(is_admin)
def admin_review_delete_api(request, review_id):
    """
    POST/DELETE: Delete a review.
    """
    try:
        review = PlatformReview.objects.get(id=review_id)
        review.delete()
        return JsonResponse({'success': True, 'message': 'Review deleted successfully.'})
    except PlatformReview.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found.'}, status=404)


# ============================================================
# PUBLIC FRONTEND: Achievements Page
# ============================================================

def achievements_list_view(request):
    """Public page listing all active achievements."""
    achievements = Achievement.objects.filter(is_active=True).order_by('-date', '-created_at')
    return render(request, 'achievements.html', {'achievements': achievements})


# ============================================================
# ADMIN API: Achievements CRUD
# ============================================================

@user_passes_test(is_admin)
def admin_achievements_list_api(request):
    """GET: List all achievements for admin dashboard."""
    achievements = Achievement.objects.all().order_by('-date', '-created_at')
    data = []
    for a in achievements:
        data.append({
            'id':               a.id,
            'title':            a.title,
            'category':         a.category,
            'category_display': a.get_category_display(),
            'description':      a.description or '',
            'photo_url':        a.photo.url if a.photo else None,
            'video_url':        a.video_url or '',
            'date':             a.date.strftime('%Y-%m-%d') if a.date else '',
            'is_active':        a.is_active,
            'created_at':       a.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'success': True, 'achievements': data})


@csrf_exempt
@user_passes_test(is_admin)
def admin_achievement_create_api(request):
    """POST: Create a new achievement (multipart/form-data for photo upload)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed.'}, status=405)

    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'success': False, 'message': 'Title is required.'}, status=400)

    achievement = Achievement(
        title=title,
        category=request.POST.get('category', 'milestone'),
        description=request.POST.get('description', '').strip(),
        video_url=request.POST.get('video_url', '').strip() or None,
        date=request.POST.get('date') or None,
        is_active=request.POST.get('is_active', 'true') == 'true',
    )
    if 'photo' in request.FILES:
        achievement.photo = request.FILES['photo']
    achievement.save()

    return JsonResponse({'success': True, 'id': achievement.id, 'message': 'Achievement created.'})


@csrf_exempt
@user_passes_test(is_admin)
def admin_achievement_detail_api(request, pk):
    """POST: Update  |  DELETE: Delete a specific achievement."""
    try:
        achievement = Achievement.objects.get(pk=pk)
    except Achievement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Not found.'}, status=404)

    if request.method == 'DELETE':
        achievement.delete()
        return JsonResponse({'success': True, 'message': 'Deleted.'})

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            achievement.title = title
        achievement.category    = request.POST.get('category', achievement.category)
        achievement.description = request.POST.get('description', achievement.description or '')
        achievement.video_url   = request.POST.get('video_url', achievement.video_url or '') or None
        achievement.date        = request.POST.get('date') or achievement.date
        achievement.is_active   = request.POST.get('is_active', 'true') == 'true'
        if 'photo' in request.FILES:
            achievement.photo = request.FILES['photo']
        achievement.save()
        return JsonResponse({'success': True, 'message': 'Updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


def robots_txt_view(request):
    """
    Serves plain-text robots.txt allowing search indexing for public routes
    while strictly disallowing internal dashboard, auth, and admin URLs.
    """
    host = request.build_absolute_uri('/')[:-1]
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /dashboard/\n"
        "Disallow: /auth/\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n\n"
        f"Sitemap: {host}/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")
