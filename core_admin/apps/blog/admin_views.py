import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.text import slugify
from apps.blog.models import BlogPost, BlogCategory
from apps.blog.tasks import trigger_n8n_content_update_webhook

logger = logging.getLogger(__name__)


from functools import wraps

def is_admin(user):
    """Check if user has super_admin/admin role, is_staff, or is_superuser."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or getattr(user, 'role', '') in ['super_admin', 'admin']


def admin_required_api(view_func):
    """API decorator that returns JSON 403 Forbidden instead of HTML redirect on permission failure."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Admin authentication required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


@user_passes_test(is_admin)
def admin_blogs_page_view(request):
    """
    Renders the Admin Blog Management Panel SPA template.
    URL: /dashboard/admin/blogs/
    """
    return render(request, 'dashboard/admin/blogs_list.html')


@csrf_exempt
@admin_required_api
def admin_blogs_list_api(request):
    """
    GET /dashboard/admin/api/blogs/
    Query params:
      - q: Search by title
      - category: Filter by category ID or slug
      - status: Filter by 'all', 'draft', or 'published'
      - page: Page number (default 1, 20 items per page)
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    queryset = BlogPost.objects.select_related('category').all()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(title__icontains=q)

    # Category filter
    cat_val = request.GET.get('category', '').strip()
    if cat_val and cat_val != 'all':
        if cat_val.isdigit():
            queryset = queryset.filter(category_id=int(cat_val))
        else:
            queryset = queryset.filter(category__slug=cat_val)

    # Status filter
    status_val = request.GET.get('status', '').strip()
    if status_val in ['draft', 'published']:
        queryset = queryset.filter(status=status_val)

    # Order by latest created
    queryset = queryset.order_by('-created_at')

    # Pagination (Default 100 per page to show all posts)
    page_size = int(request.GET.get('page_size', 100))
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    posts_data = []
    for p in page_obj:
        posts_data.append({
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'category_id': p.category_id,
            'category_name': p.category.name if p.category else 'Uncategorized',
            'category_color': p.category.color if p.category else 'slate',
            'author_name': p.author_name,
            'read_time': p.read_time,
            'views': p.views,
            'status': p.status,
            'is_featured': p.is_featured,
            'cover_url': p.cover_image.url if p.cover_image else (f"/static/images/{p.static_cover}" if p.static_cover else "/static/images/blog_banner.png"),
            'static_cover': p.static_cover or '',
            'excerpt': p.excerpt,
            'created_at': p.created_at.strftime('%b %d, %Y'),
            'updated_at': p.updated_at.strftime('%b %d, %Y'),
            'published_at': p.published_at.strftime('%b %d, %Y') if p.published_at else 'Not Published',
        })

    categories = list(BlogCategory.objects.all().values('id', 'name', 'slug', 'color'))

    return JsonResponse({
        'success': True,
        'posts': posts_data,
        'categories': categories,
        'pagination': {
            'current_page': page_obj.number,
            'num_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


import threading

def safe_trigger_n8n_webhook(post_id):
    """Safely trigger n8n task in a daemon thread so web API returns INSTANTLY without blocking."""
    def _bg_run():
        try:
            trigger_n8n_content_update_webhook(post_id)
        except Exception as err:
            logger.warning(f"Background webhook dispatch failed: {err}")

    t = threading.Thread(target=_bg_run, daemon=True)
    t.start()


@csrf_exempt
@admin_required_api
def admin_blog_create_api(request):
    """
    POST /dashboard/admin/api/blogs/create/
    Creates a new blog post. Supports multipart/form-data for file uploads.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)

    try:
        data = request.POST if request.POST else json.loads(request.body or '{}')
    except Exception:
        data = request.POST

    title = (data.get('title') or '').strip()
    if not title:
        return JsonResponse({'success': False, 'message': 'Title is required.'}, status=400)

    category_id = data.get('category_id') or data.get('category')
    category = None
    if category_id:
        category = BlogCategory.objects.filter(id=category_id).first()

    status_val = data.get('status', 'draft')
    if status_val not in ['draft', 'published']:
        status_val = 'draft'

    is_featured = str(data.get('is_featured', '')).lower() in ['true', '1', 'on']

    post = BlogPost(
        title=title,
        category=category,
        author_name=(data.get('author_name') or 'Golden Star Team').strip(),
        read_time=int(data.get('read_time') or 5),
        status=status_val,
        is_featured=is_featured,
        static_cover=(data.get('static_cover') or '').strip() or None,
        excerpt=(data.get('excerpt') or '').strip(),
        body=(data.get('body') or '').strip(),
    )

    if 'cover_image' in request.FILES:
        post.cover_image = request.FILES['cover_image']

    if status_val == 'published':
        post.published_at = timezone.now()

    post.save()

    # Trigger n8n webhook safely if published
    if post.status == 'published':
        safe_trigger_n8n_webhook(post.id)

    return JsonResponse({
        'success': True,
        'message': f'Blog article "{post.title}" created successfully.',
        'slug': post.slug,
        'id': post.id
    })


