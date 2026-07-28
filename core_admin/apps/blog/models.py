from django.db import models
from django.utils.text import slugify
from django.conf import settings


class BlogCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True, blank=True)
    color = models.CharField(max_length=30, default='brand-orange', help_text='Tailwind color class prefix e.g. emerald, blue, brand-orange')

    class Meta:
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=220)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    cover_image = models.ImageField(upload_to='blog/covers/', blank=True, null=True)
    static_cover = models.CharField(
        max_length=120, blank=True, null=True,
        help_text='Filename of static image inside static/images/ e.g. blog_hajj.png'
    )
    excerpt = models.TextField(max_length=300, blank=True, help_text='Short summary shown on list cards')
    body = models.TextField(help_text='Full article body (supports HTML / markdown)')
    author_name = models.CharField(max_length=100, default='Golden Star Team')
    author_avatar = models.CharField(max_length=120, blank=True, null=True,
                                     help_text='Filename of static avatar image e.g. avatar_team.png')
    read_time = models.PositiveIntegerField(default=5, help_text='Estimated read time in minutes')
    is_featured = models.BooleanField(default=False, help_text='Show in hero/featured slot on blog list')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    views = models.PositiveIntegerField(default=0, editable=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        if self.cover_image:
            return self.cover_image.url
        return None
