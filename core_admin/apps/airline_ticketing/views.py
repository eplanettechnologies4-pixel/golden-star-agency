"""
Admin API views for the Airline Ticketing (B2B) section.

Permission pattern: @csrf_exempt + @user_passes_test(is_admin)
— identical to admin_packages_api / admin_package_detail_api in apps/accounts/views.py.

is_admin() redefined locally because this is a new app file
(same body as every other copy in the project).
"""

import random
import string
from decimal import Decimal
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.db import transaction
import json
import os
from functools import wraps
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render

from .models import Sector, Airline, AirlineFlightInventory, BaggageFareTier, GroupFarePolicy, AgentPackage, AgentTicketOrder, OrderPassenger, Hotel, SeatAdjustmentLog, BankAccount, AgentHajjPackage, AgentHajjAccommodation


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


def _safe_airline_logo_url(obj_or_airline):
    if not obj_or_airline:
        return None
    airline = obj_or_airline if isinstance(obj_or_airline, Airline) else getattr(obj_or_airline, 'airline', None)
    logo = None
    if airline and getattr(airline, 'logo', None):
        logo = airline.logo
    elif hasattr(obj_or_airline, 'airline_logo_url') and getattr(obj_or_airline, 'airline_logo_url'):
        return getattr(obj_or_airline, 'airline_logo_url')
    elif hasattr(obj_or_airline, 'airline_logo') and getattr(obj_or_airline, 'airline_logo'):
        logo = getattr(obj_or_airline, 'airline_logo')
    elif hasattr(obj_or_airline, 'logo') and getattr(obj_or_airline, 'logo'):
        logo = getattr(obj_or_airline, 'logo')

    if not logo:
        return None
    try:
        url = None
        if hasattr(logo, 'url') and logo.url:
            url = str(logo.url)
        elif isinstance(logo, str) and logo.strip():
            url = logo.strip()
        else:
            return None
        if url and not url.startswith('/') and not url.startswith('http://') and not url.startswith('https://'):
            url = '/' + url
        return url
    except Exception:
        return None


# ──────────────────────────────────────────────
# Permission helper  (matches apps/accounts/views.py:477 exactly)
# ──────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.role in ('super_admin', 'admin', 'staff'))


def is_agent(user):
    return user.is_authenticated and (user.role == 'agent' or user.is_superuser)


def is_agent_or_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role in ('agent', 'admin', 'super_admin', 'staff'))


def admin_required_api(view_func):
    """API decorator that returns JSON 403 instead of HTML redirect on auth failure."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Admin authentication required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


def agent_required_api(view_func):
    """API decorator for agent endpoints that returns JSON 403 instead of HTML redirect on auth failure."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_agent_or_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Agent authentication required.', 'packages': [], 'orders': [], 'inventory': []}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


