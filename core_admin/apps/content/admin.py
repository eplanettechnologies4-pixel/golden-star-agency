from django.contrib import admin
from .models import PlatformReview, Achievement


@admin.register(PlatformReview)
class PlatformReviewAdmin(admin.ModelAdmin):
    list_display  = ('name', 'reviewer_title', 'rating', 'is_featured', 'is_approved', 'created_at')
    list_filter   = ('is_approved', 'is_featured', 'rating')
    list_editable = ('is_approved', 'is_featured')
    search_fields = ('name', 'email', 'comment', 'reviewer_title')
    readonly_fields = ('created_at',)
    ordering      = ('-is_featured', '-created_at')

    fieldsets = (
        ('Reviewer Info', {
            'fields': ('name', 'reviewer_title', 'email', 'rating', 'comment')
        }),
        ('Attachment', {
            'fields': ('photo',),
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'created_at'),
        }),
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'date', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-date', '-created_at')
