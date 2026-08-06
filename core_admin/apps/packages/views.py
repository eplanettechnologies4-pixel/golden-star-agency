import os
import uuid
import json
from datetime import datetime, date
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from apps.packages.models import Package, HajjPackage, HajjAccommodation
from apps.airline_ticketing.models import Hotel
from apps.blog.admin_views import admin_required_api


def _safe_parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%b %d, %Y', '%d %b %Y'):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
    return None


def _safe_format_date(val, fmt='%Y-%m-%d'):
    if not val:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime(fmt)
    if isinstance(val, str):
        parsed = _safe_parse_date(val)
        if parsed and hasattr(parsed, 'strftime'):
            return parsed.strftime(fmt)
        return val
    return str(val)


def _safe_float_or_none(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str in ('0', '0.0', 'null', 'None', 'none'):
        return None
    try:
        f = float(val_str)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def umrah_list_view(request):
    # Fetch only Umrah packages dynamically from database for website Umrah page
    packages = Package.objects.filter(category__iexact='umrah').order_by('-created_at')
    return render(request, 'packages/umrah_list.html', {'packages': packages})

def hajj_list_view(request):
    # Fetch standalone Hajj packages dynamically from HajjPackage model
    hajj_packages = HajjPackage.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'packages/hajj_list.html', {'packages': hajj_packages, 'hajj_packages': hajj_packages})

def hajj_detail_view(request, pk):
    # Fetch standalone Hajj package detail
    hajj_package = get_object_or_404(HajjPackage, pk=pk)
    accommodations = hajj_package.accommodations.all().select_related('hotel')
    related_packages = HajjPackage.objects.filter(is_active=True).exclude(pk=pk).order_by('-created_at')[:3]
    return render(request, 'packages/hajj_detail.html', {
        'hajj_package': hajj_package,
        'package': hajj_package,
        'accommodations': accommodations,
        'related_packages': related_packages
    })

def package_detail_view(request, pk):
    # Fetch specific package detail dynamically
    package = get_object_or_404(Package, pk=pk)
    related_packages = Package.objects.exclude(pk=pk).order_by('-created_at')[:3]
    return render(request, 'packages/package_detail.html', {
        'package': package,
        'related_packages': related_packages
    })