# ══════════════════════════════════════════════
# SECTORS (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_sectors_api(request):
    """
    GET  → list all sectors with counts of flights & packages under them
    POST → create a new sector
    """
    if request.method == 'GET':
        sectors = Sector.objects.all()
        data = []
        for s in sectors:
            flights_count = s.flights.count()
            packages_count = s.agent_packages.count()
            flight_seats = sum(f.total_seats for f in s.flights.all())
            package_seats = sum(p.total_seats for p in s.agent_packages.all())
            total_seats = flight_seats + package_seats

            data.append({
                'id': s.id,
                'name': s.name,
                'origin_city': s.origin_city,
                'destination_city': s.destination_city,
                'is_round_trip': s.is_round_trip,
                'is_active': s.is_active,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
                'flights_count': flights_count,
                'packages_count': packages_count,
                'total_seats': total_seats,
            })
        return JsonResponse({'success': True, 'sectors': data})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        origin_city = request.POST.get('origin_city', '').strip()
        destination_city = request.POST.get('destination_city', '').strip()

        if not name or not origin_city or not destination_city:
            return JsonResponse({'success': False, 'message': 'Sector name, origin, and destination are required.'}, status=400)

        is_active_raw = request.POST.get('is_active')
        is_active_val = is_active_raw in ('on', 'true', '1', 'True', True) if is_active_raw is not None else True
        is_round_trip_raw = request.POST.get('is_round_trip')
        is_round_trip_val = is_round_trip_raw in ('on', 'true', '1', 'True', True) if is_round_trip_raw is not None else False

        sector = Sector(
            name=name,
            origin_city=origin_city,
            destination_city=destination_city,
            is_round_trip=is_round_trip_val,
            is_active=is_active_val,
        )
        sector.save()
        return JsonResponse({'success': True, 'id': sector.id, 'message': 'Sector created successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_sector_detail_api(request, pk):
    """
    POST   → edit sector
    DELETE → delete sector
    """
    sector = get_object_or_404(Sector, pk=pk)

    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'sector': {
                'id': sector.id,
                'name': sector.name,
                'origin_city': sector.origin_city,
                'destination_city': sector.destination_city,
                'is_round_trip': sector.is_round_trip,
                'is_active': sector.is_active,
            }
        })

    if request.method == 'DELETE':
        sector.delete()
        return JsonResponse({'success': True, 'message': 'Sector deleted.'})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            sector.name = name
        origin = request.POST.get('origin_city', '').strip()
        if origin:
            sector.origin_city = origin
        dest = request.POST.get('destination_city', '').strip()
        if dest:
            sector.destination_city = dest

        sector.is_round_trip = request.POST.get('is_round_trip', 'false') in ('true', 'on', '1', True)
        sector.is_active = request.POST.get('is_active', 'true') in ('true', 'on', '1', True)
        sector.save()
        return JsonResponse({'success': True, 'message': 'Sector updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# MANUAL SEAT ADJUSTMENT (WITHOUT Financial Impact)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_adjust_seats_api(request, pk):
    """
    POST → Manually update seat counts (total_seats, booked_seats, or delta)
           for FlightInventory, AgentPackage, or AgentHajjPackage without impacting financial ledgers or orders.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    item_type = request.POST.get('item_type', 'inventory').strip()  # 'inventory', 'package', 'hajj_package'
    target_field_req = request.POST.get('target_field', '').strip()
    reason = request.POST.get('reason', 'Offline / Manual Admin Seat Adjustment').strip()

    if item_type in ('package', 'umrah_package'):
        item = get_object_or_404(AgentPackage, pk=pk)
        fi_obj = None
        pkg_obj = item
    elif item_type in ('hajj_package', 'hajj'):
        item = get_object_or_404(AgentHajjPackage, pk=pk)
        fi_obj = None
        pkg_obj = None
    else:
        item = get_object_or_404(AirlineFlightInventory, pk=pk)
        fi_obj = item
        pkg_obj = None

    if target_field_req == 'booked_seats' and request.POST.get('booked_seats') is not None and request.POST.get('booked_seats') != '':
        new_val = int(request.POST.get('booked_seats') or 0)
        old_val = getattr(item, 'booked_seats', 0)
        if hasattr(item, 'booked_seats'):
            item.booked_seats = max(0, min(item.total_seats, new_val))
            target_field = 'booked_seats'
        else:
            item.available_seats = max(0, item.total_seats - new_val)
            target_field = 'available_seats'

    elif target_field_req == 'available_seats_delta' and request.POST.get('available_seats_delta') is not None and request.POST.get('available_seats_delta') != '':
        delta = int(request.POST.get('available_seats_delta') or 0)
        if hasattr(item, 'booked_seats'):
            old_val = item.booked_seats
            # Decrementing available seats by delta means increasing booked_seats by -delta
            new_val = max(0, min(item.total_seats, item.booked_seats - delta))
            item.booked_seats = new_val
            target_field = 'booked_seats'
        else:
            old_val = item.total_seats
            new_val = max(0, item.total_seats + delta)
            item.total_seats = new_val
            if hasattr(item, 'available_seats') and not isinstance(getattr(type(item), 'available_seats', None), property):
                item.available_seats = max(0, item.available_seats + delta)
            target_field = 'total_seats'

    else:
        new_val = int(request.POST.get('total_seats') or getattr(item, 'total_seats', 0))
        old_val = item.total_seats
        item.total_seats = max(0, new_val)
        target_field = 'total_seats'
        if hasattr(item, 'available_seats') and not isinstance(getattr(type(item), 'available_seats', None), property):
            item.available_seats = max(0, new_val)

    item.save()

    SeatAdjustmentLog.objects.create(
        flight_inventory=fi_obj,
        agent_package=pkg_obj,
        adjusted_by=request.user if request.user.is_authenticated else None,
        target_field=target_field,
        old_value=old_val,
        new_value=new_val,
        reason=reason
    )

    booked_val = getattr(item, 'booked_seats', 0)
    avail_val = max(0, item.total_seats - booked_val) if hasattr(item, 'booked_seats') else getattr(item, 'available_seats', item.total_seats)

    return JsonResponse({
        'success': True,
        'message': f'Seats updated successfully ({old_val} → {new_val}).',
        'total_seats': item.total_seats,
        'booked_seats': booked_val,
        'available_seats': avail_val
    })


# ══════════════════════════════════════════════
# AIRLINES  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_airlines_api(request):
    """
    GET  → list all airlines
    POST → create a new airline (multipart/form-data, logo via request.FILES)
    """
    if request.method == 'GET':
        airlines = Airline.objects.all()
        data = []
        for a in airlines:
            data.append({
                'id':        a.id,
                'name':      a.name,
                'iata_code': a.iata_code or '',
                'logo_url':  _safe_airline_logo_url(a),
                'is_active': a.is_active,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'airlines': data})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        iata_code = request.POST.get('iata_code', '').strip().upper()
        if not name:
            return JsonResponse({'success': False, 'message': 'Airline name is required.'}, status=400)

        is_active_raw = request.POST.get('is_active')
        is_active_val = is_active_raw in ('on', 'true', '1', 'True', True) if is_active_raw is not None else True

        airline = Airline(
            name=name,
            iata_code=iata_code,
            is_active=is_active_val,
        )
        if 'logo' in request.FILES:
            airline.logo = request.FILES['logo']
        airline.save()
        return JsonResponse({'success': True, 'id': airline.id, 'logo_url': _safe_airline_logo_url(airline), 'message': 'Airline created.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# AIRLINE DETAIL  (POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_airline_detail_api(request, pk):
    """
    POST   → edit airline name / logo / is_active
    DELETE → delete airline (cascades to AirlineFlightInventory + BaggageFareTier)
    """
    airline = get_object_or_404(Airline, pk=pk)

    if request.method == 'DELETE':
        airline.delete()
        return JsonResponse({'success': True, 'message': 'Airline deleted.'})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            airline.name = name
        airline.is_active = request.POST.get('is_active', 'true') == 'true'
        if 'logo' in request.FILES:
            airline.logo = request.FILES['logo']
        airline.save()
        return JsonResponse({'success': True, 'message': 'Airline updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# FLIGHT INVENTORY  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_flight_inventory_api(request):
    """
    GET  → list all flight inventory entries with nested baggage tiers & Sector/Trip details
    POST → create a new inventory entry + its baggage tiers in one submission
    """
    if request.method == 'GET':
        entries = AirlineFlightInventory.objects.select_related('airline', 'sector').prefetch_related('baggage_tiers')
        trip_type = request.GET.get('trip_type', '').strip()
        if trip_type:
            entries = entries.filter(trip_type=trip_type)
        data = []
        for fi in entries:
            tiers = [
                {'id': t.id, 'weight_kg': t.weight_kg, 'fare': float(t.fare)}
                for t in fi.baggage_tiers.all()
            ]
            data.append({
                'id':                   fi.id,
                'sector_id':            fi.sector_id,
                'sector_name':          fi.sector.name if fi.sector else None,
                'airline_id':           fi.airline_id,
                'airline_name':         fi.airline.name,
                'airline_logo_url':     _safe_airline_logo_url(fi),
                'departure_city':       fi.departure_city,
                'destination_city':     fi.destination_city,
                'departure_time':       fi.departure_time,
                'arrival_time':         fi.arrival_time,
                'total_seats':          fi.total_seats,
                'booked_seats':         fi.booked_seats,
                'available_seats':      fi.available_seats,
                'trip_type':            fi.trip_type,
                'trip_type_display':    fi.get_trip_type_display(),
                'route_type':           fi.route_type,
                'route_type_display':   fi.get_route_type_display(),
                'via_city':             fi.via_city or '',
                'has_meal':             fi.has_meal,
                'return_departure_time': fi.return_departure_time or '',
                'return_arrival_time':   fi.return_arrival_time or '',
                'return_route_type':     fi.return_route_type or '',
                'return_via_city':       fi.return_via_city or '',
                'is_active':            fi.is_active,
                'sectors_data':         fi.sectors_data if fi.sectors_data else [],
                'created_at':           fi.created_at.strftime('%Y-%m-%d %H:%M'),
                'baggage_tiers':        tiers,
            })
        return JsonResponse({'success': True, 'inventory': data})

    if request.method == 'POST':
        airline_id = request.POST.get('airline_id', '').strip()
        departure_city = request.POST.get('departure_city', '').strip()
        destination_city = request.POST.get('destination_city', '').strip()

        if not airline_id or not departure_city or not destination_city:
            return JsonResponse(
                {'success': False, 'message': 'airline_id, departure_city, and destination_city are required.'},
                status=400
            )

        airline = get_object_or_404(Airline, pk=airline_id)

        sector_id = request.POST.get('sector_id', '').strip()
        sector = get_object_or_404(Sector, pk=sector_id) if sector_id else None

        # Parse per-sector legs JSON
        raw_sectors = request.POST.get('sectors_data', '[]')
        try:
            parsed_sectors = json.loads(raw_sectors) if isinstance(raw_sectors, str) else raw_sectors
            if not isinstance(parsed_sectors, list): parsed_sectors = []
        except Exception:
            parsed_sectors = []

        # Derive outbound departure/arrival from first leg if not explicitly provided
        leg0 = parsed_sectors[0] if parsed_sectors else {}
        dep_time = request.POST.get('departure_time', '').strip() or leg0.get('dep_time', '00:00 AM')
        arr_time = request.POST.get('arrival_time', '').strip() or leg0.get('arr_time', '00:00 AM')

        fi = AirlineFlightInventory(
            sector=sector,
            airline=airline,
            departure_city=departure_city,
            destination_city=destination_city,
            departure_time=dep_time,
            arrival_time=arr_time,
            total_seats=int(request.POST.get('total_seats', 0) or 0),
            booked_seats=int(request.POST.get('booked_seats', 0) or 0),
            trip_type=request.POST.get('trip_type', 'return').strip(),
            route_type=request.POST.get('route_type', 'direct').strip(),
            via_city=request.POST.get('via_city', '').strip(),
            has_meal=request.POST.get('has_meal', 'false').lower() in ('true', 'on', '1'),
            return_departure_time=request.POST.get('return_departure_time', '').strip(),
            return_arrival_time=request.POST.get('return_arrival_time', '').strip(),
            return_route_type=request.POST.get('return_route_type', '').strip(),
            return_via_city=request.POST.get('return_via_city', '').strip(),
            is_active=request.POST.get('is_active', 'true') == 'true',
            sectors_data=parsed_sectors,
        )
        fi.save()

        # Save baggage tiers: sent as baggage_weight_0, baggage_fare_0, baggage_weight_1, ...
        _save_baggage_tiers(fi, request.POST)

        return JsonResponse({'success': True, 'id': fi.id, 'message': 'Flight inventory entry created.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# FLIGHT INVENTORY DETAIL  (POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_flight_inventory_detail_api(request, pk):
    """
    POST   → edit inventory entry (replaces all baggage tiers on save)
    DELETE → delete inventory entry (cascades to BaggageFareTier)
    """
    fi = get_object_or_404(AirlineFlightInventory, pk=pk)

    if request.method == 'DELETE':
        fi.delete()
        return JsonResponse({'success': True, 'message': 'Flight inventory entry deleted.'})

    if request.method == 'POST':
        airline_id = request.POST.get('airline_id', '').strip()
        if airline_id:
            fi.airline = get_object_or_404(Airline, pk=airline_id)

        sector_id = request.POST.get('sector_id', '').strip()
        if sector_id:
            fi.sector = get_object_or_404(Sector, pk=sector_id)
        elif 'sector_id' in request.POST:
            fi.sector = None

        departure_city = request.POST.get('departure_city', '').strip()
        if departure_city:
            fi.departure_city = departure_city

        destination_city = request.POST.get('destination_city', '').strip()
        if destination_city:
            fi.destination_city = destination_city

        fi.departure_time = request.POST.get('departure_time', fi.departure_time).strip()
        fi.arrival_time = request.POST.get('arrival_time', fi.arrival_time).strip()

        total = request.POST.get('total_seats')
        if total is not None and total != '':
            fi.total_seats = int(total or 0)

        booked = request.POST.get('booked_seats')
        if booked is not None and booked != '':
            fi.booked_seats = int(booked or 0)

        fi.trip_type = request.POST.get('trip_type', fi.trip_type).strip()
        fi.route_type = request.POST.get('route_type', fi.route_type).strip()
        fi.via_city = request.POST.get('via_city', fi.via_city or '').strip()
        fi.has_meal = request.POST.get('has_meal', 'false').lower() in ('true', 'on', '1') if 'has_meal' in request.POST else fi.has_meal
        fi.return_departure_time = request.POST.get('return_departure_time', fi.return_departure_time or '').strip()
        fi.return_arrival_time = request.POST.get('return_arrival_time', fi.return_arrival_time or '').strip()
        fi.return_route_type = request.POST.get('return_route_type', fi.return_route_type or '').strip()
        fi.return_via_city = request.POST.get('return_via_city', fi.return_via_city or '').strip()

        fi.is_active = request.POST.get('is_active', 'true') == 'true'

        # Update sectors_data if provided
        if 'sectors_data' in request.POST:
            raw_sectors = request.POST.get('sectors_data', '[]')
            try:
                parsed_sectors = json.loads(raw_sectors) if isinstance(raw_sectors, str) else raw_sectors
                if not isinstance(parsed_sectors, list): parsed_sectors = []
            except Exception:
                parsed_sectors = []
            fi.sectors_data = parsed_sectors
            # Auto-sync first leg times if submitted without explicit departure_time
            if parsed_sectors and not request.POST.get('departure_time', '').strip():
                fi.departure_time = parsed_sectors[0].get('dep_time', fi.departure_time)
                fi.arrival_time = parsed_sectors[0].get('arr_time', fi.arrival_time)

        fi.save()

        # Replace all baggage tiers with the newly submitted ones
        fi.baggage_tiers.all().delete()
        _save_baggage_tiers(fi, request.POST)

        return JsonResponse({'success': True, 'message': 'Flight inventory entry updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ──────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────

def _save_baggage_tiers(flight_inventory, post_data):
    """
    Parse baggage tier pairs from POST data.
    Keys expected: baggage_fare_7, baggage_fare_20, baggage_fare_30, baggage_fare_40
    Or baggage_weight_0, baggage_fare_0 ...
    If no tiers provided, creates default 7KG, 20KG, 30KG, 40KG fare tiers automatically.
    """
    created_count = 0
    i = 0
    while True:
        weight_key = f'baggage_weight_{i}'
        fare_key = f'baggage_fare_{i}'
        if weight_key not in post_data and fare_key not in post_data:
            break
        weight = post_data.get(weight_key, '').strip()
        fare = post_data.get(fare_key, '').strip()
        if weight and fare:
            try:
                BaggageFareTier.objects.create(
                    flight_inventory=flight_inventory,
                    weight_kg=int(weight),
                    fare=float(fare),
                )
                created_count += 1
            except (ValueError, TypeError):
                pass
        i += 1

    direct_tiers = [
        ('7',  post_data.get('baggage_fare_7')  or post_data.get('fare_7kg')  or post_data.get('fare_handcarry') or post_data.get('price_handcarry')),
        ('20', post_data.get('baggage_fare_20') or post_data.get('fare_20kg') or post_data.get('price_20kg') or post_data.get('price') or post_data.get('base_fare')),
        ('23', post_data.get('baggage_fare_23') or post_data.get('fare_23kg') or post_data.get('price_23kg')),
        ('25', post_data.get('baggage_fare_25') or post_data.get('fare_25kg') or post_data.get('price_25kg')),
        ('30', post_data.get('baggage_fare_30') or post_data.get('fare_30kg') or post_data.get('price_30kg')),
        ('35', post_data.get('baggage_fare_35') or post_data.get('fare_35kg') or post_data.get('price_35kg')),
        ('40', post_data.get('baggage_fare_40') or post_data.get('fare_40kg') or post_data.get('price_40kg')),
        ('46', post_data.get('baggage_fare_46') or post_data.get('fare_46kg') or post_data.get('price_46kg')),
    ]
    for w, f in direct_tiers:
        if f and str(f).strip():
            try:
                BaggageFareTier.objects.create(
                    flight_inventory=flight_inventory,
                    weight_kg=int(w),
                    fare=float(f),
                )
                created_count += 1
            except (ValueError, TypeError):
                pass

    # Fallback: if no baggage tiers created at all, create standard default tiers (7KG, 20KG, 30KG, 40KG)!
    if created_count == 0:
        base_price = float(post_data.get('price') or post_data.get('fare') or post_data.get('base_fare') or 50000.00)
        BaggageFareTier.objects.create(flight_inventory=flight_inventory, weight_kg=7, fare=max(0, base_price - 10000))
        BaggageFareTier.objects.create(flight_inventory=flight_inventory, weight_kg=20, fare=base_price)
        BaggageFareTier.objects.create(flight_inventory=flight_inventory, weight_kg=30, fare=base_price + 5000)
        BaggageFareTier.objects.create(flight_inventory=flight_inventory, weight_kg=40, fare=base_price + 10000)


# ══════════════════════════════════════════════
# GROUP FARE POLICIES  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_group_fare_policies_api(request):
    """
    GET  → list all group fare policies joined with flight inventory and airline details
    POST → create a new group fare policy (FormData)
    """
    if request.method == 'GET':
        policies = GroupFarePolicy.objects.select_related('flight_inventory', 'flight_inventory__airline').all()
        data = []
        for p in policies:
            fi = p.flight_inventory
            data.append({
                'id':                   p.id,
                'flight_inventory_id':  fi.id,
                'airline_name':         fi.airline.name,
                'airline_logo_url':     fi.airline.logo.url if fi.airline.logo else None,
                'departure_city':       fi.departure_city,
                'destination_city':     fi.destination_city,
                'departure_time':       fi.departure_time,
                'arrival_time':         fi.arrival_time,
                'route_display':        f"{fi.airline.name} — {fi.departure_city} → {fi.destination_city} ({fi.departure_time})",
                'min_group_size':       p.min_group_size,
                'discount_type':        p.discount_type,
                'discount_type_display': p.get_discount_type_display(),
                'discount_value':       float(p.discount_value),
                'baggage_weight_kg':    p.baggage_weight_kg,
                'is_active':            p.is_active,
                'created_at':           p.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'policies': data})

    if request.method == 'POST':
        inventory_id = request.POST.get('flight_inventory_id', '').strip()
        min_group_size = request.POST.get('min_group_size', '').strip()
        discount_value = request.POST.get('discount_value', '').strip()

        if not inventory_id or not min_group_size or not discount_value:
            return JsonResponse(
                {'success': False, 'message': 'flight_inventory_id, min_group_size, and discount_value are required.'},
                status=400
            )

        fi = get_object_or_404(AirlineFlightInventory, pk=inventory_id)

        policy = GroupFarePolicy(
            flight_inventory=fi,
            min_group_size=int(min_group_size),
            discount_type=request.POST.get('discount_type', 'percentage').strip(),
            discount_value=float(discount_value),
            baggage_weight_kg=int(request.POST.get('baggage_weight_kg', 20) or 20),
            is_active=request.POST.get('is_active', 'true') == 'true',
        )
        policy.save()
        return JsonResponse({'success': True, 'id': policy.id, 'message': 'Group fare policy created.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# GROUP FARE POLICY DETAIL  (POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_group_fare_policy_detail_api(request, pk):
    """
    POST   → edit group fare policy fields
    DELETE → delete group fare policy
    """
    policy = get_object_or_404(GroupFarePolicy, pk=pk)

    if request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'Group fare policy deleted.'})

    if request.method == 'POST':
        inventory_id = request.POST.get('flight_inventory_id', '').strip()
        if inventory_id:
            policy.flight_inventory = get_object_or_404(AirlineFlightInventory, pk=inventory_id)

        min_size = request.POST.get('min_group_size')
        if min_size is not None and min_size != '':
            policy.min_group_size = int(min_size)

        discount_type = request.POST.get('discount_type', '').strip()
        if discount_type:
            policy.discount_type = discount_type

        disc_val = request.POST.get('discount_value')
        if disc_val is not None and disc_val != '':
            policy.discount_value = float(disc_val)

        baggage = request.POST.get('baggage_weight_kg')
        if baggage is not None and baggage != '':
            policy.baggage_weight_kg = int(baggage)

        policy.is_active = request.POST.get('is_active', 'true') == 'true'
        policy.save()

        return JsonResponse({'success': True, 'message': 'Group fare policy updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# AGENT PACKAGES  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_agent_packages_api(request):
    """
    GET  → list all agent packages (supports ?type=umrah or ?type=hajj query param filter)
    POST → create a new agent package (FormData, multipart for images)
    """
    if request.method == 'GET':
        pkg_type = request.GET.get('type', '').strip().lower()
        packages = AgentPackage.objects.select_related('airline', 'sector').prefetch_related('hotels').all()
        if pkg_type in ['umrah', 'hajj']:
            packages = packages.filter(package_type=pkg_type)

        data = []
        for p in packages:
            data.append({
                'id':                       p.id,
                'sector_id':                p.sector_id,
                'sector_name':              p.sector.name if p.sector else None,
                'package_type':             p.package_type,
                'package_type_display':     p.get_package_type_display(),
                'title':                    p.title,
                'description':              p.description,
                'duration_days':            p.duration_days,
                'agent_price':              str(p.agent_price),
                'suggested_resale_price':   str(p.suggested_resale_price) if p.suggested_resale_price else '',
                'commission_amount':        str(p.commission_amount) if p.commission_amount else '',
                'adult_price':              str(p.adult_price) if p.adult_price is not None else str(p.agent_price),
                'child_price':              str(p.child_price) if p.child_price is not None else str(p.agent_price),
                'infant_price':              str(p.infant_price) if p.infant_price is not None else '0.00',
                'price_sharing':            str(p.price_sharing) if p.price_sharing is not None else '',
                'price_quad':               str(p.price_quad) if p.price_quad is not None else '',
                'price_triple':             str(p.price_triple) if p.price_triple is not None else '',
                'price_double':             str(p.price_double) if p.price_double is not None else '',
                'flight_name':              p.flight_name or (p.airline.name if p.airline else 'Saudi Airlines'),
                'flight_route_type':        p.flight_route_type or 'direct',
                'flight_route_type_display':'Direct Flight' if (p.flight_route_type or 'direct') == 'direct' else 'Via Flight',
                'flight_route':             p.flight_route or 'KHI - JED - MED - KHI',
                'includes_meal':            p.includes_meal,
                'meal_display':             'Yes' if p.includes_meal else 'No',
                'meal_detail':              p.meal_detail or 'Full Board',
                'transport_type':           p.transport_type or 'Sharing',
                'departure_date':           p.departure_date.strftime('%Y-%m-%d') if p.departure_date else '',
                'return_date':              p.return_date.strftime('%Y-%m-%d') if p.return_date else '',
                'hotel_ids':                list(p.hotels.values_list('id', flat=True)),
                'hotels':                   [{'id': h.id, 'name': h.name, 'city': h.city, 'location': h.location, 'city_display': h.get_city_display(), 'distance_from_haram': h.distance_from_haram, 'price_sharing': float(h.price_sharing) if h.price_sharing is not None else None, 'price_quad': float(h.price_quad) if h.price_quad is not None else None, 'price_triple': float(h.price_triple) if h.price_triple is not None else None, 'price_double': float(h.price_double) if h.price_double is not None else None} for h in p.hotels.all()],
                'total_seats':              p.total_seats,
                'booked_seats':             p.booked_seats,
                'available_seats':          p.available_seats,
                'makkah_hotel_name':        p.makkah_hotel_name,
                'makkah_hotel_distance':    p.makkah_hotel_distance,
                'makkah_nights':            p.makkah_nights,
                'madinah_hotel_name':       p.madinah_hotel_name,
                'madinah_hotel_distance':   p.madinah_hotel_distance,
                'madinah_nights':           p.madinah_nights,
                'airline_id':               p.airline_id,
                'airline_name':             p.airline.name if p.airline else (p.flight_name or ''),
                'airline_logo_url':         p.airline.logo.url if (p.airline and p.airline.logo) else None,
                'images':                   p.images or [],
                'cover_photo':              p.cover_photo.url if p.cover_photo else '',
                'cover_photo_url':          p.cover_photo_url,
                'is_active':                p.is_active,
                'created_at':               p.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'packages': data})

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip() or title
        agent_price_input = request.POST.get('agent_price', '').strip()

        if not title:
            return JsonResponse(
                {'success': False, 'message': 'Package title is required.'},
                status=400
            )

        # Fallback for agent_price if not directly supplied
        if agent_price_input:
            agent_price_val = Decimal(agent_price_input)
        else:
            adult_p = request.POST.get('adult_price', '').strip()
            sharing_p = request.POST.get('price_sharing', '').strip()
            quad_p = request.POST.get('price_quad', '').strip()
            double_p = request.POST.get('price_double', '').strip()
            triple_p = request.POST.get('price_triple', '').strip()
            fallback = adult_p or sharing_p or quad_p or triple_p or double_p or '0.00'
            agent_price_val = Decimal(fallback)

        airline_id = request.POST.get('airline_id', '').strip()
        airline = get_object_or_404(Airline, pk=airline_id) if airline_id else None

        sector_id = request.POST.get('sector_id', '').strip()
        sector = get_object_or_404(Sector, pk=sector_id) if sector_id else None

        images = []
        images_url_input = request.POST.get('images_urls', '')
        if isinstance(images_url_input, str) and images_url_input.strip():
            try:
                url_images = json.loads(images_url_input)
            except Exception:
                url_images = [u.strip() for u in images_url_input.split(',') if u.strip()]
            images.extend(url_images)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'agent_packages')
        os.makedirs(upload_dir, exist_ok=True)
        for uploaded_file in request.FILES.getlist('images_files'):
            safe_title = title[:20].replace(' ', '_')
            safe_name = f"agent_pkg_{safe_title}_{uploaded_file.name[-20:]}"
            file_path = os.path.join(upload_dir, safe_name)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)
            images.append(f"{settings.MEDIA_URL}agent_packages/{safe_name}")

        suggested_resale = request.POST.get('suggested_resale_price', '').strip()
        commission = request.POST.get('commission_amount', '').strip()

        def parse_dec(val):
            return Decimal(val) if val and str(val).strip() else None

        def parse_date(val):
            return val.strip() if val and str(val).strip() else None

        is_active_val = request.POST.get('is_active')
        is_active = is_active_val in ('on', 'true', '1', 'True', True) if is_active_val is not None else True

        flight_name = request.POST.get('flight_name', '').strip() or (airline.name if airline else 'Saudi Airlines')
        flight_route_type = request.POST.get('flight_route_type', 'direct').strip()
        flight_route = request.POST.get('flight_route', '').strip() or 'KHI - JED - MED - KHI'
        includes_meal_raw = request.POST.get('includes_meal')
        includes_meal = includes_meal_raw in ('true', '1', 'True', True, 'on') if includes_meal_raw is not None else True
        meal_detail = request.POST.get('meal_detail', 'Full Board').strip()
        transport_type = request.POST.get('transport_type', 'Sharing').strip()

        pkg = AgentPackage(
            sector=sector,
            package_type=request.POST.get('package_type', 'umrah').strip(),
            title=title,
            description=description,
            duration_days=int(request.POST.get('duration_days', 15) or 15),
            agent_price=agent_price_val,
            suggested_resale_price=parse_dec(suggested_resale),
            commission_amount=parse_dec(commission),
            adult_price=parse_dec(request.POST.get('adult_price')) or agent_price_val,
            child_price=parse_dec(request.POST.get('child_price')),
            infant_price=parse_dec(request.POST.get('infant_price')),
            price_sharing=parse_dec(request.POST.get('price_sharing')),
            price_quad=parse_dec(request.POST.get('price_quad')),
            price_triple=parse_dec(request.POST.get('price_triple')),
            price_double=parse_dec(request.POST.get('price_double')),
            flight_name=flight_name,
            flight_route_type=flight_route_type,
            flight_route=flight_route,
            includes_meal=includes_meal,
            meal_detail=meal_detail,
            transport_type=transport_type,
            departure_date=parse_date(request.POST.get('departure_date')),
            return_date=parse_date(request.POST.get('return_date')),
            total_seats=int(request.POST.get('total_seats', 30) or 30),
            booked_seats=int(request.POST.get('booked_seats', 0) or 0),
            makkah_hotel_name=request.POST.get('makkah_hotel_name', '').strip(),
            makkah_hotel_distance=request.POST.get('makkah_hotel_distance', '').strip(),
            makkah_nights=int(request.POST.get('makkah_nights', 7) or 7),
            madinah_hotel_name=request.POST.get('madinah_hotel_name', '').strip(),
            madinah_hotel_distance=request.POST.get('madinah_hotel_distance', '').strip(),
            madinah_nights=int(request.POST.get('madinah_nights', 7) or 7),
            airline=airline,
            images=images,
            cover_photo=request.FILES.get('cover_photo') or request.FILES.get('cover_image'),
            is_active=is_active,
        )
        pkg.save()

        # Link selected hotels M2M
        hotel_ids_raw = request.POST.getlist('hotel_ids')
        if not hotel_ids_raw and 'hotel_ids_json' in request.POST:
            try:
                hotel_ids_raw = json.loads(request.POST.get('hotel_ids_json'))
            except Exception:
                hotel_ids_raw = []
        if hotel_ids_raw:
            valid_hids = [int(hid) for hid in hotel_ids_raw if str(hid).isdigit()]
            pkg.hotels.set(valid_hids)

        return JsonResponse({'success': True, 'id': pkg.id, 'message': 'Agent package created successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# AGENT PACKAGE DETAIL  (POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_agent_package_detail_api(request, pk):
    """
    POST   → edit agent package details
    DELETE → delete agent package
    """
    pkg = get_object_or_404(AgentPackage, pk=pk)

    if request.method == 'DELETE':
        pkg.delete()
        return JsonResponse({'success': True, 'message': 'Agent package deleted.'})

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            pkg.title = title

        description = request.POST.get('description', '').strip()
        if description:
            pkg.description = description

        pkg.package_type = request.POST.get('package_type', pkg.package_type).strip()

        duration = request.POST.get('duration_days')
        if duration is not None and duration != '':
            pkg.duration_days = int(duration)

        def parse_dec(val):
            return Decimal(val) if val and str(val).strip() else None

        def parse_date(val):
            return val.strip() if val and str(val).strip() else None

        price = request.POST.get('agent_price')
        if price is not None and str(price).strip() != '':
            pkg.agent_price = Decimal(price)
        else:
            adult_p = request.POST.get('adult_price', '').strip()
            sharing_p = request.POST.get('price_sharing', '').strip()
            if adult_p:
                pkg.agent_price = Decimal(adult_p)
            elif sharing_p:
                pkg.agent_price = Decimal(sharing_p)

        suggested = request.POST.get('suggested_resale_price')
        pkg.suggested_resale_price = parse_dec(suggested)

        comm = request.POST.get('commission_amount')
        pkg.commission_amount = parse_dec(comm)

        if 'adult_price' in request.POST: pkg.adult_price = parse_dec(request.POST.get('adult_price'))
        if 'child_price' in request.POST: pkg.child_price = parse_dec(request.POST.get('child_price'))
        if 'infant_price' in request.POST: pkg.infant_price = parse_dec(request.POST.get('infant_price'))
        if 'price_sharing' in request.POST: pkg.price_sharing = parse_dec(request.POST.get('price_sharing'))
        if 'price_quad' in request.POST: pkg.price_quad = parse_dec(request.POST.get('price_quad'))
        if 'price_triple' in request.POST: pkg.price_triple = parse_dec(request.POST.get('price_triple'))
        if 'price_double' in request.POST: pkg.price_double = parse_dec(request.POST.get('price_double'))

        if 'departure_date' in request.POST: pkg.departure_date = parse_date(request.POST.get('departure_date'))
        if 'return_date' in request.POST: pkg.return_date = parse_date(request.POST.get('return_date'))

        total = request.POST.get('total_seats')
        if total is not None and total != '':
            pkg.total_seats = int(total)

        booked = request.POST.get('booked_seats')
        if booked is not None and booked != '':
            pkg.booked_seats = int(booked)

        if 'flight_name' in request.POST: pkg.flight_name = request.POST.get('flight_name', '').strip()
        if 'flight_route_type' in request.POST: pkg.flight_route_type = request.POST.get('flight_route_type', '').strip()
        if 'flight_route' in request.POST: pkg.flight_route = request.POST.get('flight_route', '').strip()
        if 'includes_meal' in request.POST:
            inc_raw = request.POST.get('includes_meal')
            pkg.includes_meal = inc_raw in ('true', '1', 'True', True, 'on')
        if 'meal_detail' in request.POST: pkg.meal_detail = request.POST.get('meal_detail', '').strip()
        if 'transport_type' in request.POST: pkg.transport_type = request.POST.get('transport_type', '').strip()

        pkg.makkah_hotel_name = request.POST.get('makkah_hotel_name', pkg.makkah_hotel_name).strip()
        pkg.makkah_hotel_distance = request.POST.get('makkah_hotel_distance', pkg.makkah_hotel_distance).strip()
        if 'makkah_nights' in request.POST and request.POST.get('makkah_nights').strip():
            pkg.makkah_nights = int(request.POST.get('makkah_nights'))

        pkg.madinah_hotel_name = request.POST.get('madinah_hotel_name', pkg.madinah_hotel_name).strip()
        pkg.madinah_hotel_distance = request.POST.get('madinah_hotel_distance', pkg.madinah_hotel_distance).strip()
        if 'madinah_nights' in request.POST and request.POST.get('madinah_nights').strip():
            pkg.madinah_nights = int(request.POST.get('madinah_nights'))

        airline_id = request.POST.get('airline_id', '').strip()
        if airline_id:
            pkg.airline = get_object_or_404(Airline, pk=airline_id)
        elif 'airline_id' in request.POST:
            pkg.airline = None

        # Link selected hotels M2M
        hotel_ids_raw = request.POST.getlist('hotel_ids')
        if not hotel_ids_raw and 'hotel_ids_json' in request.POST:
            try:
                hotel_ids_raw = json.loads(request.POST.get('hotel_ids_json'))
            except Exception:
                pass
        if 'hotel_ids' in request.POST or 'hotel_ids_json' in request.POST:
            valid_hids = [int(hid) for hid in hotel_ids_raw if str(hid).isdigit()]
            pkg.hotels.set(valid_hids)

        # Images update
        existing_images = pkg.images or []
        images_url_input = request.POST.get('images_urls', '')
        if isinstance(images_url_input, str) and images_url_input.strip():
            try:
                url_images = json.loads(images_url_input)
            except Exception:
                url_images = [u.strip() for u in images_url_input.split(',') if u.strip()]
            existing_images = url_images

        # Upload new image files if any
        if 'images_files' in request.FILES:
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'agent_packages')
            os.makedirs(upload_dir, exist_ok=True)
            for uploaded_file in request.FILES.getlist('images_files'):
                safe_title = pkg.title[:20].replace(' ', '_')
                safe_name = f"agent_pkg_{safe_title}_{uploaded_file.name[-20:]}"
                file_path = os.path.join(upload_dir, safe_name)
                with open(file_path, 'wb+') as dest:
                    for chunk in uploaded_file.chunks():
                        dest.write(chunk)
                existing_images.append(f"{settings.MEDIA_URL}agent_packages/{safe_name}")

        pkg.images = existing_images

        if 'cover_photo' in request.FILES:
            pkg.cover_photo = request.FILES['cover_photo']
        elif 'cover_image' in request.FILES:
            pkg.cover_photo = request.FILES['cover_image']

        if 'is_active' in request.POST:
            is_active_val = request.POST.get('is_active')
            pkg.is_active = is_active_val in ('on', 'true', '1', 'True', True)
        pkg.save()

        return JsonResponse({'success': True, 'message': 'Agent package updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# HOTELS (GET list / POST create / POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_hotels_api(request):
    """
    GET  → list all hotels (filterable by ?city=makkah / ?city=madinah)
    POST → create a new hotel (FormData, multipart for image)
    """
    if request.method == 'GET':
        city = request.GET.get('city', '').strip().lower()
        hotels = Hotel.objects.all()
        if city in ('makkah', 'madinah'):
            hotels = hotels.filter(city=city)

        data = []
        for h in hotels:
            data.append({
                'id': h.id,
                'name': h.name,
                'category': h.category,
                'category_display': h.get_category_display(),
                'city': h.city,
                'location': h.location,
                'city_display': h.get_city_display(),
                'distance_from_haram': h.distance_from_haram,
                'image_url': h.image.url if h.image else None,
                'price_sharing': float(h.price_sharing) if h.price_sharing is not None else None,
                'price_double': float(h.price_double) if h.price_double is not None else None,
                'price_triple': float(h.price_triple) if h.price_triple is not None else None,
                'price_quad': float(h.price_quad) if h.price_quad is not None else None,
                'is_active': h.is_active,
                'created_at': h.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'hotels': data})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'economy').strip().lower()
        city = request.POST.get('city', '').strip().lower()
        location = request.POST.get('location', '').strip()
        distance = request.POST.get('distance_from_haram', '').strip()

        if not name or not city or not distance:
            return JsonResponse({'success': False, 'message': 'Hotel name, city, and distance from Haram are required.'}, status=400)

        def parse_dec(val):
            if val is None or str(val).strip() == '':
                return None
            try:
                return Decimal(str(val).strip())
            except Exception:
                return None

        is_active_val = request.POST.get('is_active')
        is_active = is_active_val in ('on', 'true', '1', 'True', True) if is_active_val is not None else False

        ALLOWED_CATEGORIES = ('economy', 'economy_plus', '1star', '2star', '3star', '4star', '5star')

        hotel = Hotel(
            name=name,
            category=category if category in ALLOWED_CATEGORIES else 'economy',
            city=city,
            location=location,
            distance_from_haram=distance,
            price_sharing=parse_dec(request.POST.get('price_sharing')),
            price_double=parse_dec(request.POST.get('price_double')),
            price_triple=parse_dec(request.POST.get('price_triple')),
            price_quad=parse_dec(request.POST.get('price_quad')),
            is_active=is_active
        )
        if 'image' in request.FILES:
            hotel.image = request.FILES['image']
        hotel.save()
        return JsonResponse({'success': True, 'id': hotel.id, 'message': 'Hotel created successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_hotel_detail_api(request, pk):
    """
    POST   → edit hotel details / toggle active status / replace image
    DELETE → delete hotel
    """
    hotel = get_object_or_404(Hotel, pk=pk)

    if request.method == 'DELETE':
        hotel.delete()
        return JsonResponse({'success': True, 'message': 'Hotel deleted.'})

    if request.method == 'POST':
        ALLOWED_CATEGORIES = ('economy', 'economy_plus', '1star', '2star', '3star', '4star', '5star')
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', '').strip().lower()
        city = request.POST.get('city', '').strip().lower()
        location = request.POST.get('location', '').strip()
        distance = request.POST.get('distance_from_haram', '').strip()

        if name: hotel.name = name
        if category and category in ALLOWED_CATEGORIES: hotel.category = category
        if city: hotel.city = city
        if 'location' in request.POST: hotel.location = location
        if distance: hotel.distance_from_haram = distance

        def parse_dec(val):
            if val is None or str(val).strip() == '':
                return None
            try:
                return Decimal(str(val).strip())
            except Exception:
                return None

        if 'price_sharing' in request.POST: hotel.price_sharing = parse_dec(request.POST.get('price_sharing'))
        if 'price_double' in request.POST: hotel.price_double = parse_dec(request.POST.get('price_double'))
        if 'price_triple' in request.POST: hotel.price_triple = parse_dec(request.POST.get('price_triple'))
        if 'price_quad' in request.POST: hotel.price_quad = parse_dec(request.POST.get('price_quad'))

        if 'is_active' in request.POST:
            is_active_val = request.POST.get('is_active')
            hotel.is_active = is_active_val in ('on', 'true', '1', 'True', True)
        else:
            hotel.is_active = False

        if 'image' in request.FILES:
            hotel.image = request.FILES['image']

        hotel.save()
        return JsonResponse({'success': True, 'message': 'Hotel updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ──────────────────────────────────────────────
# AGENT-FACING READ-ONLY API ENDPOINTS
# Permission pattern: @user_passes_test(is_agent)
# ──────────────────────────────────────────────

def is_agent(user):
    return user.is_authenticated and user.role == 'agent' and user.approval_status == 'approved'


@user_passes_test(is_agent)
def agent_airlines_api(request):
    """
    GET → List all airlines for agent browsing
    """
    airlines = Airline.objects.all()
    data = []
    for a in airlines:
        data.append({
            'id': a.id,
            'name': a.name,
            'iata_code': a.iata_code or '',
            'logo_url': a.logo.url if a.logo else None,
            'is_active': a.is_active,
        })
    return JsonResponse({'success': True, 'airlines': data})


@user_passes_test(is_agent)
def agent_flight_inventory_api(request):
    """
    GET → List active flight route inventories (filtered optional by ?airline_id=X)
    Exposes available_seats (total_seats - booked_seats), NEVER raw booked_seats
    """
    inventory = AirlineFlightInventory.objects.filter(is_active=True, airline__is_active=True).select_related('airline', 'sector').prefetch_related('baggage_tiers')

    airline_id = request.GET.get('airline_id')
    if airline_id:
        inventory = inventory.filter(airline_id=airline_id)

    trip_type = request.GET.get('trip_type')
    if trip_type:
        inventory = inventory.filter(trip_type=trip_type)

    route_type = request.GET.get('route_type')
    if route_type:
        inventory = inventory.filter(route_type=route_type)

    search = request.GET.get('search')
    if search:
        from django.db.models import Q
        inventory = inventory.filter(
            Q(destination_city__icontains=search) | 
            Q(departure_city__icontains=search) | 
            Q(sector__name__icontains=search) |
            Q(airline__name__icontains=search) |
            Q(airline__iata_code__icontains=search)
        )

    data = []
    for fi in inventory:
        tiers = [
            {'id': t.id, 'weight_kg': t.weight_kg, 'fare': float(t.fare)}
            for t in fi.baggage_tiers.all()
        ]
        data.append({
            'id':                   fi.id,
            'sector_id':            fi.sector_id,
            'sector_name':          fi.sector.name if fi.sector else None,
            'airline_id':           fi.airline_id,
            'airline_name':         fi.airline.name,
            'airline_iata_code':    fi.airline.iata_code if fi.airline else '',
            'airline_logo_url':     fi.airline.logo.url if fi.airline and fi.airline.logo else None,
            'departure_city':       fi.departure_city,
            'destination_city':     fi.destination_city,
            'departure_time':       fi.departure_time,
            'arrival_time':         fi.arrival_time,
            'available_seats':      fi.available_seats,
            'trip_type':            fi.trip_type,
            'trip_type_display':    fi.get_trip_type_display(),
            'route_type':           fi.route_type,
            'route_type_display':   fi.get_route_type_display(),
            'via_city':             fi.via_city or '',
            'has_meal':             fi.has_meal,
            'return_departure_time': fi.return_departure_time or '',
            'return_arrival_time':   fi.return_arrival_time or '',
            'return_route_type':     fi.return_route_type or '',
            'return_via_city':       fi.return_via_city or '',
            'baggage_tiers':        tiers,
        })
    return JsonResponse({'success': True, 'inventory': data})


@user_passes_test(is_agent)
def agent_group_fare_policies_api(request):
    """
    GET → List active group fare policies / standalone group tickets for agents
    """
    policies = GroupFarePolicy.objects.filter(
        is_active=True
    ).select_related('flight_inventory', 'flight_inventory__airline', 'airline').all()

    data = []
    for p in policies:
        fi = p.flight_inventory

        if fi:
            airline_name = fi.airline.name if fi.airline else 'Airline'
            airline_logo_url = fi.airline.logo.url if (fi.airline and fi.airline.logo) else None
            dep_city = fi.departure_city
            dest_city = fi.destination_city
            dep_time = fi.departure_time
            arr_time = fi.arrival_time
            trip_type = fi.trip_type
            route_type = fi.route_type
            via_city = fi.via_city or ''
            has_meal = fi.has_meal
            total_seats = fi.total_seats
            avail_seats = fi.available_seats
            ret_dep_time = fi.return_departure_time or ''
            ret_arr_time = fi.return_arrival_time or ''
            ret_route_type = fi.return_route_type or ''
            ret_via_city = fi.return_via_city or ''

            tier = fi.baggage_tiers.filter(weight_kg=p.baggage_weight_kg).first() or fi.baggage_tiers.first()
            base_fare = float(tier.fare) if tier else (float(p.base_fare) if p.base_fare else 0.0)
        else:
            airline_name = p.airline.name if p.airline else (p.airline_name_custom or 'Group Ticket')
            airline_logo_url = p.airline.logo.url if (p.airline and p.airline.logo) else None
            dep_city = p.departure_city or 'Departure'
            dest_city = p.destination_city or 'Destination'
            dep_time = p.departure_time or '00:00'
            arr_time = p.arrival_time or '00:00'
            trip_type = p.trip_type or 'oneway'
            route_type = p.route_type or 'direct'
            via_city = p.via_city or ''
            has_meal = p.has_meal
            total_seats = p.total_seats
            avail_seats = p.available_seats
            ret_dep_time = p.return_departure_time or ''
            ret_arr_time = p.return_arrival_time or ''
            ret_route_type = p.route_type or ''
            ret_via_city = p.via_city or ''
            base_fare = float(p.base_fare) if p.base_fare else 0.0

        if p.group_fare_override is not None and p.group_fare_override > 0:
            group_fare = float(p.group_fare_override)
        elif p.discount_type == 'percentage':
            discount_amount = (base_fare * float(p.discount_value)) / 100.0
            group_fare = max(0.0, base_fare - discount_amount)
        else:
            group_fare = max(0.0, base_fare - float(p.discount_value))

        data.append({
            'id':                       p.id,
            'flight_inventory_id':      fi.id if fi else None,
            'airline_name':             airline_name,
            'airline_logo_url':         airline_logo_url,
            'departure_city':           dep_city,
            'destination_city':         dest_city,
            'departure_time':           dep_time,
            'arrival_time':             arr_time,
            'trip_type':                trip_type,
            'trip_type_display':        'Round Trip Group' if trip_type == 'return' else 'One Way Group',
            'route_type':               route_type,
            'route_type_display':       'Via ' + via_city if route_type == 'via' else 'Non-Stop Direct',
            'via_city':                 via_city,
            'has_meal':                 has_meal,
            'meal_display':             'In-flight Meal Included' if has_meal else 'No Meal',
            'return_departure_time':   ret_dep_time,
            'return_arrival_time':     ret_arr_time,
            'return_route_type':       ret_route_type,
            'return_via_city':         ret_via_city,
            'total_seats':              total_seats,
            'available_seats':          avail_seats,
            'min_group_size':           p.min_group_size,
            'discount_type':            p.discount_type,
            'discount_type_display':    p.get_discount_type_display(),
            'discount_value':           float(p.discount_value),
            'baggage_weight_kg':        p.baggage_weight_kg,
            'return_baggage_weight_kg': p.return_baggage_weight_kg,
            'base_fare':                round(base_fare, 2),
            'group_fare':               round(group_fare, 2),
            'route_display':            f"{airline_name} — {dep_city} → {dest_city} ({dep_time})",
        })
    return JsonResponse({'success': True, 'policies': data})


@admin_required_api
@csrf_exempt
def admin_group_fare_policies_api(request):
    """
    GET  → List all group fare policies / standalone group tickets for Admin
    POST → Create a standalone or linked group fare ticket
    """
    if request.method == 'GET':
        policies = GroupFarePolicy.objects.select_related('flight_inventory', 'flight_inventory__airline', 'airline').all()
        data = []
        for p in policies:
            fi = p.flight_inventory
            if fi:
                air_name = fi.airline.name if fi.airline else 'Airline'
                air_logo = fi.airline.logo.url if (fi.airline and fi.airline.logo) else ''
                dep = fi.departure_city
                dest = fi.destination_city
                d_time = fi.departure_time
                a_time = fi.arrival_time
                t_type = fi.trip_type
                r_type = fi.route_type
                v_city = fi.via_city or ''
                meal = fi.has_meal
                t_seats = fi.total_seats
                a_seats = fi.available_seats
                ret_d_time = fi.return_departure_time or ''
                ret_a_time = fi.return_arrival_time or ''
                tier = fi.baggage_tiers.filter(weight_kg=p.baggage_weight_kg).first() or fi.baggage_tiers.first()
                b_fare = float(tier.fare) if tier else float(getattr(p, 'base_fare', None) or 0.0)
            else:
                air_name = p.airline.name if p.airline else (p.airline_name_custom or 'Group Ticket')
                air_logo = p.airline.logo.url if (p.airline and p.airline.logo) else ''
                dep = p.departure_city or ''
                dest = p.destination_city or ''
                d_time = p.departure_time or ''
                a_time = p.arrival_time or ''
                t_type = p.trip_type or 'oneway'
                r_type = p.route_type or 'direct'
                v_city = p.via_city or ''
                meal = p.has_meal
                t_seats = p.total_seats
                a_seats = p.available_seats
                ret_d_time = p.return_departure_time or ''
                ret_a_time = p.return_arrival_time or ''
                b_fare = float(getattr(p, 'base_fare', None) or 0.0)

            group_override = getattr(p, 'group_fare_override', None)
            if group_override is not None and float(group_override) > 0:
                g_fare = float(group_override)
            elif p.discount_type == 'percentage':
                disc_amt = (b_fare * float(p.discount_value)) / 100.0
                g_fare = max(0.0, b_fare - disc_amt)
            else:
                g_fare = max(0.0, b_fare - float(p.discount_value))

            route_sec = getattr(p, 'route_sectors', None) or p.sectors_data or []

            data.append({
                'id':                       p.id,
                'flight_inventory_id':      fi.id if fi else None,
                'airline_id':               p.airline_id if p.airline else (fi.airline_id if fi else None),
                'airline_name':             air_name,
                'airline_logo_url':         air_logo,
                'airline_name_custom':      p.airline_name_custom or '',
                'departure_city':           dep,
                'destination_city':         dest,
                'departure_time':           d_time,
                'arrival_time':             a_time,
                'return_departure_time':   ret_d_time,
                'return_arrival_time':     ret_a_time,
                'trip_type':                t_type,
                'route_type':               r_type,
                'via_city':                 v_city,
                'has_meal':                 meal,
                'total_seats':              t_seats,
                'available_seats':          a_seats,
                'min_group_size':           p.min_group_size,
                'discount_type':            p.discount_type,
                'discount_value':           float(p.discount_value),
                'baggage_weight_kg':        p.baggage_weight_kg,
                'return_baggage_weight_kg': p.return_baggage_weight_kg,
                'base_fare':                round(b_fare, 2),
                'group_fare_override':      float(group_override) if group_override is not None else None,
                'group_fare':               round(g_fare, 2),
                'route_sectors':            route_sec,
                'is_active':                p.is_active,
                'route_display':            f"{air_name} — {dep} ➔ {dest}",
                'sectors_data':             p.sectors_data or (fi.sectors_data if fi else {}),
            })
        return JsonResponse({'success': True, 'policies': data})

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body)
            airline_id = payload.get('airline_id')
            airline_obj = Airline.objects.filter(id=airline_id).first() if airline_id else None

            sectors_data = payload.get('sectors_data') or payload.get('route_sectors') or {}
            going_sectors = sectors_data.get('going', []) if isinstance(sectors_data, dict) else []
            coming_sectors = sectors_data.get('coming', []) if isinstance(sectors_data, dict) else []

            dep_time = payload.get('departure_time') or (going_sectors[0].get('dep_time') if going_sectors else '')
            arr_time = payload.get('arrival_time') or (going_sectors[-1].get('arr_time') if going_sectors else '')
            ret_dep_time = payload.get('return_departure_time') or (coming_sectors[0].get('dep_time') if coming_sectors else '')
            ret_arr_time = payload.get('return_arrival_time') or (coming_sectors[-1].get('arr_time') if coming_sectors else '')

            net_fare_val = payload.get('group_fare_override') or payload.get('base_fare') or 0

            p = GroupFarePolicy.objects.create(
                airline=airline_obj,
                airline_name_custom=payload.get('airline_name_custom', ''),
                departure_city=payload.get('departure_city', ''),
                destination_city=payload.get('destination_city', ''),
                departure_time=dep_time or '',
                arrival_time=arr_time or '',
                return_departure_time=ret_dep_time or '',
                return_arrival_time=ret_arr_time or '',
                trip_type=payload.get('trip_type', 'oneway'),
                route_type=payload.get('route_type', 'direct'),
                via_city=payload.get('via_city', ''),
                has_meal=bool(payload.get('has_meal', True)),
                total_seats=int(payload.get('total_seats', 50)),
                available_seats=int(payload.get('available_seats', 50)),
                min_group_size=int(payload.get('min_group_size', 10)),
                discount_type=payload.get('discount_type', 'flat'),
                discount_value=Decimal(str(payload.get('discount_value', 0))),
                baggage_weight_kg=int(payload.get('baggage_weight_kg', 30)),
                return_baggage_weight_kg=int(payload.get('return_baggage_weight_kg', 30)),
                base_fare=Decimal(str(net_fare_val)),
                group_fare_override=Decimal(str(net_fare_val)) if net_fare_val not in [None, ''] else None,
                is_active=bool(payload.get('is_active', True)),
                sectors_data=sectors_data
            )
            return JsonResponse({'success': True, 'policy_id': p.id, 'message': 'Group ticket created successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@admin_required_api
@csrf_exempt
def admin_group_fare_policy_detail_api(request, pk):
    """
    GET    → Get single GroupFarePolicy detail
    PUT    → Update GroupFarePolicy
    DELETE → Delete GroupFarePolicy
    """
    policy = get_object_or_404(GroupFarePolicy, pk=pk)

    if request.method == 'GET':
        fi = policy.flight_inventory
        return JsonResponse({
            'success': True,
            'policy': {
                'id':                       policy.id,
                'airline_id':               policy.airline_id if policy.airline else (fi.airline_id if fi else None),
                'airline_name_custom':      policy.airline_name_custom or '',
                'departure_city':           policy.departure_city or (fi.departure_city if fi else ''),
                'destination_city':         policy.destination_city or (fi.destination_city if fi else ''),
                'departure_time':           policy.departure_time or (fi.departure_time if fi else ''),
                'arrival_time':             policy.arrival_time or (fi.arrival_time if fi else ''),
                'return_departure_time':   policy.return_departure_time or (fi.return_departure_time if fi else ''),
                'return_arrival_time':     policy.return_arrival_time or (fi.return_arrival_time if fi else ''),
                'trip_type':                policy.trip_type or (fi.trip_type if fi else 'oneway'),
                'route_type':               policy.route_type or (fi.route_type if fi else 'direct'),
                'via_city':                 policy.via_city or (fi.via_city if fi else ''),
                'has_meal':                 policy.has_meal if fi is None else fi.has_meal,
                'total_seats':              policy.total_seats if fi is None else fi.total_seats,
                'available_seats':          policy.available_seats if fi is None else fi.available_seats,
                'min_group_size':           policy.min_group_size,
                'discount_type':            policy.discount_type,
                'discount_value':           float(policy.discount_value),
                'baggage_weight_kg':        policy.baggage_weight_kg,
                'return_baggage_weight_kg': policy.return_baggage_weight_kg,
                'base_fare':                float(policy.base_fare or (fi.base_fare if fi else 0)),
                'group_fare_override':      float(policy.group_fare_override) if policy.group_fare_override is not None else float(policy.base_fare or 0),
                'is_active':                policy.is_active,
                'sectors_data':             policy.sectors_data or (fi.sectors_data if fi else {}),
            }
        })

    elif request.method == 'PUT':
        try:
            payload = json.loads(request.body)
            airline_id = payload.get('airline_id')
            if airline_id:
                policy.airline = Airline.objects.filter(id=airline_id).first()
            if 'airline_name_custom' in payload: policy.airline_name_custom = payload['airline_name_custom']
            if 'departure_city' in payload: policy.departure_city = payload['departure_city']
            if 'destination_city' in payload: policy.destination_city = payload['destination_city']
            if 'departure_time' in payload: policy.departure_time = payload['departure_time']
            if 'arrival_time' in payload: policy.arrival_time = payload['arrival_time']
            if 'return_departure_time' in payload: policy.return_departure_time = payload['return_departure_time']
            if 'return_arrival_time' in payload: policy.return_arrival_time = payload['return_arrival_time']
            if 'trip_type' in payload: policy.trip_type = payload['trip_type']
            if 'route_type' in payload: policy.route_type = payload['route_type']
            if 'via_city' in payload: policy.via_city = payload['via_city']
            if 'has_meal' in payload: policy.has_meal = bool(payload['has_meal'])
            if 'total_seats' in payload: policy.total_seats = int(payload['total_seats'])
            if 'available_seats' in payload: policy.available_seats = int(payload['available_seats'])
            if 'min_group_size' in payload: policy.min_group_size = int(payload['min_group_size'])
            if 'discount_type' in payload: policy.discount_type = payload['discount_type']
            if 'discount_value' in payload: policy.discount_value = Decimal(str(payload['discount_value']))
            if 'baggage_weight_kg' in payload: policy.baggage_weight_kg = int(payload['baggage_weight_kg'])
            if 'return_baggage_weight_kg' in payload: policy.return_baggage_weight_kg = int(payload['return_baggage_weight_kg'])
            
            if 'group_fare_override' in payload or 'base_fare' in payload:
                net_val = payload.get('group_fare_override') or payload.get('base_fare') or 0
                policy.base_fare = Decimal(str(net_val))
                policy.group_fare_override = Decimal(str(net_val)) if net_val not in [None, ''] else None

            if 'is_active' in payload: policy.is_active = bool(payload['is_active'])
            if 'sectors_data' in payload or 'route_sectors' in payload:
                sec = payload.get('sectors_data') or payload.get('route_sectors') or {}
                policy.sectors_data = sec
                if isinstance(sec, dict):
                    going_sec = sec.get('going', [])
                    coming_sec = sec.get('coming', [])
                    if going_sec and not policy.departure_time:
                        policy.departure_time = going_sec[0].get('dep_time', '')
                    if going_sec and not policy.arrival_time:
                        policy.arrival_time = going_sec[-1].get('arr_time', '')
                    if coming_sec and not policy.return_departure_time:
                        policy.return_departure_time = coming_sec[0].get('dep_time', '')
                    if coming_sec and not policy.return_arrival_time:
                        policy.return_arrival_time = coming_sec[-1].get('arr_time', '')

            policy.save()
            return JsonResponse({'success': True, 'message': 'Group ticket updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    elif request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'Group ticket deleted successfully!'})


@admin_required_api
@csrf_exempt
def admin_adjust_group_seats_api(request, pk):
    """
    POST → Quickly increment (+) or decrement (-) available_seats & total_seats for a Standalone / Linked Group Ticket
    Payload: { "action": "increment" | "decrement", "amount": 1 }
    """
    policy = get_object_or_404(GroupFarePolicy, pk=pk)
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            action = payload.get('action', 'increment')
            amount = int(payload.get('amount', 1))

            if action == 'increment':
                policy.available_seats += amount
                policy.total_seats += amount
            elif action == 'decrement':
                policy.available_seats = max(0, policy.available_seats - amount)
                policy.total_seats = max(0, policy.total_seats - amount)

            if policy.flight_inventory:
                if action == 'increment':
                    policy.flight_inventory.available_seats += amount
                    policy.flight_inventory.total_seats += amount
                elif action == 'decrement':
                    policy.flight_inventory.available_seats = max(0, policy.flight_inventory.available_seats - amount)
                    policy.flight_inventory.total_seats = max(0, policy.flight_inventory.total_seats - amount)
                policy.flight_inventory.save()

            policy.save()
            return JsonResponse({
                'success': True,
                'available_seats': policy.available_seats,
                'total_seats': policy.total_seats,
                'message': f"Seats {action}ed by {amount}. New available: {policy.available_seats}"
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@agent_required_api
def agent_packages_api(request):
    """
    GET → List active agent packages (supports ?type=umrah or ?type=hajj)
    Exposes available_seats, total_seats, booked_seats
    """
    pkg_type = request.GET.get('type', '').strip().lower()
    packages = AgentPackage.objects.filter(is_active=True).select_related('airline', 'sector').prefetch_related('hotels').all()
    if pkg_type in ['umrah', 'hajj']:
        packages = packages.filter(package_type=pkg_type)

    data = []
    for p in packages:
        data.append({
            'id':                       p.id,
            'package_type':             p.package_type,
            'package_type_display':     p.get_package_type_display(),
            'sector_id':                p.sector_id,
            'sector_name':              p.sector.name if (p.sector and p.sector.name) else (f"{p.sector.origin_city} ➔ {p.sector.destination_city}" if p.sector else (p.flight_route or None)),
            'title':                    p.title,
            'description':              p.description,
            'duration_days':            p.duration_days,
            'agent_price':              str(p.agent_price),
            'suggested_resale_price':   str(p.suggested_resale_price) if p.suggested_resale_price else '',
            'commission_amount':        str(p.commission_amount) if p.commission_amount else '',
            'adult_price':              str(p.adult_price) if p.adult_price is not None else str(p.agent_price),
            'child_price':              str(p.child_price) if p.child_price is not None else str(p.agent_price),
            'infant_price':              str(p.infant_price) if p.infant_price is not None else '0.00',
            'price_sharing':            str(p.price_sharing) if p.price_sharing is not None else str(p.agent_price),
            'price_quad':               str(p.price_quad) if p.price_quad is not None else str(p.agent_price),
            'price_triple':             str(p.price_triple) if p.price_triple is not None else str(p.agent_price),
            'price_double':             str(p.price_double) if p.price_double is not None else str(p.agent_price),
            'flight_name':              p.flight_name or (p.airline.name if p.airline else 'Saudi Airlines'),
            'flight_route_type':        p.flight_route_type or 'direct',
            'flight_route_type_display':'Direct Flight' if (p.flight_route_type or 'direct') == 'direct' else 'Via Flight',
            'flight_route':             p.flight_route or 'KHI - JED - MED - KHI',
            'includes_meal':            p.includes_meal,
            'meal_display':             'Yes' if p.includes_meal else 'No',
            'meal_detail':              p.meal_detail or 'Full Board',
            'transport_type':           p.transport_type or 'Sharing',
            'departure_date':           p.departure_date.strftime('%Y-%m-%d') if p.departure_date else '',
            'return_date':              p.return_date.strftime('%Y-%m-%d') if p.return_date else '',
            'hotel_ids':                list(p.hotels.values_list('id', flat=True)),
            'hotels':                   [{'id': h.id, 'name': h.name, 'city': h.city, 'city_display': h.get_city_display(), 'distance_from_haram': h.distance_from_haram, 'price_sharing': float(h.price_sharing) if h.price_sharing is not None else None, 'price_quad': float(h.price_quad) if h.price_quad is not None else None, 'price_triple': float(h.price_triple) if h.price_triple is not None else None, 'price_double': float(h.price_double) if h.price_double is not None else None} for h in p.hotels.all()],
            'total_seats':              p.total_seats,
            'booked_seats':             p.booked_seats,
            'available_seats':          p.available_seats,
            'makkah_hotel_name':        p.makkah_hotel_name or '',
            'makkah_hotel_distance':    p.makkah_hotel_distance or '',
            'makkah_nights':            p.makkah_nights,
            'madinah_hotel_name':       p.madinah_hotel_name or '',
            'madinah_hotel_distance':   p.madinah_hotel_distance or '',
            'madinah_nights':           p.madinah_nights,
            'airline_name':             (p.airline.name if p.airline else None) or p.flight_name or '',
            'airline_logo_url':         p.airline.logo.url if (p.airline and p.airline.logo) else None,
            'images':                   p.images or [],
            'cover_photo':              p.cover_photo.url if p.cover_photo else '',
            'cover_photo_url':          p.cover_photo_url,
        })
    return JsonResponse({'success': True, 'packages': data})


@user_passes_test(is_agent)
def agent_sectors_api(request):
    """
    GET → List active flight/package sectors defined by admin for agent portal
    """
    sectors = Sector.objects.filter(is_active=True).order_by('name')
    data = []
    for s in sectors:
        data.append({
            'id': s.id,
            'name': s.name or f"{s.origin_city} ➔ {s.destination_city}",
            'origin_city': s.origin_city,
            'destination_city': s.destination_city,
            'is_round_trip': s.is_round_trip,
        })
    return JsonResponse({'success': True, 'sectors': data})


@agent_required_api
def agent_airlines_api(request):
    """
    GET → List active airlines for agent portal ticket search toolbar
    """
    airlines = Airline.objects.filter(is_active=True).order_by('name')
    data = [{
        'id': a.id,
        'name': a.name,
        'code': a.iata_code or '',
        'logo_url': _safe_airline_logo_url(a),
    } for a in airlines]
    return JsonResponse({'success': True, 'airlines': data})


@agent_required_api
def agent_flight_inventory_api(request):
    """
    GET → List active flight inventories for agent portal (flight tickets)
    Calculates available_seats = total_seats - booked_seats
    """
    from django.db.models import Q
    airline_id = request.GET.get('airline_id', '').strip()
    trip_type = request.GET.get('trip_type', '').strip()
    search = request.GET.get('search', '').strip()
    sector_id = request.GET.get('sector_id', '').strip()

    inventories = AirlineFlightInventory.objects.filter(is_active=True).select_related('airline', 'sector').prefetch_related('baggage_tiers').all()

    if airline_id:
        inventories = inventories.filter(airline_id=airline_id)

    if sector_id:
        inventories = inventories.filter(sector_id=sector_id)

    if trip_type and trip_type != 'all':
        if trip_type == 'oneway':
            inventories = inventories.filter(Q(trip_type='oneway') | Q(trip_type='one_way'))
        elif trip_type == 'return':
            inventories = inventories.filter(Q(trip_type='return') | Q(trip_type='round_trip'))
        else:
            inventories = inventories.filter(trip_type=trip_type)

    if search:
        inventories = inventories.filter(
            Q(departure_city__icontains=search) |
            Q(destination_city__icontains=search) |
            Q(airline__name__icontains=search) |
            Q(sector__name__icontains=search) |
            Q(via_city__icontains=search)
        )

    data = []
    for fi in inventories:
        avail = max(0, fi.total_seats - fi.booked_seats)
        baggage_tiers = [{'id': b.id, 'weight_kg': b.weight_kg, 'fare': str(b.fare)} for b in fi.baggage_tiers.all()]
        first_fare = baggage_tiers[0]['fare'] if baggage_tiers else '140000.00'
        base_fare_str = str(getattr(fi, 'base_fare', first_fare))
        data.append({
            'id':                     fi.id,
            'sector_id':              fi.sector_id,
            'sector_name':            fi.sector.name if fi.sector else None,
            'airline_id':             fi.airline_id,
            'airline_name':           fi.airline.name if fi.airline else '',
            'airline_iata_code':      fi.airline.iata_code if (fi.airline and getattr(fi.airline, 'iata_code', None)) else '',
            'airline_logo_url':       _safe_airline_logo_url(fi),
            'departure_city':         fi.departure_city,
            'destination_city':       fi.destination_city,
            'departure_time':         fi.departure_time,
            'arrival_time':           fi.arrival_time,
            'return_departure_time': fi.return_departure_time or '',
            'return_arrival_time':   fi.return_arrival_time or '',
            'trip_type':              fi.trip_type,
            'trip_type_display':      fi.get_trip_type_display(),
            'route_type':             fi.route_type,
            'route_type_display':     fi.get_route_type_display(),
            'via_city':               fi.via_city or '',
            'has_meal':               fi.has_meal,
            'base_fare':              base_fare_str,
            'total_seats':            fi.total_seats,
            'booked_seats':           fi.booked_seats,
            'available_seats':        avail,
            'sectors_data':           fi.sectors_data if fi.sectors_data else [],
            'baggage_tiers':          baggage_tiers,
        })
    return JsonResponse({'success': True, 'inventory': data})


@agent_required_api
def agent_group_fare_policies_api(request):
    """
    GET → List active B2B group ticket policies for agent portal
    Supports both standalone group tickets and inventory-linked group policies.
    """
    policies = GroupFarePolicy.objects.filter(is_active=True).select_related('airline', 'flight_inventory', 'flight_inventory__airline').all()
    data = []
    for p in policies:
        fi = p.flight_inventory
        air_name = p.airline_name_custom or (p.airline.name if p.airline else (fi.airline.name if (fi and fi.airline) else 'Saudi Airlines'))
        air_logo = _safe_airline_logo_url(p) or _safe_airline_logo_url(fi)
        
        dep = p.departure_city or (fi.departure_city if fi else 'Karachi')
        dest = p.destination_city or (fi.destination_city if fi else 'Jeddah')
        d_time = p.departure_time or (fi.departure_time if fi else '10:00 AM')
        a_time = p.arrival_time or (fi.arrival_time if fi else '02:00 PM')
        ret_d_time = p.return_departure_time or (fi.return_departure_time if fi else '')
        ret_a_time = p.return_arrival_time or (fi.return_arrival_time if fi else '')
        
        t_type = p.trip_type or (fi.trip_type if fi else 'oneway')
        r_type = p.route_type or (fi.route_type if fi else 'direct')
        v_city = p.via_city or (fi.via_city if fi else '')
        meal = p.has_meal if fi is None else fi.has_meal

        t_seats = p.total_seats if fi is None else fi.total_seats
        a_seats = p.available_seats if fi is None else max(0, fi.total_seats - fi.booked_seats)

        b_fare = float(getattr(p, 'base_fare', None) or (fi.base_fare if (fi and hasattr(fi, 'base_fare')) else 0))
        group_override = getattr(p, 'group_fare_override', None)
        if group_override is not None and float(group_override) > 0:
            g_fare = float(group_override)
        elif p.discount_type == 'percentage':
            g_fare = max(0.0, b_fare - (b_fare * float(p.discount_value) / 100.0))
        else:
            g_fare = max(0.0, b_fare - float(p.discount_value))

        route_sec = getattr(p, 'route_sectors', None) or p.sectors_data or []

        data.append({
            'id':                       p.id,
            'flight_inventory_id':      fi.id if fi else None,
            'airline_id':               p.airline_id if p.airline else (fi.airline_id if fi else None),
            'airline_name':             air_name,
            'airline_logo_url':         air_logo,
            'departure_city':           dep,
            'destination_city':         dest,
            'departure_time':           d_time,
            'arrival_time':             a_time,
            'return_departure_time':   ret_d_time,
            'return_arrival_time':     ret_a_time,
            'trip_type':                t_type,
            'route_type':               r_type,
            'via_city':                 v_city,
            'has_meal':                 meal,
            'total_seats':              t_seats,
            'available_seats':          a_seats,
            'min_group_size':           p.min_group_size,
            'discount_type':            p.discount_type,
            'discount_value':           float(p.discount_value),
            'baggage_weight_kg':        p.baggage_weight_kg,
            'return_baggage_weight_kg': p.return_baggage_weight_kg,
            'base_fare':                round(b_fare, 2),
            'group_fare_override':      float(group_override) if group_override is not None else None,
            'group_fare':               round(g_fare, 2),
            'route_sectors':            route_sec,
            'is_active':                p.is_active,
            'route_display':            f"{air_name} — {dep} ➔ {dest}",
            'sectors_data':             p.sectors_data or (fi.sectors_data if fi else {}),
        })
    return JsonResponse({'success': True, 'policies': data})


def get_agent_wallet_balance(agent):
    from ..accounts.models import AgentLedger
    from django.db.models import Sum
    entries = AgentLedger.objects.filter(agent=agent)
    credit_total = entries.filter(entry_type='credit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    debit_total = entries.filter(entry_type='debit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    return Decimal(str(credit_total)) - Decimal(str(debit_total))


def generate_reference_number():
    year = timezone.now().year
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"GSA-{year}-{suffix}"


def generate_pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_ticket_number(airline_code=""):
    suffix = ''.join(random.choices(string.digits, k=10))
    return f"{airline_code}{suffix}" if airline_code else suffix


def calculate_order_total_fare(order_type, flight_inventory, agent_package,
                                baggage_weight_kg, passenger_count, booking_type=None, passengers_data=None, selected_sharing_type=None):
    """
    Recalculates total fare server-side, ignoring client payload.
    Supports ticket, group (with GroupFarePolicy discount), and umrah/hajj packages (per adult/child/infant & room sharing).
    """
    if order_type in ('ticket', 'group'):
        tier = BaggageFareTier.objects.filter(
            flight_inventory=flight_inventory,
            weight_kg=baggage_weight_kg
        ).first()
        if not tier:
            tier = BaggageFareTier.objects.filter(flight_inventory=flight_inventory).order_by('weight_kg').first()
        if not tier:
            raise BaggageFareTier.DoesNotExist("No baggage fare tier found for this flight route.")

        base_fare = Decimal(str(tier.fare)) * Decimal(str(passenger_count))

        if order_type == 'group':
            policy = GroupFarePolicy.objects.filter(
                flight_inventory=flight_inventory,
                is_active=True
            )
            if baggage_weight_kg:
                policy = policy.filter(baggage_weight_kg=baggage_weight_kg)
            
            p = policy.first()
            if not p:
                p = GroupFarePolicy.objects.filter(
                    flight_inventory=flight_inventory,
                    is_active=True
                ).first()

            if p:
                if p.discount_type == 'percentage':
                    disc = Decimal(str(p.discount_value))
                    base_fare -= base_fare * (disc / Decimal('100'))
                else:  # flat
                    disc = Decimal(str(p.discount_value))
                    base_fare -= disc * Decimal(str(passenger_count))
        return base_fare

    elif order_type in ('umrah', 'hajj'):
        if passengers_data and isinstance(passengers_data, list):
            adult_count = sum(1 for p in passengers_data if str(p.get('passenger_type', '')).lower() == 'adult')
            child_count = sum(1 for p in passengers_data if str(p.get('passenger_type', '')).lower() == 'child')
            infant_count = sum(1 for p in passengers_data if str(p.get('passenger_type', '')).lower() == 'infant')
            if adult_count == 0 and child_count == 0 and infant_count == 0:
                adult_count = passenger_count
        else:
            adult_count = passenger_count
            child_count = 0
            infant_count = 0

        # Selected room occupancy pricing (sharing, quad, triple, double)
        base_room_price = None
        st = str(selected_sharing_type or '').strip().lower()
        if agent_package:
            if st == 'quad' and getattr(agent_package, 'price_quad', None) is not None:
                base_room_price = agent_package.price_quad
            elif st == 'triple' and getattr(agent_package, 'price_triple', None) is not None:
                base_room_price = agent_package.price_triple
            elif st == 'double' and getattr(agent_package, 'price_double', None) is not None:
                base_room_price = agent_package.price_double
            elif st == 'sharing' and getattr(agent_package, 'price_sharing', None) is not None:
                base_room_price = agent_package.price_sharing

            if base_room_price is None:
                base_room_price = getattr(agent_package, 'agent_price', 0) or getattr(agent_package, 'price_sharing', 0) or 0

            adult_price = Decimal(str(getattr(agent_package, 'adult_price', None) or base_room_price))
            child_price = Decimal(str(getattr(agent_package, 'child_price', None) or base_room_price))
            infant_price = Decimal(str(getattr(agent_package, 'infant_price', None) or '0.00'))
        else:
            adult_price = Decimal('0.00')
            child_price = Decimal('0.00')
            infant_price = Decimal('0.00')

        return (Decimal(str(adult_count)) * adult_price) + (Decimal(str(child_count)) * child_price) + (Decimal(str(infant_count)) * infant_price)

    raise ValueError(f"Unknown order_type: {order_type}")


def issue_pnr_and_tickets_for_order(order):
    """
    Atomically generates a 6-character PNR and 10-digit ticket numbers for flight orders,
    or confirms package bookings using reference_number as confirmation code.
    Sets order status to 'paid' and sends email notifications.
    Shared by admin confirmation and instant wallet payment paths.
    """
    pnr = None
    if order.order_type in ('ticket', 'group'):
        pnr = generate_pnr()
        order.pnr = pnr
        airline_code = order.flight_inventory.airline.name[:3].upper() if (order.flight_inventory and order.flight_inventory.airline) else ""
        for passenger in order.passengers.all():
            if not passenger.allotted_ticket_number:
                passenger.allotted_ticket_number = generate_ticket_number(airline_code)
                passenger.save()

    order.status = 'paid'
    order.save()

    try:
        from ..accounts.views import build_professional_email_html, _dispatch_email
        from django.conf import settings
        
        if order.order_type in ('umrah', 'hajj'):
            subject = f"Package Booking Confirmation — Ref: {order.reference_number}"
            body_html = f"""
            <p>Your package booking order <strong>{order.reference_number}</strong> has been successfully <strong>CONFIRMED</strong> by <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong></p>
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
                <h4 style="margin: 0 0 10px 0; color: #ea580c; font-size: 14px; text-transform: uppercase;">Booking Summary</h4>
                <p style="margin: 0 0 4px 0;"><strong>Reference Number:</strong> {order.reference_number}</p>
                <p style="margin: 0 0 4px 0;"><strong>Package:</strong> {order.package.title if hasattr(order, 'package') and order.package else 'Pilgrimage Package'}</p>
                <p style="margin: 0;"><strong>Total Fare Paid:</strong> PKR {order.total_fare}</p>
            </div>
            <p>You can print your official package voucher anytime from your dashboard portal.</p>
            """
        else:
            subject = f"Booking Confirmation & E-Ticket — PNR: {pnr} ({order.reference_number})"
            body_html = f"""
            <p>Your flight booking order <strong>{order.reference_number}</strong> has been successfully <strong>CONFIRMED</strong> by <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong></p>
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
                <h4 style="margin: 0 0 10px 0; color: #ea580c; font-size: 14px; text-transform: uppercase;">E-Ticket Details</h4>
                <p style="margin: 0 0 4px 0; font-size: 16px; color: #ea580c;"><strong>PNR Code:</strong> <span style="font-family: monospace; font-weight: 900;">{pnr}</span></p>
                <p style="margin: 0 0 4px 0;"><strong>Reference:</strong> {order.reference_number}</p>
                <p style="margin: 0;"><strong>Total Fare Paid:</strong> PKR {order.total_fare}</p>
            </div>
            <p>You can print your official E-Ticket receipt anytime from your dashboard portal.</p>
            """
            
        recipients = list(set([email.strip() for email in [order.agent_contact_email, order.traveler_contact_email] if email and email.strip()]))
        if recipients:
            html_email = build_professional_email_html(subject, None, body_html, "View Dashboard Portal", "http://127.0.0.1:8000/auth/login/")
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')
            _dispatch_email(subject, f"Booking confirmation for {order.reference_number}", from_email, recipients, html_message=html_email)
    except Exception as e:
        print(f"[Email Error] Booking confirmation failed: {e}")

    return pnr or order.reference_number


def send_b2b_order_notification_email(order, event_type='created'):
    """
    Automated email dispatcher for B2B Agent orders & Admin Panel alerts.
    Events:
    - 'created': Sent to Admin & Agent when order is placed (hold or paid).
    - 'paid': Sent to Admin & Agent when agent pays for an order.
    - 'ticketed': Sent to Agent & Traveler when order is confirmed/ticketed by admin.
    """
    try:
        from ..accounts.views import build_professional_email_html, _dispatch_email
        from ..accounts.models import User
        from django.conf import settings

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None) or 'goldenstartraveltours@gmail.com'

        # Gather Admin emails
        admin_emails = set()
        default_admin = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
        if default_admin and default_admin.strip():
            admin_emails.add(default_admin.strip())
        
        try:
            superadmin_list = User.objects.filter(is_superuser=True, is_active=True).values_list('email', flat=True)
            for em in superadmin_list:
                if em and em.strip():
                    admin_emails.add(em.strip())
        except Exception:
            pass
        
        admin_recipients = list(admin_emails)

        agent_email = (order.agent_contact_email or (order.agent.email if order.agent else '') or '').strip()
        traveler_email = (order.traveler_contact_email or '').strip()
        agent_name = order.agent.get_full_name() if (order.agent and hasattr(order.agent, 'get_full_name')) else (order.agent.username if order.agent else 'Partner Agent')
        agency_name = getattr(order.agent, 'company_name', '') if order.agent else ''

        # Passengers list string
        pax_list = list(order.passengers.all())
        pax_names = ", ".join([f"{p.title} {p.first_name} {p.last_name}".strip() for p in pax_list]) if pax_list else f"{order.passenger_count or 1} Passenger(s)"

        # Item title
        if order.flight_inventory:
            item_title = f"Flight: {order.flight_inventory.airline_name} ({order.flight_inventory.departure_city} ➔ {order.flight_inventory.destination_city})"
        elif order.agent_package:
            item_title = f"Umrah Package: {order.agent_package.title}"
        elif order.agent_hajj_package:
            item_title = f"Hajj Package: {order.agent_hajj_package.title}"
        elif order.group_policy:
            item_title = f"Group Fare Policy #{order.group_policy.id}"
        else:
            item_title = "B2B Ticket / Package Booking"

        ref_no = order.reference_number or f"#{order.id}"
        status_disp = order.get_status_display().upper()

        if event_type in ('created', 'paid'):
            # 1. Admin Email Alert
            subject_admin = f"B2B Order Alert [{ref_no}] — {status_disp} ({agency_name or agent_name})"
            body_admin_html = f"""
            <p>A B2B booking order <strong>#{ref_no}</strong> has been {event_type} by partner agent <strong>{agent_name}</strong> ({agency_name or 'N/A'}).</p>
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 16px 0;">
                <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 14px; text-transform: uppercase;">Order Summary</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr><td style="padding: 4px 0; color: #64748b;">Order Ref #:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{ref_no}</td></tr>
                    <tr><td style="padding: 4px 0; color: #64748b;">Status:</td><td style="padding: 4px 0; font-weight: bold; color: #ea580c; text-align: right;">{status_disp}</td></tr>
                    <tr><td style="padding: 4px 0; color: #64748b;">Service / Item:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{item_title}</td></tr>
                    <tr><td style="padding: 4px 0; color: #64748b;">Passengers:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{pax_names}</td></tr>
                    <tr><td style="padding: 4px 0; color: #64748b;">Agent Contact:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{order.agent_phone_number or 'N/A'} ({agent_email})</td></tr>
                    <tr style="border-top: 1px solid #e2e8f0;"><td style="padding: 8px 0 4px 0; color: #0f172a; font-weight: bold;">Total Amount:</td><td style="padding: 8px 0 4px 0; font-weight: 900; color: #ea580c; font-size: 16px; text-align: right;">PKR {float(order.total_fare):,.2f}</td></tr>
                </table>
            </div>
            <p>Log in to the Golden Star Admin Dashboard to manage this order and allot ticket numbers / PNR.</p>
            """
            if admin_recipients:
                html_admin = build_professional_email_html("B2B Order Alert", "Golden Star Admin", body_admin_html, "Manage Orders in Admin Panel", "http://127.0.0.1:8000/dashboard/admin/")
                _dispatch_email(subject_admin, f"B2B Order Alert {ref_no}", from_email, admin_recipients, html_message=html_admin)

            # 2. Agent Email Confirmation
            if agent_email:
                subject_agent = f"B2B Order Confirmation — Ref: #{ref_no} [{status_disp}]"
                body_agent_html = f"""
                <p>Assalamu Alaikum <strong>{agent_name}</strong>,</p>
                <p>Your B2B booking order <strong>#{ref_no}</strong> has been successfully placed in our system.</p>
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 16px 0;">
                    <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 14px; text-transform: uppercase;">Booking Details</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr><td style="padding: 4px 0; color: #64748b;">Reference #:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{ref_no}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Service:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{item_title}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Passengers:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{pax_names}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Total Fare:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">PKR {float(order.total_fare):,.2f}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Status:</td><td style="padding: 4px 0; font-weight: bold; color: #ea580c; text-align: right;">{status_disp}</td></tr>
                    </table>
                </div>
                <p>You can track order status or print official vouchers anytime from your B2B Agent Dashboard.</p>
                """
                html_agent = build_professional_email_html("B2B Order Confirmation", agent_name, body_agent_html, "View Order Dashboard", "http://127.0.0.1:8000/dashboard/agent/")
                _dispatch_email(subject_agent, f"B2B Order #{ref_no} Confirmation", from_email, [agent_email], html_message=html_agent)

        elif event_type in ('ticketed', 'confirmed', 'paid_pending'):
            # 3. Confirmation alert to Agent & Traveler
            recipients = list(set([e for e in [agent_email, traveler_email] if e]))
            if recipients:
                subject_confirm = f"B2B Order #{ref_no} Confirmed and Ticketed — Golden Star Travel"
                pnr_str = order.pnr or 'Confirmed'
                body_confirm_html = f"""
                <p>Your B2B booking order <strong>#{ref_no}</strong> has been <strong>CONFIRMED & TICKETED</strong> by <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong></p>
                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 16px 0;">
                    <h4 style="margin: 0 0 12px 0; color: #166534; font-size: 14px; text-transform: uppercase;">Ticket & Reservation Summary</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr><td style="padding: 4px 0; color: #64748b;">Reference #:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{ref_no}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">PNR Code:</td><td style="padding: 4px 0; font-weight: 900; color: #ea580c; font-size: 15px; font-family: monospace; text-align: right;">{pnr_str}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Service:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{item_title}</td></tr>
                        <tr><td style="padding: 4px 0; color: #64748b;">Passengers:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{pax_names}</td></tr>
                        <tr style="border-top: 1px solid #e2e8f0;"><td style="padding: 8px 0 4px 0; color: #0f172a; font-weight: bold;">Status:</td><td style="padding: 8px 0 4px 0; font-weight: 900; color: #166534; font-size: 14px; text-align: right;">{status_disp}</td></tr>
                    </table>
                </div>
                <p>You can print your official E-Ticket/Voucher anytime from your dashboard portal.</p>
                """
                html_confirm = build_professional_email_html("B2B Ticket Confirmation", agent_name, body_confirm_html, "Print Voucher / E-Ticket", f"http://127.0.0.1:8000/dashboard/agent/ticket-orders/{ref_no}/print/")
                _dispatch_email(subject_confirm, f"B2B Order #{ref_no} Confirmed", from_email, recipients, html_message=html_confirm)

    except Exception as err:
        print(f"[b2b_mail_error] Failed sending B2B order email for #{getattr(order, 'reference_number', '')}: {err}")


@csrf_exempt
@user_passes_test(is_agent)
def agent_create_ticket_order_api(request):
    """
    POST → Create a B2B ticket/group/package order with atomic seat locking.
    Uses select_for_update() inside transaction.atomic() to guarantee no overbooking.
    Recalculates total_fare server-side (never trusting client input).
    Validates GroupFarePolicy min_group_size for group bookings.
    If decision == 'pay_now', validates wallet balance via AgentLedger, creates a debit entry,
    and issues PNR & ticket numbers (or package confirmation code).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    booking_type = data.get('booking_type', 'ticket')
    item_id = data.get('item_id')
    route_id = data.get('route_id')
    group_policy_id = data.get('group_policy_id')  # standalone group ticket ID
    passengers = data.get('passengers', [])
    if isinstance(passengers, str) and passengers.strip():
        try:
            passengers = json.loads(passengers)
        except Exception:
            passengers = []

    seat_count_raw = data.get('seat_count') or (len(passengers) if isinstance(passengers, list) else 1) or 1
    try:
        seat_count = int(seat_count_raw)
    except Exception:
        seat_count = max(len(passengers) if isinstance(passengers, list) else 1, 1)

    total_seats_requested = max(len(passengers) if isinstance(passengers, list) else 1, seat_count)
    decision = data.get('decision', 'hold')
    traveler_email = data.get('traveler_email', '')
    agent_email = data.get('agent_email', request.user.email or '')
    agent_phone = data.get('agent_phone_number') or getattr(request.user, 'phone', '') or ''
    baggage_weight_kg = data.get('baggage_weight_kg')
    selected_hotel_id = data.get('selected_hotel_id')
    selected_sharing_type = data.get('selected_sharing_type')

    if total_seats_requested < 1:
        return JsonResponse({'success': False, 'error': 'At least 1 seat/passenger is required.'}, status=400)

    try:
        with transaction.atomic():
            inventory = None
            pkg = None
            hajj_pkg = None
            selected_hotel = None

            if selected_hotel_id:
                selected_hotel = Hotel.objects.filter(id=selected_hotel_id).first()

            standalone_policy = None
            if booking_type in ['ticket', 'group']:
                # ── Standalone Group Ticket path (no linked flight inventory) ──
                if booking_type == 'group' and group_policy_id and not (route_id or item_id):
                    standalone_policy = GroupFarePolicy.objects.select_for_update().filter(
                        id=group_policy_id, is_active=True, flight_inventory__isnull=True
                    ).first()
                    if not standalone_policy:
                        return JsonResponse({'success': False, 'error': 'Standalone group ticket not found or inactive.'}, status=404)
                    if total_seats_requested > standalone_policy.available_seats:
                        return JsonResponse({
                            'success': False,
                            'error': f'Only {standalone_policy.available_seats} seats available for this group ticket.'
                        }, status=400)
                    standalone_policy.available_seats -= total_seats_requested
                    standalone_policy.save()
                    # inventory stays None; we'll compute fare from the policy
                else:
                    inv_id = route_id or item_id
                    # LOCK the row so no other agent can overbook these seats
                    inventory = AirlineFlightInventory.objects.select_for_update().get(id=inv_id)

                    available = inventory.total_seats - inventory.booked_seats
                    if total_seats_requested > available:
                        return JsonResponse({
                            'success': False,
                            'error': f'Only {available} seats available for this flight.'
                        }, status=400)

                    inventory.booked_seats += total_seats_requested
                    inventory.save()

            elif booking_type in ['umrah', 'hajj']:
                hajj_pkg_obj = AgentHajjPackage.objects.select_for_update().filter(id=item_id).first()
                if hajj_pkg_obj and booking_type == 'hajj':
                    available = hajj_pkg_obj.available_seats
                    if total_seats_requested > available:
                        return JsonResponse({
                            'success': False,
                            'error': f'Only {available} seats available for this Hajj package.'
                        }, status=400)
                    hajj_pkg_obj.available_seats = max(0, hajj_pkg_obj.available_seats - total_seats_requested)
                    hajj_pkg_obj.save()
                    hajj_pkg = hajj_pkg_obj
                else:
                    # LOCK the package row
                    pkg = AgentPackage.objects.select_for_update().filter(id=item_id).first()
                    if not pkg:
                        return JsonResponse({'success': False, 'error': 'Package details not found.'}, status=404)
                    available = pkg.total_seats - pkg.booked_seats
                    if total_seats_requested > available:
                        return JsonResponse({
                            'success': False,
                            'error': f'Only {available} seats available for this package.'
                        }, status=400)

                    pkg.booked_seats += total_seats_requested
                    pkg.save()

            # ── Fare calculation: standalone policy uses its own group_fare ──
            if standalone_policy:
                if standalone_policy.group_fare_override is not None and standalone_policy.group_fare_override > 0:
                    per_seat = float(standalone_policy.group_fare_override)
                elif standalone_policy.discount_type == 'percentage':
                    base = float(standalone_policy.base_fare or 0)
                    per_seat = max(0.0, base - (base * float(standalone_policy.discount_value) / 100.0))
                else:
                    per_seat = max(0.0, float(standalone_policy.base_fare or 0) - float(standalone_policy.discount_value))
                calculated_total_fare = Decimal(str(round(per_seat * total_seats_requested, 2)))
            else:
                calculated_total_fare = calculate_order_total_fare(
                    order_type=booking_type,
                    flight_inventory=inventory,
                    agent_package=pkg or hajj_pkg,
                    baggage_weight_kg=baggage_weight_kg,
                    passenger_count=total_seats_requested,
                    booking_type=booking_type,
                    passengers_data=passengers,
                    selected_sharing_type=selected_sharing_type
                )

            # Check wallet balance if pay_now
            if decision == 'pay_now':
                wallet_balance = get_agent_wallet_balance(request.user)
                if wallet_balance < calculated_total_fare:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient wallet balance. Available: PKR {wallet_balance}, Required: PKR {calculated_total_fare}'
                    }, status=400)

            ref_num = generate_reference_number()
            hold_exp = timezone.now() + timedelta(hours=2) if decision == 'hold' else None
            order_status = 'paid' if decision == 'pay_now' else 'hold'

            order = AgentTicketOrder.objects.create(
                reference_number=ref_num,
                agent=request.user,
                order_type=booking_type,
                flight_inventory=inventory,
                agent_package=pkg,
                agent_hajj_package=hajj_pkg,
                group_policy=standalone_policy,
                selected_hotel=selected_hotel,
                selected_sharing_type=selected_sharing_type,
                baggage_weight_kg=baggage_weight_kg,
                traveler_contact_email=traveler_email,
                agent_contact_email=agent_email,
                agent_phone_number=agent_phone,
                total_fare=calculated_total_fare,
                status=order_status,
                hold_expires_at=hold_exp
            )

            for i in range(total_seats_requested):
                p = passengers[i] if i < len(passengers) else {}
                p_first = p.get('first_name', '').strip() or f"Passenger {i+1}"
                p_last = p.get('last_name', '').strip()
                p_file = request.FILES.get(f'passport_image_{i+1}') or request.FILES.get(f'passport_image_{i}') or request.FILES.get(f'passport_image_{p.get("id")}')
                
                op = OrderPassenger.objects.create(
                    order=order,
                    passenger_type=p.get('passenger_type', 'adult'),
                    title=p.get('title', 'Mr') or 'Mr',
                    first_name=p_first,
                    last_name=p_last,
                    date_of_birth=p.get('dob') or None,
                    nationality=p.get('nationality', 'Pakistan') or 'Pakistan',
                    passport_number=p.get('passport_number', '').strip(),
                    passport_issue_date=p.get('passport_issue_date') or None,
                    passport_expiry_date=p.get('passport_expiry_date') or None
                )
                if p_file:
                    op.passport_image = p_file
                    op.save()

            if decision == 'pay_now':
                from ..accounts.models import AgentLedger
                AgentLedger.objects.create(
                    agent=request.user,
                    entry_type='debit',
                    category='ticket_purchase',
                    amount=calculated_total_fare,
                    description=f'Ticket purchase - {order.reference_number}',
                    reference=order.reference_number,
                    created_by=request.user
                )
                order.pnr = None
                order.status = 'paid'
                order.save()

            # Trigger automated email alert to Admin and Agent
            send_b2b_order_notification_email(order, event_type='created')

        return JsonResponse({
            'success': True,
            'reference_number': order.reference_number,
            'status': order.status,
            'pnr': order.pnr or '',
            'hold_expires_at': order.hold_expires_at.isoformat() if order.hold_expires_at else None,
            'message': 'Order successfully created.'
        })

    except BaggageFareTier.DoesNotExist as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except AirlineFlightInventory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Flight inventory route not found.'}, status=404)
    except AgentPackage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Agent package not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@user_passes_test(is_agent)
