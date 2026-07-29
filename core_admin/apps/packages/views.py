import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apps.packages.models import Package
from apps.blog.admin_views import admin_required_api

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


# ══════════════════════════════════════════════════════════════════════
# B2C ADMIN PANEL PACKAGES CRUD REST APIS
# ══════════════════════════════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_packages_list_api(request):
    """
    GET /dashboard/admin/api/packages/
    Returns list of all Package records for B2C Admin Panel.
    """
    packages = Package.objects.all().order_by('-created_at')
    data = []
    for pkg in packages:
        data.append({
            'id': pkg.id,
            'title': pkg.title,
            'category': pkg.category,
            'price': float(pkg.price),
            'duration_days': pkg.duration_days,
            'available_seats': pkg.available_seats,
            'total_seats': pkg.total_seats,
            'makkah_hotel_name': pkg.makkah_hotel_name or 'Anjum Hotel Makkah',
            'makkah_hotel_distance': pkg.makkah_hotel_distance or '350m from Haram',
            'madinah_hotel_name': pkg.madinah_hotel_name or 'Pullman Zamzam Madinah',
            'madinah_hotel_distance': pkg.madinah_hotel_distance or '150m from Prophet\'s Mosque',
            'airline': pkg.airline or 'Saudi Airlines',
            'flight_routes': pkg.flight_routes or 'KHI - JED - MED - KHI',
            'flight_route_type': pkg.flight_route_type or 'direct',
            'price_sharing': float(pkg.price_sharing),
            'price_quad': float(pkg.price_quad),
            'price_triple': float(pkg.price_triple),
            'price_double': float(pkg.price_double),
            'price_child': float(pkg.price_child),
            'price_infant': float(pkg.price_infant),
            'discount_percentage': float(pkg.discount_percentage),
            'description': pkg.description or '',
            'created_at': pkg.created_at.strftime('%Y-%m-%d')
        })
    
    return JsonResponse({
        'success': True,
        'packages': data,
        'data': data,
        'total_count': len(data),
        'umrah_count': packages.filter(category__iexact='umrah').count(),
        'hajj_count': packages.filter(category__iexact='hajj').count(),
        'tour_count': packages.filter(category__iexact='tour').count()
    })


@csrf_exempt
@admin_required_api
def admin_package_detail_api(request, pk):
    """
    GET  /dashboard/admin/api/packages/<pk>/ -> Fetch single package details for editing
    POST /dashboard/admin/api/packages/<pk>/ -> Update package
    """
    pkg = get_object_or_404(Package, pk=pk)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'package': {
                'id': pkg.id,
                'title': pkg.title,
                'category': pkg.category,
                'price': float(pkg.price),
                'price_sharing': float(pkg.price_sharing),
                'price_quad':    float(pkg.price_quad),
                'price_triple':  float(pkg.price_triple),
                'price_double':  float(pkg.price_double),
                'price_child':   float(pkg.price_child),
                'price_infant':  float(pkg.price_infant),
                'discount_percentage': float(pkg.discount_percentage),
                'duration_days': pkg.duration_days,
                'available_seats': pkg.available_seats,
                'total_seats': pkg.total_seats,
                'makkah_hotel_name': pkg.makkah_hotel_name or '',
                'makkah_hotel_distance': pkg.makkah_hotel_distance or '',
                'madinah_hotel_name': pkg.madinah_hotel_name or '',
                'madinah_hotel_distance': pkg.madinah_hotel_distance or '',
                'airline': pkg.airline or '',
                'flight_routes': pkg.flight_routes or '',
                'flight_route_type': pkg.flight_route_type or 'direct',
                'meal_detail': pkg.meal_detail or 'Full Board',
                'transport_type': pkg.transport_type or 'Sharing',
                'luggage_weight': pkg.luggage_weight or '20 kg + 7 kg Hand Carry',
                'description': pkg.description or ''
            }
        })
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        pkg.title = (body.get('title') or pkg.title).strip()
        pkg.category = (body.get('category') or pkg.category).strip().lower()
        if body.get('price')         is not None: pkg.price          = float(body['price'])
        if body.get('price_sharing') is not None: pkg.price_sharing  = float(body['price_sharing'])
        if body.get('price_quad')    is not None: pkg.price_quad     = float(body['price_quad'])
        if body.get('price_triple')  is not None: pkg.price_triple   = float(body['price_triple'])
        if body.get('price_double')  is not None: pkg.price_double   = float(body['price_double'])
        if body.get('price_child')   is not None: pkg.price_child    = float(body['price_child'])
        if body.get('price_infant')  is not None: pkg.price_infant   = float(body['price_infant'])
        if body.get('discount_percentage') is not None: pkg.discount_percentage = float(body['discount_percentage'])
        if body.get('duration_days'): pkg.duration_days = int(body['duration_days'])
        if body.get('total_seats'):   pkg.total_seats   = int(body['total_seats'])
        if body.get('available_seats'): pkg.available_seats = int(body['available_seats'])
        if body.get('makkah_hotel_name'):     pkg.makkah_hotel_name     = body['makkah_hotel_name']
        if body.get('makkah_hotel_distance'): pkg.makkah_hotel_distance = body['makkah_hotel_distance']
        if body.get('madinah_hotel_name'):    pkg.madinah_hotel_name    = body['madinah_hotel_name']
        if body.get('madinah_hotel_distance'):pkg.madinah_hotel_distance= body['madinah_hotel_distance']
        if body.get('airline'):          pkg.airline          = body['airline']
        if body.get('flight_routes'):    pkg.flight_routes    = body['flight_routes']
        if body.get('flight_route_type'): pkg.flight_route_type = body['flight_route_type']
        if body.get('meal_detail'):      pkg.meal_detail      = body['meal_detail']
        if body.get('transport_type'):   pkg.transport_type   = body['transport_type']
        if body.get('luggage_weight'):   pkg.luggage_weight   = body['luggage_weight']
        if body.get('description') is not None: pkg.description = body['description']
        
        pkg.save()
        return JsonResponse({'success': True, 'message': 'Package updated successfully.'})


