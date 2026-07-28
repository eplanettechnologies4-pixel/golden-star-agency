from django.contrib import admin
from .models import BlogPost, BlogCategory


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author_name', 'status', 'is_featured', 'views', 'published_at', 'created_at')
    list_filter = ('status', 'is_featured', 'category')
    search_fields = ('title', 'excerpt', 'body', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')
    readonly_fields = ('views', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'excerpt', 'body')
        }),
        ('Media', {
            'fields': ('cover_image', 'static_cover'),
        }),
        ('Author', {
            'fields': ('author_name', 'author_avatar', 'read_time'),
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'published_at'),
        }),
        ('Stats', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