def agent_update_passengers_api(request, pk):
    """
    POST → Allows agent to update passenger details (names, passport numbers, dates)
    and optionally pay/confirm a held order using wallet balance.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

    order = get_object_or_404(AgentTicketOrder, pk=pk, agent=request.user)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    passengers_list = data.get('passengers', [])
    decision = data.get('decision')
    agent_phone = data.get('agent_phone_number')

    if agent_phone:
        order.agent_phone_number = agent_phone.strip()
        order.save()

    for p_item in passengers_list:
        p_id = p_item.get('id')
        passenger = None
        if p_id:
            passenger = OrderPassenger.objects.filter(id=p_id, order=order).first()
        if passenger:
            if 'first_name' in p_item and p_item['first_name'] is not None: passenger.first_name = str(p_item['first_name']).strip()
            if 'last_name' in p_item and p_item['last_name'] is not None: passenger.last_name = str(p_item['last_name']).strip()
            if 'title' in p_item and p_item['title'] is not None: passenger.title = str(p_item['title']).strip()
            if 'passport_number' in p_item and p_item['passport_number'] is not None: passenger.passport_number = str(p_item['passport_number']).strip()
            if 'nationality' in p_item and p_item['nationality'] is not None: passenger.nationality = str(p_item['nationality']).strip()
            if 'dob' in p_item: passenger.date_of_birth = p_item['dob'] or None
            if 'passport_issue_date' in p_item: passenger.passport_issue_date = p_item['passport_issue_date'] or None
            if 'passport_expiry_date' in p_item: passenger.passport_expiry_date = p_item['passport_expiry_date'] or None
            passenger.save()

    if decision == 'pay_now' and order.status == 'hold':
        wallet_balance = get_agent_wallet_balance(request.user)
        if wallet_balance < order.total_fare:
            return JsonResponse({
                'success': False,
                'error': f'Insufficient wallet balance. Available: PKR {wallet_balance}, Required: PKR {order.total_fare}'
            }, status=400)

        from ..accounts.models import AgentLedger
        AgentLedger.objects.create(
            agent=request.user,
            entry_type='debit',
            category='ticket_purchase',
            amount=order.total_fare,
            description=f'Ticket purchase - {order.reference_number}',
            reference=order.reference_number,
            created_by=request.user
        )
        order.status = 'paid'
        order.pnr = None
        order.save()

    return JsonResponse({
        'success': True,
        'message': 'Passenger details updated successfully.',
        'status': order.status,
        'pnr': order.pnr or ''
    })


def is_agent_or_admin(user):
    if not user.is_authenticated:
        return False
    role = getattr(user, 'role', None)
    return user.is_superuser or role in ['admin', 'super_admin', 'agent']


def restore_order_seats_and_update_status(order, new_status='cancelled'):
    """
    Restores reserved seats to FlightInventory, AgentPackage, or GroupFarePolicy when an order is cancelled or expired.
    """
    if order.status in ('expired', 'cancelled'):
        order.status = new_status
        order.save()
        return

    with transaction.atomic():
        seat_count = order.passengers.count() or 1

        if order.flight_inventory:
            fi = AirlineFlightInventory.objects.select_for_update().filter(id=order.flight_inventory.id).first()
            if fi:
                fi.booked_seats = max(0, fi.booked_seats - seat_count)
                fi.save()

        if order.agent_package:
            pkg = AgentPackage.objects.select_for_update().filter(id=order.agent_package.id).first()
            if pkg:
                pkg.booked_seats = max(0, pkg.booked_seats - seat_count)
                pkg.save()

        if order.agent_hajj_package:
            hpkg = AgentHajjPackage.objects.select_for_update().filter(id=order.agent_hajj_package.id).first()
            if hpkg:
                hpkg.available_seats += seat_count
                hpkg.save()

        if order.group_policy:
            pol = GroupFarePolicy.objects.select_for_update().filter(id=order.group_policy.id).first()
            if pol:
                pol.available_seats += seat_count
                pol.save()

        order.status = new_status
        order.save()


def auto_expire_hold_orders_helper():
    """
    Automatically expires hold orders older than 2 hours (or past hold_expires_at) and releases reserved seats.
    """
    now = timezone.now()
    expired_orders = AgentTicketOrder.objects.filter(
        status='hold',
        hold_expires_at__lte=now
    )
    for order in expired_orders:
        try:
            restore_order_seats_and_update_status(order, new_status='expired')
        except Exception as e:
            print(f"Error auto-expiring hold order #{order.id}: {e}")


@csrf_exempt
@admin_required_api
def admin_ticket_orders_api(request):
    """
    GET → List all AgentTicketOrder records AND Booking records for admin view with status filter.
    """
    auto_expire_hold_orders_helper()
    status_filter = request.GET.get('status', 'all').strip().lower()
    orders = AgentTicketOrder.objects.select_related('agent', 'flight_inventory__airline', 'agent_package').prefetch_related('passengers').all()

    if status_filter and status_filter != 'all':
        orders = orders.filter(status=status_filter)

    data = []
    for order in orders:
        route_title = ""
        airline_name = ""
        airline_code = ""

        if order.flight_inventory:
            fi = order.flight_inventory
            airline_name = fi.airline.name if fi.airline else ""
            airline_code = getattr(fi.airline, 'iata_code', '') if fi.airline else ""
            route_title = f"{airline_name} ({airline_code}): {fi.departure_city} ➔ {fi.destination_city}" if airline_code else f"{airline_name}: {fi.departure_city} ➔ {fi.destination_city}"
        elif order.agent_package:
            route_title = f"Package: {order.agent_package.title} ({order.agent_package.get_package_type_display()})"

        passengers_data = []
        for p in order.passengers.all():
            passengers_data.append({
                'id': p.id,
                'passenger_type': p.passenger_type,
                'passenger_type_display': p.get_passenger_type_display(),
                'title': p.title,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'full_name': f"{p.title}. {p.first_name} {p.last_name}".strip(),
                'dob': p.date_of_birth.isoformat() if p.date_of_birth else '',
                'nationality': p.nationality,
                'passport_number': p.passport_number,
                'passport_issue_date': p.passport_issue_date.isoformat() if p.passport_issue_date else '',
                'passport_expiry_date': p.passport_expiry_date.isoformat() if p.passport_expiry_date else '',
                'passport_image_url': p.passport_image.url if p.passport_image else '',
                'allotted_ticket_number': p.allotted_ticket_number or '',
            })

        data.append({
            'id': order.id,
            'reference_number': order.reference_number,
            'agent_id': order.agent.id if order.agent else None,
            'agent_name': order.agent.username if order.agent else 'System',
            'agent_email': order.agent.email if order.agent else '',
            'agent_phone_number': order.agent_phone_number or getattr(order.agent, 'phone', '') or '',
            'order_type': order.order_type,
            'order_type_display': order.get_order_type_display(),
            'route_title': route_title,
            'baggage_weight_kg': order.baggage_weight_kg,
            'traveler_contact_email': order.traveler_contact_email,
            'agent_contact_email': order.agent_contact_email,
            'total_fare': str(order.total_fare),
            'original_fare': str(order.original_fare) if order.original_fare is not None else str(order.total_fare),
            'admin_discount': str(getattr(order, 'admin_discount', '0.00')),
            'status': order.status,
            'status_display': order.get_status_display(),
            'hold_expires_at': order.hold_expires_at.isoformat() if order.hold_expires_at else None,
            'pnr': order.pnr or '',
            'passenger_count': len(passengers_data) or 1,
            'passengers': passengers_data,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'source_model': 'AgentTicketOrder'
        })

    # Include Booking model records (Package Bookings from main package catalog)
    try:
        from ..bookings.models import Booking
        pkg_bookings = Booking.objects.select_related('user', 'package').all()
        for b in pkg_bookings:
            pkg_type = getattr(b.package, 'package_type', 'umrah') if b.package else 'umrah'
            pkg_title = b.package.title if b.package else 'Custom Package'
            pnr_val = getattr(b, 'pnr', '') or ''
            user_phone = getattr(b.user, 'phone', '') or 'N/A'
            p_count = (b.adults_count or 1) + (b.children_count or 0) + (b.infants_count or 0)

            data.append({
                'id': f"bkg_{b.id}",
                'reference_number': f"INV-PKG-{b.id:04d}",
                'agent_id': b.user.id if b.user else None,
                'agent_name': b.user.username if b.user else 'Customer',
                'agent_email': b.user.email if b.user else '',
                'agent_phone_number': user_phone,
                'order_type': pkg_type,
                'order_type_display': pkg_type.capitalize() + ' Package',
                'route_title': f"Package: {pkg_title} ({b.sharing_category or 'Standard'})",
                'baggage_weight_kg': None,
                'traveler_contact_email': b.user.email if b.user else '',
                'agent_contact_email': b.user.email if b.user else '',
                'total_fare': str(b.total_price),
                'original_fare': str(b.total_price),
                'admin_discount': '0.00',
                'status': b.status,
                'status_display': b.get_status_display(),
                'hold_expires_at': None,
                'pnr': pnr_val,
                'passenger_count': p_count,
                'passengers': [
                    {
                        'id': f"bkg_p_{b.id}",
                        'passenger_type': 'adult',
                        'passenger_type_display': 'Adult',
                        'title': 'Mr/Ms',
                        'first_name': b.user.username if b.user else 'Lead',
                        'last_name': 'Passenger',
                        'full_name': b.user.get_full_name() or (b.user.username if b.user else 'Lead Passenger'),
                        'dob': '',
                        'nationality': 'PK',
                        'passport_number': 'N/A',
                        'allotted_ticket_number': 'Confirmed' if b.status == 'confirmed' else 'Pending',
                    }
                ],
                'created_at': b.created_at.strftime('%Y-%m-%d %H:%M'),
                'source_model': 'Booking'
            })
    except Exception as err:
        print(f"[admin_ticket_orders_api] Error loading Booking model records: {err}")

    return JsonResponse({'success': True, 'orders': data})


@csrf_exempt
@admin_required_api
def admin_allot_tickets_api(request, pk):
    """
    POST → Admin enters ticket numbers for passengers, optional PNR, optional Admin Discount, and marks status as 'ticketed' or 'paid'.
    Supports both AgentTicketOrder (integer pk) and Booking (pk starting with bkg_).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    pnr_val = data.get('pnr')
    new_status = data.get('status', 'paid')
    passengers_list = data.get('passengers', [])

    str_pk = str(pk)
    if str_pk.startswith('bkg_'):
        from ..bookings.models import Booking
        real_id = int(str_pk.replace('bkg_', ''))
        booking = get_object_or_404(Booking, pk=real_id)

        if pnr_val:
            booking.pnr = pnr_val.strip()

        if new_status in ['paid', 'confirmed', 'ticketed']:
            booking.status = 'confirmed'
        elif new_status == 'hold':
            booking.status = 'pending'
        booking.save()

        return JsonResponse({
            'success': True,
            'message': f'Package booking status updated to {booking.get_status_display()}.',
            'status': booking.status,
            'pnr': getattr(booking, 'pnr', '') or ''
        })

    # Standard AgentTicketOrder
    order = get_object_or_404(AgentTicketOrder, pk=pk)

    if pnr_val:
        order.pnr = pnr_val.strip()

    if new_status in ['paid', 'confirmed', 'ticketed']:
        order.status = new_status

    # Optional Admin Discount processing
    raw_discount = data.get('admin_discount') or data.get('discount_amount')
    if raw_discount is not None and str(raw_discount).strip() != '':
        try:
            from decimal import Decimal
            from ..accounts.models import AgentLedger
            new_discount = Decimal(str(raw_discount).strip())
            if new_discount >= 0:
                if order.original_fare is None:
                    order.original_fare = order.total_fare

                old_discount = order.admin_discount or Decimal('0.00')
                discount_diff = new_discount - old_discount

                order.admin_discount = new_discount
                order.total_fare = max(Decimal('0.00'), order.original_fare - new_discount)

                if discount_diff > 0 and order.agent:
                    AgentLedger.objects.create(
                        agent=order.agent,
                        entry_type='credit',
                        category='adjustment',
                        amount=discount_diff,
                        description=f"Special Admin Discount credited for Order #{order.reference_number}",
                        reference=order.reference_number,
                        created_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                    )
        except Exception as disc_err:
            print(f"[admin_allot_tickets_api] Error processing discount: {disc_err}")

    order.save()

    for p_item in passengers_list:
        p_id = p_item.get('id')
        t_num = p_item.get('ticket_number') or p_item.get('allotted_ticket_number')
        if p_id and t_num:
            passenger = OrderPassenger.objects.filter(id=p_id, order=order).first()
            if passenger:
                passenger.allotted_ticket_number = str(t_num).strip()
                passenger.save()

    # Dispatch email notification to Agent and Traveler
    send_b2b_order_notification_email(order, event_type='ticketed')

    return JsonResponse({
        'success': True,
        'message': f'Ticket numbers allotted and order status updated to {order.get_status_display()}.',
        'status': order.status,
        'pnr': order.pnr or '',
        'total_fare': str(order.total_fare),
        'admin_discount': str(order.admin_discount)
    })