@csrf_exempt
@admin_required_api
def admin_package_create_api(request):
    """
    POST /dashboard/admin/api/packages/create/
    Creates a new Package.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)
        
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    title = (body.get('title') or '').strip()
    if not title:
        return JsonResponse({'success': False, 'message': 'Package title is required.'}, status=400)

    category = (body.get('category') or 'umrah').strip().lower()
    price = float(body.get('price') or 210000)
    duration_days = int(body.get('duration_days') or 15)
    total_seats = int(body.get('total_seats') or 30)

    pkg = Package.objects.create(
        title=title,
        category=category,
        price=price,
        price_sharing=float(body.get('price_sharing') or price),
        price_quad=float(body.get('price_quad')    or price + 35000),
        price_triple=float(body.get('price_triple') or price + 65000),
        price_double=float(body.get('price_double') or price + 110000),
        price_child=float(body.get('price_child')  or 180000),
        price_infant=float(body.get('price_infant') or 65000),
        discount_percentage=float(body.get('discount_percentage') or 0),
        duration_days=duration_days,
        total_seats=total_seats,
        available_seats=total_seats,
        makkah_hotel_name=body.get('makkah_hotel_name') or 'Anjum Hotel Makkah',
        makkah_hotel_distance=body.get('makkah_hotel_distance') or '350m from Haram',
        madinah_hotel_name=body.get('madinah_hotel_name') or 'Pullman Zamzam Madinah',
        madinah_hotel_distance=body.get('madinah_hotel_distance') or "150m from Prophet's Mosque",
        airline=body.get('airline') or 'Saudi Airlines',
        flight_routes=body.get('flight_routes') or 'KHI - JED - MED - KHI',
        flight_route_type=body.get('flight_route_type') or 'direct',
        meal_detail=body.get('meal_detail') or 'Full Board',
        transport_type=body.get('transport_type') or 'Sharing',
        luggage_weight=body.get('luggage_weight') or '20 kg + 7 kg Hand Carry',
        description=body.get('description') or 'Premium package with complete Hajj & Umrah services.'
    )

    return JsonResponse({'success': True, 'message': f'Package "{pkg.title}" created successfully.', 'id': pkg.id})


@csrf_exempt
@admin_required_api
def admin_package_delete_api(request, pk):
    """
    POST /dashboard/admin/api/packages/<pk>/delete/
    Deletes a package permanently.
    """
    pkg = get_object_or_404(Package, pk=pk)
    pkg.delete()
    return JsonResponse({'success': True, 'message': 'Package deleted successfully.'})
