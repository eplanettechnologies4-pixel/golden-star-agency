from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import BlogPost, BlogCategory


def blog_list_view(request):
    """Public blog listing — all published posts with search, category filter, sorting, and pagination."""
    category_slug = request.GET.get('category', None)
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'latest').strip().lower()

    # Get categories with published post count
    categories = BlogCategory.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    )

    posts_qs = BlogPost.objects.filter(status='published').select_related('category')

    # Category filter
    active_category = None
    if category_slug:
        active_category = BlogCategory.objects.filter(slug=category_slug).first()
        if active_category:
            posts_qs = posts_qs.filter(category=active_category)

    # Search filter
    if search_query:
        posts_qs = posts_qs.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(body__icontains=search_query) |
            Q(author_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Featured post handling (only show separate hero post when no search query is active)
    featured_post = None
    grid_qs = posts_qs

    if not search_query:
        featured_post = posts_qs.filter(is_featured=True).first()
        if not featured_post and not active_category:
            featured_post = posts_qs.first()

        if featured_post:
            grid_qs = posts_qs.exclude(pk=featured_post.pk)

    # Sorting
    if sort_by == 'popular':
        grid_qs = grid_qs.order_by('-views', '-published_at')
    elif sort_by == 'oldest':
        grid_qs = grid_qs.order_by('published_at', 'created_at')
    else: # latest
        grid_qs = grid_qs.order_by('-published_at', '-created_at')

    # Popular / Trending articles for sidebar
    popular_posts = BlogPost.objects.filter(status='published').order_by('-views', '-published_at')[:4]

    # Paginate grid
    paginator = Paginator(grid_qs, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blogs/blog_list.html', {
        'featured_post': featured_post,
        'page_obj': page_obj,
        'categories': categories,
        'active_category': active_category,
        'popular_posts': popular_posts,
        'total_posts': posts_qs.count(),
        'search_query': search_query,
        'sort_by': sort_by,
    })


def blog_detail_view(request, slug):
    """Public detail page for a single blog post — increments view counter."""
    post = get_object_or_404(BlogPost, slug=slug, status='published')

    # Increment view count
    BlogPost.objects.filter(pk=post.pk).update(views=post.views + 1)
    post.views += 1

    # Categories for sidebar
    categories = BlogCategory.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    )

    # Related posts (same category, exclude self)
    related = BlogPost.objects.filter(
        status='published', category=post.category
    ).exclude(pk=post.pk).order_by('-published_at')[:3]

    # Fallback related if no category match
    if not related.exists():
        related = BlogPost.objects.filter(status='published').exclude(pk=post.pk).order_by('-published_at')[:3]

    return render(request, 'blogs/blog_detail.html', {
        'post': post,
        'related_posts': related,
        'categories': categories,
    })