def _handle_hotel_images_upload(request, file_key, folder_name, existing_images=None):
    """
    Saves uploaded files under request.FILES for `file_key` and merges with existing/new URL lists.
    """
    images_list = list(existing_images) if isinstance(existing_images, list) else []
    
    # 1. Process uploaded files from request.FILES
    files = request.FILES.getlist(file_key)
    if files:
        target_dir = os.path.join(settings.MEDIA_ROOT, 'packages', 'hotels', folder_name)
        os.makedirs(target_dir, exist_ok=True)
        fs = FileSystemStorage(location=target_dir)
        for f in files:
            ext = os.path.splitext(f.name)[1].lower() or '.jpg'
            filename = f"{uuid.uuid4().hex[:10]}{ext}"
            saved_name = fs.save(filename, f)
            url_path = f"{settings.MEDIA_URL}packages/hotels/{folder_name}/{saved_name}"
            if url_path not in images_list:
                images_list.append(url_path)

    # 2. Process URL strings passed via form input
    urls_raw = request.POST.get(f"{file_key}_urls") or request.POST.get(file_key)
    if urls_raw and isinstance(urls_raw, str):
        try:
            parsed = json.loads(urls_raw)
            if isinstance(parsed, list):
                for u in parsed:
                    if isinstance(u, str) and u.strip() and u.strip() not in images_list:
                        images_list.append(u.strip())
        except Exception:
            for u in urls_raw.split(','):
                if u.strip() and u.strip() not in images_list:
                    images_list.append(u.strip())

    return images_list


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
        makkah_imgs = pkg.makkah_hotel_images if isinstance(pkg.makkah_hotel_images, list) else []
        madinah_imgs = pkg.madinah_hotel_images if isinstance(pkg.madinah_hotel_images, list) else []
        gallery_imgs = pkg.images if isinstance(pkg.images, list) else []
        
        data.append({
            'id': pkg.id,
            'title': pkg.title,
            'category': pkg.category,
            'is_featured': pkg.is_featured,
            'cover_url': pkg.cover_url,
            'price': float(pkg.price) if pkg.price else 0.0,
            'min_available_price': float(pkg.min_available_price),
            'duration_days': pkg.duration_days,
            'available_seats': pkg.available_seats,
            'total_seats': pkg.total_seats,
            'makkah_hotel_name': pkg.makkah_hotel_name or 'Anjum Hotel Makkah',
            'makkah_hotel_distance': pkg.makkah_hotel_distance or '350m from Haram',
            'makkah_hotel_images': makkah_imgs,
            'makkah_nights': pkg.makkah_nights or 7,
            'madinah_hotel_name': pkg.madinah_hotel_name or 'Pullman Zamzam Madinah',
            'madinah_hotel_distance': pkg.madinah_hotel_distance or '150m from Prophet\'s Mosque',
            'madinah_hotel_images': madinah_imgs,
            'madinah_nights': pkg.madinah_nights or 7,
            'images': gallery_imgs,
            'all_hotel_images': pkg.get_all_hotel_and_package_images(),
            'airline': pkg.airline or 'Saudi Airlines',
            'airline_logo': pkg.airline_logo or (pkg.get_airline_info().get('logo_url') if pkg.get_airline_info() else None),
            'flight_routes': pkg.flight_routes or 'KHI - JED - MED - KHI',
            'flight_route_type': pkg.flight_route_type or 'direct',
            'sectors_data': pkg.sectors_data if isinstance(pkg.sectors_data, list) else [],
            'sectors_info': pkg.get_sectors_list(),
            'flight_dates': pkg.flight_dates or '',
            'departure_date': _safe_format_date(pkg.departure_date, '%Y-%m-%d'),
            'return_date': _safe_format_date(pkg.return_date, '%Y-%m-%d'),
            'price_sharing': float(pkg.price_sharing) if pkg.price_sharing is not None else None,
            'price_quad': float(pkg.price_quad) if pkg.price_quad is not None else None,
            'price_triple': float(pkg.price_triple) if pkg.price_triple is not None else None,
            'price_double': float(pkg.price_double) if pkg.price_double is not None else None,
            'price_child': float(pkg.price_child) if pkg.price_child is not None else None,
            'price_child_with_bed': float(pkg.price_child_with_bed) if pkg.price_child_with_bed is not None else None,
            'price_child_no_bed': float(pkg.price_child_no_bed) if pkg.price_child_no_bed is not None else None,
            'price_infant': float(pkg.price_infant) if pkg.price_infant is not None else None,
            'discount_percentage': float(pkg.discount_percentage) if pkg.discount_percentage else 0.0,
            'description': pkg.description or '',
            'created_at': _safe_format_date(pkg.created_at, '%Y-%m-%d'),
            'addons': pkg.addons if isinstance(pkg.addons, list) else [],
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
        makkah_imgs = pkg.makkah_hotel_images if isinstance(pkg.makkah_hotel_images, list) else []
        madinah_imgs = pkg.madinah_hotel_images if isinstance(pkg.madinah_hotel_images, list) else []
        gallery_imgs = pkg.images if isinstance(pkg.images, list) else []
        
        return JsonResponse({
            'success': True,
            'package': {
                'id': pkg.id,
                'title': pkg.title,
                'category': pkg.category,
                'is_featured': pkg.is_featured,
                'cover_url': pkg.cover_url,
                'price': float(pkg.price) if pkg.price else 0.0,
                'min_available_price': float(pkg.min_available_price),
                'price_sharing': float(pkg.price_sharing) if pkg.price_sharing is not None else None,
                'price_quad':    float(pkg.price_quad) if pkg.price_quad is not None else None,
                'price_triple':  float(pkg.price_triple) if pkg.price_triple is not None else None,
                'price_double':  float(pkg.price_double) if pkg.price_double is not None else None,
                'price_child':   float(pkg.price_child) if pkg.price_child is not None else None,
                'price_child_with_bed': float(pkg.price_child_with_bed) if pkg.price_child_with_bed is not None else None,
                'price_child_no_bed': float(pkg.price_child_no_bed) if pkg.price_child_no_bed is not None else None,
                'price_infant':  float(pkg.price_infant) if pkg.price_infant is not None else None,
                'discount_percentage': float(pkg.discount_percentage) if pkg.discount_percentage else 0.0,
                'duration_days': pkg.duration_days,
                'available_seats': pkg.available_seats,
                'total_seats': pkg.total_seats,
                'makkah_hotel_name': pkg.makkah_hotel_name or '',
                'makkah_hotel_distance': pkg.makkah_hotel_distance or '',
                'makkah_hotel_images': makkah_imgs,
                'makkah_nights': pkg.makkah_nights or 7,
                'madinah_hotel_name': pkg.madinah_hotel_name or '',
                'madinah_hotel_distance': pkg.madinah_hotel_distance or '',
                'madinah_hotel_images': madinah_imgs,
                'madinah_nights': pkg.madinah_nights or 7,
                'images': gallery_imgs,
                'all_hotel_images': pkg.get_all_hotel_and_package_images(),
                'airline': pkg.airline or '',
                'airline_logo': pkg.airline_logo or (pkg.get_airline_info().get('logo_url') if pkg.get_airline_info() else None),
                'flight_routes': pkg.flight_routes or '',
                'flight_route_type': pkg.flight_route_type or 'direct',
                'sectors_data': pkg.sectors_data if isinstance(pkg.sectors_data, list) else [],
                'sectors_info': pkg.get_sectors_list(),
                'flight_dates': pkg.flight_dates or '',
                'departure_date': _safe_format_date(pkg.departure_date, '%Y-%m-%d'),
                'return_date': _safe_format_date(pkg.return_date, '%Y-%m-%d'),
                'meal_detail': pkg.meal_detail or 'Full Board',
                'transport_type': pkg.transport_type or 'Sharing',
                'luggage_weight': pkg.luggage_weight or '20 kg + 7 kg Hand Carry',
                'description': pkg.description or '',
                'addons': pkg.addons if isinstance(pkg.addons, list) else [],
            }
        })
    
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        pkg.title = (body.get('title') or request.POST.get('title') or pkg.title).strip()
        pkg.category = (body.get('category') or request.POST.get('category') or pkg.category).strip().lower()
        
        if 'is_featured' in body or 'is_featured' in request.POST:
            feat_val = body.get('is_featured') if 'is_featured' in body else request.POST.get('is_featured')
            pkg.is_featured = str(feat_val).lower() in ('true', '1', 'on', 'yes')
        
        if 'cover_image' in request.FILES:
            pkg.cover_image = request.FILES['cover_image']

        # Process uploaded / provided Makkah Hotel Images
        if 'makkah_hotel_images' in request.FILES or 'makkah_hotel_images' in request.POST or 'makkah_hotel_images_urls' in request.POST:
            pkg.makkah_hotel_images = _handle_hotel_images_upload(request, 'makkah_hotel_images', 'makkah', pkg.makkah_hotel_images)

        # Process uploaded / provided Madinah Hotel Images
        if 'madinah_hotel_images' in request.FILES or 'madinah_hotel_images' in request.POST or 'madinah_hotel_images_urls' in request.POST:
            pkg.madinah_hotel_images = _handle_hotel_images_upload(request, 'madinah_hotel_images', 'madinah', pkg.madinah_hotel_images)

        p_val = body.get('price') or request.POST.get('price')
        if p_val is not None: pkg.price = float(p_val) if float(p_val) > 0 else 210000.0
        
        if 'price_sharing' in body or 'price_sharing' in request.POST:
            pkg.price_sharing = _safe_float_or_none(body.get('price_sharing') if 'price_sharing' in body else request.POST.get('price_sharing'))

        if 'price_quad' in body or 'price_quad' in request.POST:
            pkg.price_quad = _safe_float_or_none(body.get('price_quad') if 'price_quad' in body else request.POST.get('price_quad'))

        if 'price_triple' in body or 'price_triple' in request.POST:
            pkg.price_triple = _safe_float_or_none(body.get('price_triple') if 'price_triple' in body else request.POST.get('price_triple'))

        if 'price_double' in body or 'price_double' in request.POST:
            pkg.price_double = _safe_float_or_none(body.get('price_double') if 'price_double' in body else request.POST.get('price_double'))

        if 'price_child' in body or 'price_child' in request.POST:
            pkg.price_child = _safe_float_or_none(body.get('price_child') if 'price_child' in body else request.POST.get('price_child'))

        if 'price_child_with_bed' in body or 'price_child_with_bed' in request.POST:
            pkg.price_child_with_bed = _safe_float_or_none(body.get('price_child_with_bed') if 'price_child_with_bed' in body else request.POST.get('price_child_with_bed'))

        if 'price_child_no_bed' in body or 'price_child_no_bed' in request.POST:
            pkg.price_child_no_bed = _safe_float_or_none(body.get('price_child_no_bed') if 'price_child_no_bed' in body else request.POST.get('price_child_no_bed'))

        if 'price_infant' in body or 'price_infant' in request.POST:
            pkg.price_infant = _safe_float_or_none(body.get('price_infant') if 'price_infant' in body else request.POST.get('price_infant'))

        disc = body.get('discount_percentage') or request.POST.get('discount_percentage')
        if disc is not None: pkg.discount_percentage = float(disc)

        dur = body.get('duration_days') or request.POST.get('duration_days')
        if dur: pkg.duration_days = int(dur)

        t_seat = body.get('total_seats') or request.POST.get('total_seats')
        if t_seat: pkg.total_seats = int(t_seat)

        a_seat = body.get('available_seats') or request.POST.get('available_seats')
        if a_seat: pkg.available_seats = int(a_seat)

        m_hn = body.get('makkah_hotel_name') or request.POST.get('makkah_hotel_name')
        if m_hn: pkg.makkah_hotel_name = m_hn

        m_hd = body.get('makkah_hotel_distance') or request.POST.get('makkah_hotel_distance')
        if m_hd: pkg.makkah_hotel_distance = m_hd

        m_n = body.get('makkah_nights') or request.POST.get('makkah_nights')
        if m_n is not None and str(m_n).isdigit(): pkg.makkah_nights = int(m_n)

        md_hn = body.get('madinah_hotel_name') or request.POST.get('madinah_hotel_name')
        if md_hn: pkg.madinah_hotel_name = md_hn

        md_hd = body.get('madinah_hotel_distance') or request.POST.get('madinah_hotel_distance')
        if md_hd: pkg.madinah_hotel_distance = md_hd

        md_n = body.get('madinah_nights') or request.POST.get('madinah_nights')
        if md_n is not None and str(md_n).isdigit(): pkg.madinah_nights = int(md_n)

        air = body.get('airline') or request.POST.get('airline')
        if air: pkg.airline = air

        fr = body.get('flight_routes') or request.POST.get('flight_routes')
        if fr: pkg.flight_routes = fr

        frt = body.get('flight_route_type') or request.POST.get('flight_route_type')
        if frt: pkg.flight_route_type = frt

        if 'sectors_data' in body or 'sectors_data' in request.POST:
            sec_raw = body.get('sectors_data') if 'sectors_data' in body else request.POST.get('sectors_data')
            if isinstance(sec_raw, str):
                try:
                    sec_raw = json.loads(sec_raw)
                except Exception:
                    sec_raw = []
            if isinstance(sec_raw, list):
                pkg.sectors_data = [str(s).strip().upper() for s in sec_raw if str(s).strip()]

        if 'departure_date' in body or 'departure_date' in request.POST:
            dep = body.get('departure_date') if 'departure_date' in body else request.POST.get('departure_date')
            pkg.departure_date = _safe_parse_date(dep)
            
        if 'return_date' in body or 'return_date' in request.POST:
            ret = body.get('return_date') if 'return_date' in body else request.POST.get('return_date')
            pkg.return_date = _safe_parse_date(ret)

        md = body.get('meal_detail') or request.POST.get('meal_detail')
        if md: pkg.meal_detail = md

        tt = body.get('transport_type') or request.POST.get('transport_type')
        if tt: pkg.transport_type = tt

        lw = body.get('luggage_weight') or request.POST.get('luggage_weight')
        if lw: pkg.luggage_weight = lw

        desc = body.get('description') if 'description' in body else request.POST.get('description')
        if desc is not None: pkg.description = desc

        if 'addons' in body or 'addons' in request.POST:
            addons_raw = body.get('addons') if 'addons' in body else request.POST.get('addons')
            if isinstance(addons_raw, str):
                try:
                    addons_raw = json.loads(addons_raw)
                except Exception:
                    addons_raw = []
            pkg.addons = [{'name': a['name'], 'price': int(a.get('price', 0))} for a in (addons_raw or []) if isinstance(a, dict) and a.get('name', '').strip()]
        
        # Handle gallery images upload / update
        gallery_imgs = list(pkg.images or [])
        if 'images' in body or 'images_urls' in body or 'images' in request.POST:
            raw_imgs = body.get('images') or body.get('images_urls') or request.POST.get('images')
            if isinstance(raw_imgs, str):
                try: raw_imgs = json.loads(raw_imgs)
                except Exception: raw_imgs = [u.strip() for u in raw_imgs.split(',') if u.strip()]
            if isinstance(raw_imgs, list):
                gallery_imgs = [str(u).strip() for u in raw_imgs if str(u).strip()]

        for key in ('images_files', 'gallery_images', 'images'):
            if key in request.FILES:
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'packages', 'gallery')
                os.makedirs(upload_dir, exist_ok=True)
                for uploaded_file in request.FILES.getlist(key):
                    safe_name = f"pkg_{pkg.id}_{uploaded_file.name[-25:].replace(' ', '_')}"
                    file_path = os.path.join(upload_dir, safe_name)
                    with open(file_path, 'wb+') as dest:
                        for chunk in uploaded_file.chunks():
                            dest.write(chunk)
                    gallery_url = f"{settings.MEDIA_URL}packages/gallery/{safe_name}"
                    if gallery_url not in gallery_imgs:
                        gallery_imgs.append(gallery_url)
        pkg.images = gallery_imgs

        pkg.save()
        return JsonResponse({
            'success': True,
            'message': 'Package updated successfully.',
            'cover_url': pkg.cover_url,
            'airline_logo': pkg.airline_logo,
            'images': pkg.images,
            'makkah_hotel_images': pkg.makkah_hotel_images,
            'madinah_hotel_images': pkg.madinah_hotel_images
        })


@csrf_exempt
@admin_required_api
def admin_package_create_api(request):
    """
    POST /dashboard/admin/api/packages/create/
    Creates a new Package with optional Cover, Airline Logo & Hotel Images upload.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)
        
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    title = (body.get('title') or request.POST.get('title') or '').strip()
    if not title:
        return JsonResponse({'success': False, 'message': 'Package title is required.'}, status=400)

    category = (body.get('category') or request.POST.get('category') or 'umrah').strip().lower()
    price = float(body.get('price') or request.POST.get('price') or 210000)
    duration_days = int(body.get('duration_days') or request.POST.get('duration_days') or 15)
    total_seats = int(body.get('total_seats') or request.POST.get('total_seats') or 30)

    feat_val = body.get('is_featured') if 'is_featured' in body else request.POST.get('is_featured')
    is_featured = str(feat_val).lower() in ('true', '1', 'on', 'yes')

    addons_raw = body.get('addons') if 'addons' in body else request.POST.get('addons')
    if isinstance(addons_raw, str):
        try:
            addons_raw = json.loads(addons_raw)
        except Exception:
            addons_raw = []

    sectors_raw = body.get('sectors_data') if 'sectors_data' in body else request.POST.get('sectors_data')
    if isinstance(sectors_raw, str):
        try:
            sectors_raw = json.loads(sectors_raw)
        except Exception:
            sectors_raw = []
    clean_sectors = [str(s).strip().upper() for s in (sectors_raw or []) if str(s).strip()]

    makkah_imgs = _handle_hotel_images_upload(request, 'makkah_hotel_images', 'makkah', [])
    madinah_imgs = _handle_hotel_images_upload(request, 'madinah_hotel_images', 'madinah', [])

    pkg = Package.objects.create(
        title=title,
        category=category,
        is_featured=is_featured,
        price=price,
        price_sharing=_safe_float_or_none(body.get('price_sharing') or request.POST.get('price_sharing')),
        price_quad=_safe_float_or_none(body.get('price_quad') or request.POST.get('price_quad')),
        price_triple=_safe_float_or_none(body.get('price_triple') or request.POST.get('price_triple')),
        price_double=_safe_float_or_none(body.get('price_double') or request.POST.get('price_double')),
        price_child=_safe_float_or_none(body.get('price_child') or request.POST.get('price_child')),
        price_child_with_bed=_safe_float_or_none(body.get('price_child_with_bed') or request.POST.get('price_child_with_bed')),
        price_child_no_bed=_safe_float_or_none(body.get('price_child_no_bed') or request.POST.get('price_child_no_bed')),
        price_infant=_safe_float_or_none(body.get('price_infant') or request.POST.get('price_infant')),
        discount_percentage=float(body.get('discount_percentage') or request.POST.get('discount_percentage') or 0),
        duration_days=duration_days,
        total_seats=total_seats,
        available_seats=int(body.get('available_seats') or request.POST.get('available_seats') or total_seats),
        makkah_hotel_name=body.get('makkah_hotel_name') or request.POST.get('makkah_hotel_name') or 'Anjum Hotel Makkah',
        makkah_hotel_distance=body.get('makkah_hotel_distance') or request.POST.get('makkah_hotel_distance') or '350m from Haram',
        makkah_hotel_images=makkah_imgs,
        makkah_nights=int(body.get('makkah_nights') or request.POST.get('makkah_nights') or 7),
        madinah_hotel_name=body.get('madinah_hotel_name') or request.POST.get('madinah_hotel_name') or 'Pullman Zamzam Madinah',
        madinah_hotel_distance=body.get('madinah_hotel_distance') or request.POST.get('madinah_hotel_distance') or "150m from Prophet's Mosque",
        madinah_hotel_images=madinah_imgs,
        madinah_nights=int(body.get('madinah_nights') or request.POST.get('madinah_nights') or 7),
        airline=body.get('airline') or request.POST.get('airline') or 'Saudi Airlines',
        flight_routes=body.get('flight_routes') or request.POST.get('flight_routes') or 'KHI - JED - MED - KHI',
        flight_route_type=body.get('flight_route_type') or request.POST.get('flight_route_type') or 'direct',
        sectors_data=clean_sectors,
        flight_dates=body.get('flight_dates') or request.POST.get('flight_dates') or '15 Aug 2026 - 30 Aug 2026',
        departure_date=(body.get('departure_date') or request.POST.get('departure_date') or '').strip() or None,
        return_date=(body.get('return_date') or request.POST.get('return_date') or '').strip() or None,
        meal_detail=body.get('meal_detail') or request.POST.get('meal_detail') or 'Full Board',
        transport_type=body.get('transport_type') or request.POST.get('transport_type') or 'Sharing',
        luggage_weight=body.get('luggage_weight') or request.POST.get('luggage_weight') or '20 kg + 7 kg Hand Carry',
        description=body.get('description') or request.POST.get('description') or 'Premium package with complete Hajj & Umrah services.',
        addons=[{'name': a['name'], 'price': int(a.get('price', 0))} for a in (addons_raw or []) if isinstance(a, dict) and a.get('name', '').strip()]
    )

    if 'cover_image' in request.FILES:
        pkg.cover_image = request.FILES['cover_image']
        pkg.save()

    if 'airline_logo' in request.FILES:
        logo_file = request.FILES['airline_logo']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'packages', 'airlines'), base_url=settings.MEDIA_URL + 'packages/airlines/')
        filename = fs.save(logo_file.name, logo_file)
        pkg.airline_logo = fs.url(filename)
        pkg.save()
    elif body.get('airline_logo') or request.POST.get('airline_logo'):
        logo_val = (body.get('airline_logo') or request.POST.get('airline_logo')).strip()
        if logo_val:
            pkg.airline_logo = logo_val
            pkg.save()

    # Handle uploaded gallery images
    gallery_imgs = []
    for key in ('images_files', 'gallery_images', 'images'):
        if key in request.FILES:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'packages', 'gallery')
            os.makedirs(upload_dir, exist_ok=True)
            for uploaded_file in request.FILES.getlist(key):
                safe_name = f"pkg_{pkg.id}_{uploaded_file.name[-25:].replace(' ', '_')}"
                file_path = os.path.join(upload_dir, safe_name)
                with open(file_path, 'wb+') as dest:
                    for chunk in uploaded_file.chunks():
                        dest.write(chunk)
                gallery_url = f"{settings.MEDIA_URL}packages/gallery/{safe_name}"
                if gallery_url not in gallery_imgs:
                    gallery_imgs.append(gallery_url)
    if gallery_imgs:
        pkg.images = gallery_imgs
        pkg.save()

    return JsonResponse({
        'success': True,
        'message': f'Package "{pkg.title}" created successfully.',
        'id': pkg.id,
        'cover_url': pkg.cover_url,
        'airline_logo': pkg.airline_logo,
        'images': pkg.images,
        'makkah_hotel_images': pkg.makkah_hotel_images,
        'madinah_hotel_images': pkg.madinah_hotel_images
    })


@csrf_exempt
@admin_required_api
def admin_package_toggle_featured_api(request, pk):
    """
    POST /dashboard/admin/api/packages/<pk>/toggle-featured/
    Toggles the is_featured status of a Package.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)
    pkg = get_object_or_404(Package, pk=pk)
    pkg.is_featured = not pkg.is_featured
    pkg.save()
    return JsonResponse({
        'success': True,
        'message': f'Package "{pkg.title}" is_featured set to {pkg.is_featured}.',
        'is_featured': pkg.is_featured
    })


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