@csrf_exempt
@admin_required_api
def admin_blog_detail_api(request, slug):
    """
    GET  /dashboard/admin/api/blogs/<slug>/ -> Return blog details for editing.
    POST /dashboard/admin/api/blogs/<slug>/ -> Update existing blog post.
    """
    post = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'post': {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'category_id': post.category_id,
                'author_name': post.author_name,
                'read_time': post.read_time,
                'status': post.status,
                'is_featured': post.is_featured,
                'cover_url': post.cover_image.url if post.cover_image else None,
                'static_cover': post.static_cover or '',
                'excerpt': post.excerpt,
                'body': post.body,
                'views': post.views,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M'),
                'published_at': post.published_at.strftime('%Y-%m-%d %H:%M') if post.published_at else None,
            }
        })

    elif request.method == 'POST':
        try:
            data = request.POST if request.POST else json.loads(request.body or '{}')
        except Exception:
            data = request.POST

        title = (data.get('title') or '').strip()
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required.'}, status=400)

        category_id = data.get('category_id') or data.get('category')
        if category_id:
            post.category = BlogCategory.objects.filter(id=category_id).first()
        elif 'category_id' in data or 'category' in data:
            post.category = None

        new_status = data.get('status', post.status)
        if new_status in ['draft', 'published']:
            if new_status == 'published' and post.status != 'published' and not post.published_at:
                post.published_at = timezone.now()
                safe_trigger_n8n_webhook(post.id)
            post.status = new_status

        post.title = title
        post.author_name = (data.get('author_name') or post.author_name).strip()
        post.read_time = int(data.get('read_time') or post.read_time or 5)
        post.is_featured = str(data.get('is_featured', '')).lower() in ['true', '1', 'on']
        post.static_cover = (data.get('static_cover') or '').strip() or None
        post.excerpt = (data.get('excerpt') or '').strip()
        post.body = (data.get('body') or '').strip()

        if 'cover_image' in request.FILES:
            post.cover_image = request.FILES['cover_image']

        post.save()

        return JsonResponse({
            'success': True,
            'message': f'Blog article "{post.title}" updated successfully.',
            'slug': post.slug
        })

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_blog_delete_api(request, slug):
    """
    DELETE or POST /dashboard/admin/api/blogs/<slug>/delete/
    Hard deletes a BlogPost.
    """
    if request.method not in ['POST', 'DELETE']:
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    post = get_object_or_404(BlogPost, slug=slug)
    title = post.title
    post.delete()

    return JsonResponse({'success': True, 'message': f'Blog article "{title}" deleted successfully.'})


@csrf_exempt
@admin_required_api
def admin_blog_toggle_publish_api(request, slug):
    """
    POST /dashboard/admin/api/blogs/<slug>/toggle-publish/
    Flips status between 'draft' and 'published'.
    Sets published_at if empty when published.
    Dispatches Celery webhook task to N8N when status becomes 'published'.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)

    post = get_object_or_404(BlogPost, slug=slug)

    if post.status == 'published':
        post.status = 'draft'
        new_status = 'draft'
    else:
        post.status = 'published'
        new_status = 'published'
        if not post.published_at:
            post.published_at = timezone.now()

    post.save()

    # IMPORTANT: Fire N8N webhook via Celery task when published
    if post.status == 'published':
        safe_trigger_n8n_webhook(post.id)

    return JsonResponse({
        'success': True,
        'new_status': new_status,
        'message': f'"{post.title}" is now {new_status}.'
    })


@csrf_exempt
@admin_required_api
def admin_blog_categories_api(request):
    """
    GET /dashboard/admin/api/blog-categories/
    Returns list of all BlogCategory items with post count.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    categories = BlogCategory.objects.all().order_by('name')
    data = []
    for c in categories:
        data.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'color': c.color,
            'posts_count': c.posts.count(),
        })

    return JsonResponse({'success': True, 'categories': data})


@csrf_exempt
@admin_required_api
def admin_blog_category_create_api(request):
    """
    POST /dashboard/admin/api/blog-categories/create/
    Creates a new BlogCategory. Auto-slugifies name.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required.'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except Exception:
        data = request.POST

    name = (data.get('name') or '').strip()
    if not name:
        return JsonResponse({'success': False, 'message': 'Category name is required.'}, status=400)

    color = (data.get('color') or 'brand-orange').strip()

    category, created = BlogCategory.objects.get_or_create(
        name=name,
        defaults={'color': color}
    )
    if not created:
        category.color = color
        category.save()

    return JsonResponse({
        'success': True,
        'message': f'Category "{category.name}" created.',
        'category': {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'color': category.color,
        }
    })