@csrf_exempt
@admin_required_api
def admin_confirm_ticket_payment_api(request, pk):
    """
    POST → Admin confirms payment for a ticket order.
    Generates 6-character PNR and 10-digit ticket numbers for all passengers inside transaction.atomic().
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

    order = get_object_or_404(AgentTicketOrder, pk=pk)
    if order.status not in ['hold', 'paid_pending']:
        return JsonResponse({
            'success': False,
            'error': f'Cannot confirm payment for an order with status {order.get_status_display()}'
        }, status=400)

    pnr = issue_pnr_and_tickets_for_order(order)
    send_b2b_order_notification_email(order, event_type='ticketed')

    return JsonResponse({
        'success': True,
        'pnr': pnr,
        'status': 'paid',
        'message': f'Payment confirmed for order {order.reference_number}. PNR {pnr} generated.'
    })


@csrf_exempt
@admin_required_api
def admin_cancel_ticket_order_api(request, pk):
    """
    POST → Admin cancels an AgentTicketOrder or Booking record and restores reserved seats.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    str_pk = str(pk)
    if str_pk.startswith('bkg_'):
        from ..bookings.models import Booking
        real_id = int(str_pk.replace('bkg_', ''))
        booking = get_object_or_404(Booking, pk=real_id)
        booking.status = 'cancelled'
        booking.save()
        return JsonResponse({
            'success': True,
            'message': f'Package booking #{booking.id} cancelled successfully.',
            'status': 'cancelled'
        })

    order = get_object_or_404(AgentTicketOrder, pk=pk)
    restore_order_seats_and_update_status(order, new_status='cancelled')
    return JsonResponse({
        'success': True,
        'message': f'Order #{order.reference_number} cancelled successfully by Admin. Reserved seats released.',
        'status': 'cancelled'
    })


