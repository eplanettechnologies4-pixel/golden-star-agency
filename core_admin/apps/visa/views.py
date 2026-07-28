from django.shortcuts import render
from .models import VisaPackage

def visa_countries_view(request):
    visa_packages = VisaPackage.objects.all().order_by('-is_popular', '-created_at')
    return render(request, 'visa/country_list.html', {'visa_packages': visa_packages})
