from django.shortcuts import render, get_object_or_404
from apps.packages.models import Package

def umrah_list_view(request):
    # Fetch all Umrah packages dynamically from database
    packages = Package.objects.filter(category__iexact='umrah').order_by('-created_at')
    if not packages.exists():
        packages = Package.objects.all().order_by('-created_at')
    return render(request, 'packages/umrah_list.html', {'packages': packages})

def hajj_list_view(request):
    # Fetch all Hajj packages dynamically from database
    packages = Package.objects.filter(category__iexact='hajj').order_by('-created_at')
    if not packages.exists():
        packages = Package.objects.all().order_by('-created_at')
    return render(request, 'packages/hajj_list.html', {'packages': packages})

def package_detail_view(request, pk):
    # Fetch specific package detail dynamically
    package = get_object_or_404(Package, pk=pk)
    related_packages = Package.objects.exclude(pk=pk).order_by('-created_at')[:3]
    return render(request, 'packages/package_detail.html', {
        'package': package,
        'related_packages': related_packages
    })