@csrf_exempt
@user_passes_test(is_agent)
def agent_cancel_ticket_order_api(request, pk):
    """
    POST → Agent cancels their own order (if status is 'hold', 'paid_pending', or 'paid').
    Restores reserved seats back to inventory / package / group ticket.
    If order was paid, automatically refunds the payment to agent's wallet ledger!
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    order = get_object_or_404(AgentTicketOrder, pk=pk, agent=request.user)
    if order.status not in ('hold', 'paid_pending', 'paid'):
        return JsonResponse({
            'success': False,
            'message': f'Cannot cancel order with status "{order.get_status_display()}". Only hold, pending, or un-ticketed paid orders can be cancelled.'
        }, status=400)

    was_paid = (order.status == 'paid')
    refund_amount = order.total_fare

    restore_order_seats_and_update_status(order, new_status='cancelled')

    if was_paid and refund_amount > 0:
        from ..accounts.models import AgentLedger
        AgentLedger.objects.create(
            agent=request.user,
            entry_type='credit',
            category='refund',
            amount=refund_amount,
            description=f'Refund for cancelled ticket order #{order.reference_number}',
            reference=order.reference_number,
            created_by=request.user
        )

    msg = f'Order #{order.reference_number} has been cancelled successfully. Reserved seats released.'
    if was_paid:
        msg += f' PKR {refund_amount} has been refunded to your wallet ledger.'

    return JsonResponse({
        'success': True,
        'message': msg,
        'status': 'cancelled'
    })


@csrf_exempt
@user_passes_test(is_agent)
def agent_delete_ticket_order_api(request, pk):
    """
    DELETE / POST → Agent deletes an order record (if cancelled, expired, or hold).
    If order is on hold, restores seats before deletion.
    """
    order = get_object_or_404(AgentTicketOrder, pk=pk, agent=request.user)

    if order.status == 'hold':
        restore_order_seats_and_update_status(order, new_status='cancelled')

    order.delete()
    return JsonResponse({
        'success': True,
        'message': 'Order deleted successfully.'
    })


@csrf_exempt
@user_passes_test(is_agent_or_admin)
def agent_my_orders_api(request):
    """
    GET → List all AgentTicketOrder records belonging to the logged-in agent.
    """
    auto_expire_hold_orders_helper()
    orders = AgentTicketOrder.objects.filter(agent=request.user).select_related(
        'flight_inventory', 'flight_inventory__airline',
        'group_policy', 'group_policy__airline',
        'agent_package'
    ).prefetch_related('passengers').order_by('-created_at').all()

    data = []
    for order in orders:
        route_title = ""
        airline_name = ""
        airline_code = ""

        if order.flight_inventory:
            fi = order.flight_inventory
            airline_name = fi.airline.name if fi.airline else "Airline Flight"
            airline_code = getattr(fi.airline, 'iata_code', '') if fi.airline else ""
            route_title = f"{airline_name} ({airline_code}): {fi.departure_city} ➔ {fi.destination_city}" if airline_code else f"{airline_name}: {fi.departure_city} ➔ {fi.destination_city}"
        elif order.group_policy:
            gp = order.group_policy
            airline_name = gp.airline_name_custom or (gp.airline.name if gp.airline else "Group Airlines")
            route_title = f"{airline_name}: {gp.departure_city} ➔ {gp.destination_city} (Group Deal)"
        elif order.agent_package:
            route_title = f"Package: {order.agent_package.title} ({order.agent_package.get_package_type_display()})"
        else:
            route_title = f"B2B Order #{order.reference_number or order.id}"

        passengers_data = []
        for p in order.passengers.all():
            passengers_data.append({
                'id': p.id,
                'passenger_type': p.passenger_type,
                'passenger_type_display': p.get_passenger_type_display(),
                'title': p.title,
                'first_name': p.first_name,
                'last_name': p.last_name,
                'full_name': f"{p.title}. {p.first_name} {p.last_name}".strip(),
                'dob': p.date_of_birth.isoformat() if p.date_of_birth else '',
                'nationality': p.nationality,
                'passport_number': p.passport_number,
                'allotted_ticket_number': p.allotted_ticket_number or 'Pending Payment',
            })

        data.append({
            'id': order.id,
            'reference_number': order.reference_number,
            'order_type': order.order_type,
            'order_type_display': order.get_order_type_display(),
            'route_title': route_title,
            'baggage_weight_kg': order.baggage_weight_kg,
            'traveler_contact_email': order.traveler_contact_email,
            'agent_contact_email': order.agent_contact_email,
            'agent_phone_number': order.agent_phone_number or getattr(order.agent, 'phone', '') or '',
            'total_fare': str(order.total_fare),
            'status': order.status,
            'status_display': order.get_status_display(),
            'hold_expires_at': order.hold_expires_at.isoformat() if order.hold_expires_at else None,
            'pnr': order.pnr or '',
            'passenger_count': len(passengers_data),
            'passengers': passengers_data,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({'success': True, 'orders': data})


@user_passes_test(is_agent_or_admin)
def agent_ticket_order_print_view(request, reference_number):
    """
    GET → Printable E-Ticket / Package Booking Confirmation Voucher view.
    Renders clean, chrome-less printable page templates/letters/ticket_confirmation.html.
    Supports ?hide_fare=1 or ?hide_fare=true to suppress price details for client receipts.
    Fallback lookup handles Booking IDs (e.g. INV-PKG-0046) seamlessly.
    """
    from ..bookings.models import Booking

    # 1. Direct reference match on AgentTicketOrder
    order = AgentTicketOrder.objects.filter(reference_number=reference_number).select_related('agent', 'flight_inventory__airline', 'agent_package').prefetch_related('passengers').first()

    # 2. Case-insensitive match on AgentTicketOrder
    if not order:
        order = AgentTicketOrder.objects.filter(reference_number__iexact=reference_number).select_related('agent', 'flight_inventory__airline', 'agent_package').prefetch_related('passengers').first()

    # 3. Numeric ID match on AgentTicketOrder
    digits = ''.join(filter(str.isdigit, reference_number))
    if not order and digits:
        try:
            order = AgentTicketOrder.objects.filter(id=int(digits)).select_related('agent', 'flight_inventory__airline', 'agent_package').prefetch_related('passengers').first()
        except Exception:
            pass

    # 4. Fallback: Check Package Booking (Booking model)
    if not order and digits:
        try:
            booking = Booking.objects.filter(id=int(digits)).first()
            if booking:
                from ..accounts.views import package_approval_letter_view
                return package_approval_letter_view(request, pk=booking.id)
        except Exception:
            pass

    if not order:
        booking = Booking.objects.filter(reference_number__iexact=reference_number).first()
        if booking:
            from ..accounts.views import package_approval_letter_view
            return package_approval_letter_view(request, pk=booking.id)

    # 5. If order exists, perform authorization check
    if order:
        if not (request.user.is_superuser or getattr(request.user, 'role', '') in ['admin', 'super_admin']) and order.agent != request.user:
            return JsonResponse({'error': 'Unauthorized to view this order ticket.'}, status=403)

        hide_fare = request.GET.get('hide_fare', '').lower() in ['1', 'true', 'yes']

        return render(request, 'letters/ticket_confirmation.html', {
            'order': order,
            'passengers': order.passengers.all(),
            'hide_fare': hide_fare,
            'document_title': f"E-Ticket {order.reference_number}",
        })

    # Fallback 404 response
    return render(request, 'letters/ticket_confirmation.html', {
        'order': None,
        'error_message': f"Order or Booking with reference '{reference_number}' could not be located.",
        'document_title': "Order Not Found",
    })


@csrf_exempt
@user_passes_test(is_agent)
def agent_my_activity_api(request):
    """
    GET → Fetch agent's own ticket orders, ledger entries, and current wallet balance.
    """
    from ..accounts.models import AgentLedger

    orders = AgentTicketOrder.objects.filter(agent=request.user).select_related('flight_inventory__airline', 'agent_package').prefetch_related('passengers').order_by('-created_at')

    orders_data = []
    for order in orders:
        route_title = ""
        if order.flight_inventory:
            fi = order.flight_inventory
            name = fi.airline.name if fi.airline else ""
            route_title = f"{name}: {fi.departure_city} ➔ {fi.destination_city}"
        elif order.agent_package:
            route_title = f"Package: {order.agent_package.title}"

        orders_data.append({
            'id': order.id,
            'reference_number': order.reference_number,
            'order_type': order.order_type,
            'order_type_display': order.get_order_type_display(),
            'route_title': route_title,
            'baggage_weight_kg': order.baggage_weight_kg,
            'traveler_contact_email': order.traveler_contact_email,
            'total_fare': str(order.total_fare),
            'status': order.status,
            'status_display': order.get_status_display(),
            'hold_expires_at': order.hold_expires_at.isoformat() if order.hold_expires_at else None,
            'pnr': order.pnr or '',
            'passenger_count': order.passengers.count(),
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    entries_qs = AgentLedger.objects.filter(agent=request.user).order_by('created_at')

    from_date = request.GET.get('from_date', '').strip()
    if from_date:
        entries_qs = entries_qs.filter(created_at__date__gte=from_date)

    to_date = request.GET.get('to_date', '').strip()
    if to_date:
        entries_qs = entries_qs.filter(created_at__date__lte=to_date)

    entry_type = request.GET.get('entry_type', '').strip()
    if entry_type and entry_type in ['credit', 'debit']:
        entries_qs = entries_qs.filter(entry_type=entry_type)

    search = request.GET.get('search', '').strip()
    if search:
        from django.db.models import Q
        entries_qs = entries_qs.filter(
            Q(description__icontains=search) | Q(reference__icontains=search)
        )

    all_agent_entries = AgentLedger.objects.filter(agent=request.user)
    total_credit = sum(e.amount for e in all_agent_entries if e.entry_type == 'credit')
    total_debit = sum(e.amount for e in all_agent_entries if e.entry_type == 'debit')
    wallet_balance = total_credit - total_debit

    ledger_data = []
    running = Decimal('0.00')
    for e in list(entries_qs):
        signed = e.amount if e.entry_type == 'credit' else -e.amount
        running += signed
        ledger_data.append({
            'id': e.id,
            'entry_type': e.entry_type,
            'category': e.category,
            'category_display': e.get_category_display() if hasattr(e, 'get_category_display') else e.category,
            'amount': float(e.amount),
            'description': e.description or '',
            'reference': e.reference or '',
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M'),
            'running_bal': float(running),
        })
    ledger_data.reverse()

    return JsonResponse({
        'success': True,
        'wallet_balance': float(wallet_balance),
        'total_credit': float(total_credit),
        'total_debit': float(total_debit),
        'orders': orders_data,
        'ledger_entries': ledger_data,
    })


@csrf_exempt
@agent_required_api
def agent_wallet_ledger_api(request):
    """
    GET → List logged-in agent's wallet ledger entries with date range, entry type (+/-), and search keyword.
    """
    from ..accounts.models import AgentLedger
    from django.db.models import Q
    from decimal import Decimal

    qs = AgentLedger.objects.filter(agent=request.user).order_by('created_at')

    from_date = request.GET.get('from_date', '').strip()
    if from_date:
        qs = qs.filter(created_at__date__gte=from_date)

    to_date = request.GET.get('to_date', '').strip()
    if to_date:
        qs = qs.filter(created_at__date__lte=to_date)

    entry_type = request.GET.get('entry_type', '').strip()
    if entry_type and entry_type in ['credit', 'debit']:
        qs = qs.filter(entry_type=entry_type)

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(description__icontains=search) | Q(reference__icontains=search) | Q(category__icontains=search)
        )

    all_entries = AgentLedger.objects.filter(agent=request.user)
    total_credit = sum(e.amount for e in all_entries if e.entry_type == 'credit')
    total_debit = sum(e.amount for e in all_entries if e.entry_type == 'debit')
    wallet_balance = float(total_credit - total_debit)

    entries = list(qs)
    data = []
    running = Decimal('0.00')
    for e in entries:
        signed = e.amount if e.entry_type == 'credit' else -e.amount
        running += signed
        data.append({
            'id': e.id,
            'entry_type': e.entry_type,
            'category': e.category,
            'category_display': e.get_category_display() if hasattr(e, 'get_category_display') else e.category,
            'amount': float(e.amount),
            'description': e.description or '',
            'reference': e.reference or '',
            'running_bal': float(e.running_balance) if e.running_balance is not None else float(running),
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else '',
        })

    data.reverse()

    return JsonResponse({
        'success': True,
        'wallet_balance': wallet_balance,
        'total_credit': float(total_credit),
        'total_debit': float(total_debit),
        'entries': data,
        'ledger_entries': data,
    })


# ══════════════════════════════════════════════
# B2B BANK ACCOUNTS MANAGEMENT (ADMIN & AGENT APIs)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_bank_accounts_api(request):
    """
    GET  → return list of bank accounts
    POST → create a new bank account
    """
    if request.method == 'GET':
        accounts = BankAccount.objects.all()
        data = []
        for a in accounts:
            data.append({
                'id': a.id,
                'bank_name': a.bank_name,
                'account_title': a.account_title,
                'account_number': a.account_number,
                'bank_logo_url': a.bank_logo.url if a.bank_logo else None,
                'is_active': a.is_active,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'bank_accounts': data})

    if request.method == 'POST':
        bank_name = request.POST.get('bank_name', '').strip()
        account_title = request.POST.get('account_title', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        
        if not bank_name or not account_title or not account_number:
            return JsonResponse({'success': False, 'message': 'Bank name, title, and number are required.'}, status=400)
            
        is_active_val = request.POST.get('is_active')
        is_active = is_active_val in ('on', 'true', '1', 'True', True) if is_active_val is not None else True
        
        logo = request.FILES.get('bank_logo')
        
        acc = BankAccount.objects.create(
            bank_name=bank_name,
            account_title=account_title,
            account_number=account_number,
            bank_logo=logo,
            is_active=is_active
        )
        return JsonResponse({'success': True, 'id': acc.id, 'message': 'Bank account created successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_bank_account_detail_api(request, pk):
    """
    POST   → update bank account details
    DELETE → delete bank account
    """
    acc = get_object_or_404(BankAccount, pk=pk)

    if request.method == 'DELETE':
        acc.delete()
        return JsonResponse({'success': True, 'message': 'Bank account deleted.'})

    if request.method == 'POST':
        bank_name = request.POST.get('bank_name', '').strip()
        account_title = request.POST.get('account_title', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        
        if bank_name:
            acc.bank_name = bank_name
        if account_title:
            acc.account_title = account_title
        if account_number:
            acc.account_number = account_number
            
        is_active_val = request.POST.get('is_active')
        if is_active_val is not None:
            acc.is_active = is_active_val in ('on', 'true', '1', 'True', True)
            
        if 'bank_logo' in request.FILES:
            acc.bank_logo = request.FILES['bank_logo']
        elif request.POST.get('remove_logo') == 'true':
            acc.bank_logo = None
            
        acc.save()
        return JsonResponse({'success': True, 'message': 'Bank account updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
def agent_bank_accounts_api(request):
    """
    GET → return list of active bank accounts for agents to view
    """
    if request.method == 'GET':
        accounts = BankAccount.objects.filter(is_active=True)
        data = []
        for a in accounts:
            data.append({
                'id': a.id,
                'bank_name': a.bank_name,
                'account_title': a.account_title,
                'account_number': a.account_number,
                'bank_logo_url': a.bank_logo.url if a.bank_logo else None,
            })
        return JsonResponse({'success': True, 'bank_accounts': data})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════════════════════════════════════
# STANDALONE AGENT HAJJ PACKAGES (B2B) — ADMIN & AGENT APIS
# ══════════════════════════════════════════════════════════════════════════════

def _serialize_agent_hajj_package(p):
    accommodations_data = []
    for acc in p.accommodations.select_related('hotel').all():
        h_name = acc.hotel.name if acc.hotel else (acc.manual_hotel_name or '')
        h_dist = acc.hotel.distance_from_haram if acc.hotel else (acc.manual_hotel_distance or '')
        accommodations_data.append({
            'id': acc.id,
            'city': acc.city,
            'city_display': acc.get_city_display(),
            'hotel_id': acc.hotel_id,
            'manual_hotel_name': acc.manual_hotel_name or '',
            'manual_hotel_distance': acc.manual_hotel_distance or '',
            'hotel_name': h_name,
            'hotel_distance': h_dist,
            'nights': acc.nights,
            'order': acc.order,
        })

    makkah_hotel = next((acc for acc in accommodations_data if acc['city'] == 'makkah'), None)
    madinah_hotel = next((acc for acc in accommodations_data if acc['city'] == 'madinah'), None)

    return {
        'id': p.id,
        'package_type': 'hajj',
        'package_type_display': 'Hajj Package',
        'is_hajj_model': True,
        'title': p.title,
        'description': p.description,
        'company_logo_url': p.logo_url,
        'company_logo': p.logo_url,
        'duration_days': p.duration_days,

        'departure_date': _safe_format_date(p.departure_date, '%Y-%m-%d'),
        'return_date': _safe_format_date(p.return_date, '%Y-%m-%d'),

        'includes_meal': p.includes_meal,
        'meal_display': 'Yes' if p.includes_meal else 'No',
        'meal_detail': p.meal_detail or 'Full Board Buffet',

        'airline_name': p.airline_name or 'Saudi Airlines',
        'airline_logo_url': p.airline_logo_url,
        'flight_name': p.flight_name or p.airline_name or 'Saudi Airlines',
        'flight_route': p.flight_route or 'KHI - JED - MED - KHI',

        'price_quad': str(p.price_quad),
        'price_triple': str(p.price_triple),
        'price_double': str(p.price_double),
        'price_sharing': str(p.price_sharing) if p.price_sharing is not None else '',
        'agent_price': str(p.starting_price),
        'starting_price': str(p.starting_price),

        'hajj_operator_name': p.hajj_operator_name,
        'license_number': p.license_number,
        'saudi_registration_number': p.saudi_registration_number,

        'total_seats': p.total_seats,
        'available_seats': p.available_seats,

        'accommodations': accommodations_data,
        'makkah_hotel_name': p.makkah_hotel_name or (makkah_hotel['hotel_name'] if makkah_hotel else 'N/A'),
        'makkah_hotel_distance': p.makkah_hotel_distance or (makkah_hotel['hotel_distance'] if makkah_hotel else ''),
        'madinah_hotel_name': p.madinah_hotel_name or (madinah_hotel['hotel_name'] if madinah_hotel else 'N/A'),
        'madinah_hotel_distance': p.madinah_hotel_distance or (madinah_hotel['hotel_distance'] if madinah_hotel else ''),

        'images': p.images or [],
        'is_active': p.is_active,
        'created_at': _safe_format_date(p.created_at, '%Y-%m-%d %H:%M'),
    }


@csrf_exempt
@admin_required_api
def admin_agent_hajj_packages_api(request):
    """
    GET  → list all agent hajj packages
    POST → create a new agent hajj package with nested accommodations
    """
    if request.method == 'GET':
        packages = AgentHajjPackage.objects.prefetch_related('accommodations__hotel').all()
        data = [_serialize_agent_hajj_package(p) for p in packages]
        return JsonResponse({'success': True, 'packages': data})

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip() or title
            duration_days = int(request.POST.get('duration_days', 15))

            departure_date_raw = request.POST.get('departure_date', '').strip()
            return_date_raw = request.POST.get('return_date', '').strip()
            departure_date = _safe_parse_date(departure_date_raw)
            return_date = _safe_parse_date(return_date_raw)

            includes_meal = request.POST.get('includes_meal', 'true').lower() in ('true', '1', 'on')
            meal_detail = request.POST.get('meal_detail', 'Full Board Buffet').strip()

            airline_name = request.POST.get('airline_name', 'Saudi Airlines').strip()
            flight_name = request.POST.get('flight_name', '').strip() or airline_name
            flight_route = request.POST.get('flight_route', 'KHI - JED - MED - KHI').strip()

            makkah_hotel_name = request.POST.get('makkah_hotel_name', '').strip()
            makkah_hotel_distance = request.POST.get('makkah_hotel_distance', '').strip()
            madinah_hotel_name = request.POST.get('madinah_hotel_name', '').strip()
            madinah_hotel_distance = request.POST.get('madinah_hotel_distance', '').strip()

            price_quad = Decimal(request.POST.get('price_quad', '0.00'))
            price_triple = Decimal(request.POST.get('price_triple', '0.00'))
            price_double = Decimal(request.POST.get('price_double', '0.00'))
            price_sharing_raw = request.POST.get('price_sharing', '').strip()
            price_sharing = Decimal(price_sharing_raw) if price_sharing_raw else None

            hajj_operator_name = request.POST.get('hajj_operator_name', '').strip()
            license_number = request.POST.get('license_number', '').strip()
            saudi_registration_number = request.POST.get('saudi_registration_number', '').strip()

            total_seats = int(request.POST.get('total_seats', 30))
            available_seats = int(request.POST.get('available_seats', total_seats))

            is_active = request.POST.get('is_active', 'true').lower() in ('true', '1', 'on')

            if not title:
                return JsonResponse({'success': False, 'message': 'Package title is required.'}, status=400)

            with transaction.atomic():
                pkg = AgentHajjPackage.objects.create(
                    title=title,
                    description=description,
                    duration_days=duration_days,
                    departure_date=departure_date,
                    return_date=return_date,
                    includes_meal=includes_meal,
                    meal_detail=meal_detail,
                    airline_name=airline_name,
                    flight_name=flight_name,
                    flight_route=flight_route,
                    makkah_hotel_name=makkah_hotel_name,
                    makkah_hotel_distance=makkah_hotel_distance,
                    madinah_hotel_name=madinah_hotel_name,
                    madinah_hotel_distance=madinah_hotel_distance,
                    price_quad=price_quad,
                    price_triple=price_triple,
                    price_double=price_double,
                    price_sharing=price_sharing,
                    hajj_operator_name=hajj_operator_name,
                    license_number=license_number,
                    saudi_registration_number=saudi_registration_number,
                    total_seats=total_seats,
                    available_seats=available_seats,
                    is_active=is_active
                )

                if 'company_logo' in request.FILES:
                    pkg.company_logo = request.FILES['company_logo']
                    pkg.save()

                if 'airline_logo' in request.FILES:
                    pkg.airline_logo = request.FILES['airline_logo']
                    pkg.save()

                # Process gallery image files
                if request.FILES.getlist('images'):
                    images_list = []
                    for idx, img_file in enumerate(request.FILES.getlist('images')):
                        ext = os.path.splitext(img_file.name)[1]
                        filename = f"hajj_pkg_{pkg.id}_img_{idx+1}{ext}"
                        save_path = os.path.join(settings.MEDIA_ROOT, 'agent_hajj', 'gallery', filename)
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb+') as destination:
                            for chunk in img_file.chunks():
                                destination.write(chunk)
                        images_list.append(f"{settings.MEDIA_URL}agent_hajj/gallery/{filename}")
                    pkg.images = images_list
                    pkg.save()

                # Process nested accommodation stays
                accommodations_json = request.POST.get('accommodations', '[]')
                try:
                    stays = json.loads(accommodations_json)
                except Exception:
                    stays = []

                for order, stay in enumerate(stays):
                    city = stay.get('city', 'makkah')
                    hotel_id = stay.get('hotel_id')
                    manual_hotel_name = stay.get('manual_hotel_name', '').strip()
                    manual_hotel_distance = stay.get('manual_hotel_distance', '').strip()
                    nights = int(stay.get('nights', 1))

                    hotel = Hotel.objects.filter(pk=hotel_id).first() if hotel_id else None
                    if hotel or manual_hotel_name:
                        AgentHajjAccommodation.objects.create(
                            agent_hajj_package=pkg,
                            city=city,
                            hotel=hotel,
                            manual_hotel_name=manual_hotel_name,
                            manual_hotel_distance=manual_hotel_distance,
                            nights=nights,
                            order=order
                        )

            return JsonResponse({'success': True, 'message': 'Agent Hajj Package created successfully!', 'package': _serialize_agent_hajj_package(pkg)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
@admin_required_api
def admin_agent_hajj_package_detail_api(request, pk):
    """
    GET    → Retrieve single AgentHajjPackage details
    POST   → Update AgentHajjPackage and replace all accommodation stays
    DELETE → Delete AgentHajjPackage
    """
    pkg = get_object_or_404(AgentHajjPackage, pk=pk)

    if request.method == 'GET':
        return JsonResponse({'success': True, 'package': _serialize_agent_hajj_package(pkg)})

    if request.method == 'DELETE':
        pkg.delete()
        return JsonResponse({'success': True, 'message': 'Agent Hajj Package deleted successfully.'})

    if request.method == 'POST':
        try:
            pkg.title = request.POST.get('title', pkg.title).strip()
            pkg.description = request.POST.get('description', pkg.description).strip()
            if 'duration_days' in request.POST and request.POST.get('duration_days').strip():
                pkg.duration_days = int(request.POST.get('duration_days'))

            if 'departure_date' in request.POST:
                raw_dep = request.POST.get('departure_date', '').strip()
                pkg.departure_date = _safe_parse_date(raw_dep)
            if 'return_date' in request.POST:
                raw_ret = request.POST.get('return_date', '').strip()
                pkg.return_date = _safe_parse_date(raw_ret)

            if 'includes_meal' in request.POST:
                pkg.includes_meal = request.POST.get('includes_meal', 'true').lower() in ('true', '1', 'on')
            if 'meal_detail' in request.POST:
                pkg.meal_detail = request.POST.get('meal_detail', pkg.meal_detail).strip()

            if 'airline_name' in request.POST:
                pkg.airline_name = request.POST.get('airline_name', pkg.airline_name).strip()
            if 'flight_name' in request.POST:
                pkg.flight_name = request.POST.get('flight_name', pkg.flight_name).strip()
            if 'flight_route' in request.POST:
                pkg.flight_route = request.POST.get('flight_route', pkg.flight_route).strip()

            if 'makkah_hotel_name' in request.POST:
                pkg.makkah_hotel_name = request.POST.get('makkah_hotel_name', '').strip()
            if 'makkah_hotel_distance' in request.POST:
                pkg.makkah_hotel_distance = request.POST.get('makkah_hotel_distance', '').strip()
            if 'madinah_hotel_name' in request.POST:
                pkg.madinah_hotel_name = request.POST.get('madinah_hotel_name', '').strip()
            if 'madinah_hotel_distance' in request.POST:
                pkg.madinah_hotel_distance = request.POST.get('madinah_hotel_distance', '').strip()

            if 'price_quad' in request.POST and request.POST.get('price_quad').strip():
                pkg.price_quad = Decimal(request.POST.get('price_quad'))
            if 'price_triple' in request.POST and request.POST.get('price_triple').strip():
                pkg.price_triple = Decimal(request.POST.get('price_triple'))
            if 'price_double' in request.POST and request.POST.get('price_double').strip():
                pkg.price_double = Decimal(request.POST.get('price_double'))
            if 'price_sharing' in request.POST:
                raw_sharing = request.POST.get('price_sharing', '').strip()
                pkg.price_sharing = Decimal(raw_sharing) if raw_sharing else None

            pkg.hajj_operator_name = request.POST.get('hajj_operator_name', pkg.hajj_operator_name).strip()
            pkg.license_number = request.POST.get('license_number', pkg.license_number).strip()
            pkg.saudi_registration_number = request.POST.get('saudi_registration_number', pkg.saudi_registration_number).strip()

            if 'total_seats' in request.POST and request.POST.get('total_seats').strip():
                pkg.total_seats = int(request.POST.get('total_seats'))
            if 'available_seats' in request.POST and request.POST.get('available_seats').strip():
                pkg.available_seats = int(request.POST.get('available_seats'))

            if 'is_active' in request.POST:
                pkg.is_active = request.POST.get('is_active', 'true').lower() in ('true', '1', 'on')

            with transaction.atomic():
                if 'company_logo' in request.FILES:
                    pkg.company_logo = request.FILES['company_logo']
                if 'airline_logo' in request.FILES:
                    pkg.airline_logo = request.FILES['airline_logo']

                if request.FILES.getlist('images'):
                    images_list = []
                    for idx, img_file in enumerate(request.FILES.getlist('images')):
                        ext = os.path.splitext(img_file.name)[1]
                        filename = f"hajj_pkg_{pkg.id}_img_{idx+1}{ext}"
                        save_path = os.path.join(settings.MEDIA_ROOT, 'agent_hajj', 'gallery', filename)
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, 'wb+') as destination:
                            for chunk in img_file.chunks():
                                destination.write(chunk)
                        images_list.append(f"{settings.MEDIA_URL}agent_hajj/gallery/{filename}")
                    pkg.images = images_list

                pkg.save()

                if 'accommodations' in request.POST:
                    accommodations_json = request.POST.get('accommodations', '[]')
                    try:
                        stays = json.loads(accommodations_json)
                    except Exception:
                        stays = []

                    pkg.accommodations.all().delete()

                    for order, stay in enumerate(stays):
                        city = stay.get('city', 'makkah')
                        hotel_id = stay.get('hotel_id')
                        manual_hotel_name = stay.get('manual_hotel_name', '').strip()
                        manual_hotel_distance = stay.get('manual_hotel_distance', '').strip()
                        nights = int(stay.get('nights', 1))

                        hotel = Hotel.objects.filter(pk=hotel_id).first() if hotel_id else None
                        if hotel or manual_hotel_name:
                            AgentHajjAccommodation.objects.create(
                                agent_hajj_package=pkg,
                                city=city,
                                hotel=hotel,
                                manual_hotel_name=manual_hotel_name,
                                manual_hotel_distance=manual_hotel_distance,
                                nights=nights,
                                order=order
                            )

            return JsonResponse({'success': True, 'message': 'Agent Hajj Package updated successfully!', 'package': _serialize_agent_hajj_package(pkg)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


@agent_required_api
def agent_hajj_packages_api(request):
    """
    GET → List active AgentHajjPackage records for Agent Portal
    """
    packages = AgentHajjPackage.objects.filter(is_active=True).prefetch_related('accommodations__hotel').all()
    data = [_serialize_agent_hajj_package(p) for p in packages]
    return JsonResponse({'success': True, 'packages': data})






