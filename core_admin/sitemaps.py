from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.packages.models import Package
from apps.blog.models import BlogPost
from apps.visa.models import VisaPackage


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return [
            'home',
            'about',
            'contact',
            'careers',
            'privacy_policy',
            'achievements_list',
            'hajj_list',
            'umrah_list',
            'visa_countries',
            'visa_apply',
            'flights_list',
            'flight_quote',
            'blog_list',
        ]

    def location(self, item):
        return reverse(item)


class PackageSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Package.objects.all().order_by('-created_at')

    def location(self, item):
        return reverse('package_detail', kwargs={'pk': item.pk})

    def lastmod(self, item):
        return item.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(status='published').order_by('-published_at')

    def location(self, item):
        return reverse('blog_detail', kwargs={'slug': item.slug})

    def lastmod(self, item):
        return item.updated_at
