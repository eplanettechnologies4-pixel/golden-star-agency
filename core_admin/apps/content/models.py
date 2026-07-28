from django.db import models


class PlatformReview(models.Model):
    # Core review fields
    name            = models.CharField(max_length=100)
    reviewer_title  = models.CharField(max_length=120, blank=True, null=True,
                                       help_text='e.g. Hajj Pilgrim 2024, CEO at Al-Noor Travels')
    email           = models.EmailField(blank=True, null=True)
    rating          = models.IntegerField(default=5)  # 1–5 stars
    comment         = models.TextField()

    # Image attachment (admin-added)
    photo           = models.ImageField(upload_to='reviews/photos/', blank=True, null=True,
                                        help_text='Reviewer photo or trip photo')

    # Moderation
    is_approved     = models.BooleanField(default=True)
    is_featured     = models.BooleanField(default=False, help_text='Pin this review to appear first in the carousel')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = 'Platform Review'
        verbose_name_plural = 'Platform Reviews'

    def __str__(self):
        has_photo = "With Photo" if self.photo else "Text Only"
        return f"Review by {self.name} — {self.rating}★ ({has_photo})"


class Achievement(models.Model):
    CATEGORY_CHOICES = [
        ('review', 'Review'),
        ('video', 'Video / Media'),
        ('meeting', 'Meeting / Event'),
        ('milestone', 'Milestone / Award'),
    ]
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='milestone')
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='achievements/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text='Link to YouTube, Vimeo, etc. (optional)')
    date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"