# ══════════════════════════════════════════════════════════════════════
# STANDALONE HAJJ PACKAGES ADMIN REST APIS
# ══════════════════════════════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_hajj_packages_api(request):
    """
    GET  /dashboard/admin/api/hajj-packages/ -> List all HajjPackage records
    POST /dashboard/admin/api/hajj-packages/ -> Create new HajjPackage with accommodations
    """
    if request.method == 'GET':
        pkgs = HajjPackage.objects.all().order_by('-created_at')
        data = []
        for p in pkgs:
            accommodations_data = []
            for acc in p.accommodations.all().select_related('hotel'):



                
                accommodations_data.append({
                    'id': acc.id,
                    'city': acc.city,
                    'city_display': acc.get_city_display(),
                    'hotel_id': acc.hotel.id if acc.hotel else None,
                    'hotel_name': acc.get_hotel_name,
                    'hotel_distance': acc.get_hotel_distance,
                    'hotel_name_manual': acc.hotel_name_manual or '',
                    'distance_manual': acc.distance_manual or '',
                    'nights': acc.nights,
                    'order': acc.order
                })
            data.append({
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'logo_url': p.logo_url,
                'duration_days': p.duration_days,
                'airline_name': p.airline_name or 'Saudi Airlines',
                'airline_logo_url': p.get_airline_logo_url,
                'flight_dates': p.get_english_dates,
                'english_dates': p.get_english_dates,
                'hijri_dates': p.get_hijri_dates,
                'departure_date': p.departure_date.strftime('%Y-%m-%d') if p.departure_date else '',
                'return_date': p.return_date.strftime('%Y-%m-%d') if p.return_date else '',
                'price_quad': float(p.price_quad),
                'price_triple': float(p.price_triple),
                'price_double': float(p.price_double),
                'price_sharing': float(p.price_sharing) if p.price_sharing is not None else None,
                'starting_price': float(p.starting_price),
                'hajj_operator_name': p.hajj_operator_name,
                'license_number': p.license_number,
                'saudi_registration_number': p.saudi_registration_number,
                'total_seats': p.total_seats,
                'available_seats': p.available_seats,
                'images': p.images if isinstance(p.images, list) else [],
                'cover_photo': p.cover_photo.url if p.cover_photo else '',
                'cover_photo_url': p.cover_photo_url,
                'is_active': p.is_active,
                'accommodations': accommodations_data,
                'created_at': p.created_at.strftime('%Y-%m-%d'),
            })
        return JsonResponse({'success': True, 'hajj_packages': data, 'packages': data, 'total_count': len(data)})

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        title = (body.get('title') or request.POST.get('title') or '').strip()
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required.'}, status=400)

        description = body.get('description') or request.POST.get('description') or ''
        duration_days = int(body.get('duration_days') or request.POST.get('duration_days') or 15)

        airline_name = (body.get('airline_name') or request.POST.get('airline_name') or 'Saudi Airlines').strip()
        flight_dates = (body.get('flight_dates') or request.POST.get('flight_dates') or '').strip()
        hijri_dates = (body.get('hijri_dates') or request.POST.get('hijri_dates') or '').strip()
        dep_date_raw = body.get('departure_date') or request.POST.get('departure_date')
        ret_date_raw = body.get('return_date') or request.POST.get('return_date')
        departure_date = dep_date_raw if dep_date_raw and str(dep_date_raw).strip() != '' else None
        return_date = ret_date_raw if ret_date_raw and str(ret_date_raw).strip() != '' else None

        price_quad = float(body.get('price_quad') or request.POST.get('price_quad') or 0)
        price_triple = float(body.get('price_triple') or request.POST.get('price_triple') or 0)
        price_double = float(body.get('price_double') or request.POST.get('price_double') or 0)
        p_sharing = body.get('price_sharing') or request.POST.get('price_sharing')
        price_sharing = float(p_sharing) if p_sharing and str(p_sharing).strip() != '' else None

        hajj_operator_name = (body.get('hajj_operator_name') or request.POST.get('hajj_operator_name') or '').strip()
        license_number = (body.get('license_number') or request.POST.get('license_number') or '').strip()
        saudi_registration_number = (body.get('saudi_registration_number') or request.POST.get('saudi_registration_number') or '').strip()

        total_seats = int(body.get('total_seats') or request.POST.get('total_seats') or 30)
        available_seats = int(body.get('available_seats') or request.POST.get('available_seats') or total_seats)

        is_active_val = body.get('is_active') if 'is_active' in body else request.POST.get('is_active')
        is_active = str(is_active_val).lower() in ('true', '1', 'on', 'yes') if is_active_val is not None else True

        # Process gallery images
        images_list = []
        if 'images' in request.FILES:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'hajj', 'gallery'))
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'hajj', 'gallery'), exist_ok=True)
            for img_file in request.FILES.getlist('images'):
                filename = fs.save(f"{uuid.uuid4().hex[:10]}_{img_file.name}", img_file)
                images_list.append(f"{settings.MEDIA_URL}hajj/gallery/{filename}")

        urls_raw = body.get('images') if 'images' in body else request.POST.get('images_urls')
        if urls_raw:
            if isinstance(urls_raw, str):
                try:
                    urls_parsed = json.loads(urls_raw)
                    if isinstance(urls_parsed, list):
                        images_list.extend(urls_parsed)
                except Exception:
                    for u in urls_raw.split(','):
                        if u.strip(): images_list.append(u.strip())
            elif isinstance(urls_raw, list):
                images_list.extend(urls_raw)

        hajj_pkg = HajjPackage.objects.create(
            title=title,
            description=description,
            duration_days=duration_days,
            airline_name=airline_name,
            flight_dates=flight_dates,
            hijri_dates=hijri_dates,
            departure_date=departure_date,
            return_date=return_date,
            price_quad=price_quad,
            price_triple=price_triple,
            price_double=price_double,
            price_sharing=price_sharing,
            hajj_operator_name=hajj_operator_name,
            license_number=license_number,
            saudi_registration_number=saudi_registration_number,
            total_seats=total_seats,
            available_seats=available_seats,
            images=images_list,
            is_active=is_active
        )

        if 'company_logo' in request.FILES:
            hajj_pkg.company_logo = request.FILES['company_logo']
            hajj_pkg.save()

        if 'cover_photo' in request.FILES:
            hajj_pkg.cover_photo = request.FILES['cover_photo']
            hajj_pkg.save()

        if 'airline_logo' in request.FILES:
            hajj_pkg.airline_logo = request.FILES['airline_logo']
            hajj_pkg.save()

        # Handle nested accommodations
        accommodations_raw = body.get('accommodations') if 'accommodations' in body else request.POST.get('accommodations')
        if isinstance(accommodations_raw, str):
            try:
                accommodations_raw = json.loads(accommodations_raw)
            except Exception:
                accommodations_raw = []

        if isinstance(accommodations_raw, list):
            for idx, acc_item in enumerate(accommodations_raw):
                if isinstance(acc_item, dict):
                    hotel_id = acc_item.get('hotel_id')
                    hotel_inst = Hotel.objects.filter(pk=hotel_id).first() if hotel_id else None
                    h_name = (acc_item.get('hotel_name_manual') or acc_item.get('hotel_name') or (hotel_inst.name if hotel_inst else '')).strip()
                    h_dist = (acc_item.get('distance_manual') or acc_item.get('distance') or (hotel_inst.distance_from_haram if hotel_inst else '')).strip()
                    city_val = acc_item.get('city') or (hotel_inst.city if hotel_inst else 'makkah')

                    if h_name or hotel_inst:
                        HajjAccommodation.objects.create(
                            hajj_package=hajj_pkg,
                            city=city_val,
                            hotel=hotel_inst,
                            hotel_name_manual=h_name,
                            distance_manual=h_dist,
                            nights=int(acc_item.get('nights', 1)),
                            order=idx
                        )

        return JsonResponse({'success': True, 'message': 'Hajj Package created successfully.', 'id': hajj_pkg.id})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_hajj_package_detail_api(request, pk):
    """
    GET    /dashboard/admin/api/hajj-packages/<pk>/ -> Retrieve single HajjPackage
    POST   /dashboard/admin/api/hajj-packages/<pk>/ -> Update HajjPackage & replace accommodations
    DELETE /dashboard/admin/api/hajj-packages/<pk>/ -> Delete HajjPackage
    """
    hajj_pkg = get_object_or_404(HajjPackage, pk=pk)

    if request.method == 'GET':
        accommodations_data = []
        for acc in hajj_pkg.accommodations.all().select_related('hotel'):
            accommodations_data.append({
                'id': acc.id,
                'city': acc.city,
                'city_display': acc.get_city_display(),
                'hotel_id': acc.hotel.id if acc.hotel else None,
                'hotel_name': acc.get_hotel_name,
                'hotel_distance': acc.get_hotel_distance,
                'hotel_name_manual': acc.hotel_name_manual or '',
                'distance_manual': acc.distance_manual or '',
                'nights': acc.nights,
                'order': acc.order
            })
        return JsonResponse({
            'success': True,
            'hajj_package': {
                'id': hajj_pkg.id,
                'title': hajj_pkg.title,
                'description': hajj_pkg.description,
                'logo_url': hajj_pkg.logo_url,
                'duration_days': hajj_pkg.duration_days,
                'airline_name': hajj_pkg.airline_name or 'Saudi Airlines',
                'airline_logo_url': hajj_pkg.get_airline_logo_url,
                'flight_dates': hajj_pkg.flight_dates or '',
                'departure_date': _safe_format_date(hajj_pkg.departure_date, '%Y-%m-%d'),
                'return_date': _safe_format_date(hajj_pkg.return_date, '%Y-%m-%d'),
                'price_quad': float(hajj_pkg.price_quad),
                'price_triple': float(hajj_pkg.price_triple),
                'price_double': float(hajj_pkg.price_double),
                'price_sharing': float(hajj_pkg.price_sharing) if hajj_pkg.price_sharing is not None else None,
                'starting_price': float(hajj_pkg.starting_price),
                'hajj_operator_name': hajj_pkg.hajj_operator_name,
                'license_number': hajj_pkg.license_number,
                'saudi_registration_number': hajj_pkg.saudi_registration_number,
                'total_seats': hajj_pkg.total_seats,
                'available_seats': hajj_pkg.available_seats,
                'images': hajj_pkg.images if isinstance(hajj_pkg.images, list) else [],
                'cover_photo': hajj_pkg.cover_photo.url if hajj_pkg.cover_photo else '',
                'cover_photo_url': hajj_pkg.cover_photo_url,
                'is_active': hajj_pkg.is_active,
                'accommodations': accommodations_data,
                'created_at': _safe_format_date(hajj_pkg.created_at, '%Y-%m-%d'),
            }
        })

    elif request.method in ['POST', 'PUT', 'PATCH']:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        if 'title' in body or 'title' in request.POST:
            hajj_pkg.title = (body.get('title') or request.POST.get('title') or hajj_pkg.title).strip()
        if 'description' in body or 'description' in request.POST:
            hajj_pkg.description = body.get('description') if 'description' in body else request.POST.get('description')
        if 'duration_days' in body or 'duration_days' in request.POST:
            hajj_pkg.duration_days = int(body.get('duration_days') or request.POST.get('duration_days') or hajj_pkg.duration_days)

        if 'airline_name' in body or 'airline_name' in request.POST:
            hajj_pkg.airline_name = (body.get('airline_name') or request.POST.get('airline_name') or hajj_pkg.airline_name).strip()
        if 'flight_dates' in body or 'flight_dates' in request.POST:
            hajj_pkg.flight_dates = body.get('flight_dates') if 'flight_dates' in body else request.POST.get('flight_dates')
        if 'hijri_dates' in body or 'hijri_dates' in request.POST:
            hajj_pkg.hijri_dates = body.get('hijri_dates') if 'hijri_dates' in body else request.POST.get('hijri_dates')
        if 'departure_date' in body or 'departure_date' in request.POST:
            d_d = body.get('departure_date') if 'departure_date' in body else request.POST.get('departure_date')
            hajj_pkg.departure_date = _safe_parse_date(d_d)
        if 'return_date' in body or 'return_date' in request.POST:
            r_d = body.get('return_date') if 'return_date' in body else request.POST.get('return_date')
            hajj_pkg.return_date = _safe_parse_date(r_d)

        if 'price_quad' in body or 'price_quad' in request.POST:
            hajj_pkg.price_quad = float(body.get('price_quad') or request.POST.get('price_quad') or hajj_pkg.price_quad)
        if 'price_triple' in body or 'price_triple' in request.POST:
            hajj_pkg.price_triple = float(body.get('price_triple') or request.POST.get('price_triple') or hajj_pkg.price_triple)
        if 'price_double' in body or 'price_double' in request.POST:
            hajj_pkg.price_double = float(body.get('price_double') or request.POST.get('price_double') or hajj_pkg.price_double)
        if 'price_sharing' in body or 'price_sharing' in request.POST:
            p_sh = body.get('price_sharing') if 'price_sharing' in body else request.POST.get('price_sharing')
            hajj_pkg.price_sharing = float(p_sh) if p_sh and str(p_sh).strip() != '' else None

        if 'hajj_operator_name' in body or 'hajj_operator_name' in request.POST:
            hajj_pkg.hajj_operator_name = body.get('hajj_operator_name') if 'hajj_operator_name' in body else request.POST.get('hajj_operator_name')
        if 'license_number' in body or 'license_number' in request.POST:
            hajj_pkg.license_number = body.get('license_number') if 'license_number' in body else request.POST.get('license_number')
        if 'saudi_registration_number' in body or 'saudi_registration_number' in request.POST:
            hajj_pkg.saudi_registration_number = body.get('saudi_registration_number') if 'saudi_registration_number' in body else request.POST.get('saudi_registration_number')

        if 'total_seats' in body or 'total_seats' in request.POST:
            hajj_pkg.total_seats = int(body.get('total_seats') or request.POST.get('total_seats') or hajj_pkg.total_seats)
        if 'available_seats' in body or 'available_seats' in request.POST:
            hajj_pkg.available_seats = int(body.get('available_seats') or request.POST.get('available_seats') or hajj_pkg.available_seats)

        if 'is_active' in body or 'is_active' in request.POST:
            is_act = body.get('is_active') if 'is_active' in body else request.POST.get('is_active')
            hajj_pkg.is_active = str(is_act).lower() in ('true', '1', 'on', 'yes')

        if 'company_logo' in request.FILES:
            hajj_pkg.company_logo = request.FILES['company_logo']

        if 'cover_photo' in request.FILES:
            hajj_pkg.cover_photo = request.FILES['cover_photo']

        if 'airline_logo' in request.FILES:
            hajj_pkg.airline_logo = request.FILES['airline_logo']

        # Handle image updates
        images_list = list(hajj_pkg.images) if isinstance(hajj_pkg.images, list) else []
        if 'images' in request.FILES:
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'hajj', 'gallery'))
            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'hajj', 'gallery'), exist_ok=True)
            for img_file in request.FILES.getlist('images'):
                filename = fs.save(f"{uuid.uuid4().hex[:10]}_{img_file.name}", img_file)
                images_list.append(f"{settings.MEDIA_URL}hajj/gallery/{filename}")

        urls_raw = body.get('images') if 'images' in body else request.POST.get('images_urls')
        if urls_raw:
            if isinstance(urls_raw, str):
                try:
                    urls_parsed = json.loads(urls_raw)
                    if isinstance(urls_parsed, list):
                        images_list = urls_parsed
                except Exception:
                    pass
            elif isinstance(urls_raw, list):
                images_list = urls_raw
        hajj_pkg.images = images_list
        hajj_pkg.save()

        # Accommodations update (delete existing and recreate)
        if 'accommodations' in body or 'accommodations' in request.POST:
            accommodations_raw = body.get('accommodations') if 'accommodations' in body else request.POST.get('accommodations')
            if isinstance(accommodations_raw, str):
                try:
                    accommodations_raw = json.loads(accommodations_raw)
                except Exception:
                    accommodations_raw = None

            if isinstance(accommodations_raw, list):
                hajj_pkg.accommodations.all().delete()
                for idx, acc_item in enumerate(accommodations_raw):
                    if isinstance(acc_item, dict):
                        hotel_id = acc_item.get('hotel_id')
                        hotel_inst = Hotel.objects.filter(pk=hotel_id).first() if hotel_id else None
                        h_name = (acc_item.get('hotel_name_manual') or acc_item.get('hotel_name') or (hotel_inst.name if hotel_inst else '')).strip()
                        h_dist = (acc_item.get('distance_manual') or acc_item.get('distance') or (hotel_inst.distance_from_haram if hotel_inst else '')).strip()
                        city_val = acc_item.get('city') or (hotel_inst.city if hotel_inst else 'makkah')

                        if h_name or hotel_inst:
                            HajjAccommodation.objects.create(
                                hajj_package=hajj_pkg,
                                city=city_val,
                                hotel=hotel_inst,
                                hotel_name_manual=h_name,
                                distance_manual=h_dist,
                                nights=int(acc_item.get('nights', 1)),
                                order=idx
                            )

        return JsonResponse({'success': True, 'message': 'Hajj Package updated successfully.'})

    elif request.method == 'DELETE':
        hajj_pkg.delete()
        return JsonResponse({'success': True, 'message': 'Hajj Package deleted successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
def book_package_api(request):
    """
    POST /api/packages/book/
    Creates a new Package Booking record for public/retail website users.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)

    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        package_id = data.get('package_id')
        if not package_id:
            return JsonResponse({'success': False, 'message': 'Package ID is required.'}, status=400)

        package = get_object_or_404(Package, pk=package_id)

        full_name = (data.get('full_name') or '').strip()
        phone_number = (data.get('phone_number') or '').strip()
        email = (data.get('email') or '').strip()
        sharing_category = (data.get('sharing_category') or 'quad').strip().lower()

        adults_count = int(data.get('adults_count') or 1)
        children_count = int(data.get('children_count') or 0)
        children_with_bed_count = int(data.get('children_with_bed_count') or 0)
        children_no_bed_count = int(data.get('children_no_bed_count') or 0)
        infants_count = int(data.get('infants_count') or 0)
        selected_addons = data.get('selected_addons') or []

        # Calculate pricing dynamically based on room type & passenger counts
        rate_per_adult = float(getattr(package, f'price_{sharing_category}', None) or package.price or 210000)
        rate_child = float(package.price_child_with_bed or package.price_child or (rate_per_adult * 0.85))
        rate_child_no_bed = float(package.price_child_no_bed or (rate_per_adult * 0.60))
        rate_infant = float(package.price_infant or 65000)

        total_price = (
            (adults_count * rate_per_adult) +
            (children_with_bed_count * rate_child) +
            (children_no_bed_count * rate_child_no_bed) +
            (infants_count * rate_infant)
        )

        if isinstance(selected_addons, list):
            for add in selected_addons:
                if isinstance(add, dict):
                    total_price += float(add.get('price', 0))

        tracking_id = f"GSA-PKG-{uuid.uuid4().hex[:8].upper()}"
        user = request.user if (hasattr(request, 'user') and request.user.is_authenticated) else None

        if user:
            if not full_name:
                full_name = user.get_full_name() or user.username
            if not email:
                email = getattr(user, 'email', '') or ''
            if not phone_number and hasattr(user, 'phone_number'):
                phone_number = getattr(user, 'phone_number', '') or ''

        from apps.bookings.models import Booking
        booking = Booking.objects.create(
            user=user,
            package=package,
            booking_type='package',
            status='pending',
            sharing_category=sharing_category.capitalize(),
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            adults_count=adults_count,
            children_count=children_count,
            infants_count=infants_count,
            selected_addons=selected_addons,
            total_price=total_price,
            pnr=tracking_id
        )

        if package.available_seats and package.available_seats > 0:
            total_pax = adults_count + children_count
            package.available_seats = max(0, package.available_seats - total_pax)
            package.save()

        # Dispatch automated confirmation emails (User & Admin)
        try:
            from apps.accounts.views import send_package_booking_confirmation_email
            send_package_booking_confirmation_email(user, tracking_id, package, booking, guest_email=email, guest_name=full_name, guest_phone=phone_number)
        except Exception as email_err:
            print(f"[Booking Email Dispatch Error] {email_err}")

        return JsonResponse({
            'success': True,
            'message': 'Package booking submitted successfully!',
            'tracking_id': tracking_id,
            'package_title': package.title,
            'sharing_category': sharing_category.upper(),
            'adults_count': adults_count,
            'children_count': children_count,
            'total_price': str(total_price)
        })
    except Exception as err:
        return JsonResponse({'success': False, 'message': f'Failed to register booking: {str(err)}'}, status=500)


