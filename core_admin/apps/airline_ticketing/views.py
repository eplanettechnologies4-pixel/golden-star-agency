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
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
import json
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, render

from .models import Sector, Airline, AirlineFlightInventory, BaggageFareTier, GroupFarePolicy, AgentPackage, AgentTicketOrder, OrderPassenger, Hotel, SeatAdjustmentLog, BankAccount


# ──────────────────────────────────────────────
# Permission helper  (matches apps/accounts/views.py:477 exactly)
# ──────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.role in ('super_admin', 'admin', 'staff'))


def is_agent(user):
    return user.is_authenticated and (user.role == 'agent' or user.is_superuser)


# ══════════════════════════════════════════════
# SECTORS (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_admin)
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

        sector = Sector(
            name=name,
            origin_city=origin_city,
            destination_city=destination_city,
            is_round_trip=request.POST.get('is_round_trip', 'false') == 'true',
            is_active=request.POST.get('is_active', 'true') == 'true',
        )
        sector.save()
        return JsonResponse({'success': True, 'id': sector.id, 'message': 'Sector created successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@user_passes_test(is_admin)
def admin_sector_detail_api(request, pk):
    """
    POST   → edit sector
    DELETE → delete sector
    """
    sector = get_object_or_404(Sector, pk=pk)

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

        sector.is_round_trip = request.POST.get('is_round_trip', 'false') == 'true'
        sector.is_active = request.POST.get('is_active', 'true') == 'true'
        sector.save()
        return JsonResponse({'success': True, 'message': 'Sector updated.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# MANUAL SEAT ADJUSTMENT (WITHOUT Financial Impact)
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_admin)
def admin_adjust_seats_api(request, pk):
    """
    POST → Manually update seat counts (total_seats or booked_seats)
           for FlightInventory or AgentPackage without impacting financial ledgers or orders.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    item_type = request.POST.get('item_type', 'inventory').strip()  # 'inventory' or 'package'
    reason = request.POST.get('reason', 'Offline / Manual Admin Seat Adjustment').strip()

    if item_type == 'package':
        item = get_object_or_404(AgentPackage, pk=pk)
        fi_obj = None
        pkg_obj = item
    else:
        item = get_object_or_404(AirlineFlightInventory, pk=pk)
        fi_obj = item
        pkg_obj = None

    if 'total_seats' in request.POST and request.POST.get('total_seats') != '':
        new_val = int(request.POST.get('total_seats') or 0)
        old_val = item.total_seats
        item.total_seats = max(0, new_val)
        target_field = 'total_seats'
    elif 'booked_seats' in request.POST and request.POST.get('booked_seats') != '':
        new_val = int(request.POST.get('booked_seats') or 0)
        old_val = item.booked_seats
        item.booked_seats = max(0, new_val)
        target_field = 'booked_seats'
    elif 'available_seats_delta' in request.POST and request.POST.get('available_seats_delta') != '':
        delta = int(request.POST.get('available_seats_delta') or 0)
        old_val = item.total_seats
        new_val = max(0, item.total_seats + delta)
        item.total_seats = new_val
        target_field = 'total_seats'
    else:
        return JsonResponse({'success': False, 'message': 'No valid seat count or delta provided.'}, status=400)

    item.save()

    # Log audit entry (NEVER referenced or joined into any financial analytics queries)
    SeatAdjustmentLog.objects.create(
        flight_inventory=fi_obj,
        agent_package=pkg_obj,
        adjusted_by=request.user if request.user.is_authenticated else None,
        target_field=target_field,
        old_value=old_val,
        new_value=new_val,
        reason=reason
    )

    return JsonResponse({
        'success': True,
        'message': f'Seats updated successfully ({old_val} → {new_val}).',
        'total_seats': item.total_seats,
        'booked_seats': item.booked_seats,
        'available_seats': item.available_seats
    })


# ══════════════════════════════════════════════
# AIRLINES  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_admin)
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
                'logo_url':  a.logo.url if a.logo else None,
                'is_active': a.is_active,
                'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'airlines': data})

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'message': 'Airline name is required.'}, status=400)

        airline = Airline(
            name=name,
            is_active=request.POST.get('is_active', 'true') == 'true',
        )
        if 'logo' in request.FILES:
            airline.logo = request.FILES['logo']
        airline.save()
        return JsonResponse({'success': True, 'id': airline.id, 'message': 'Airline created.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


# ══════════════════════════════════════════════
# AIRLINE DETAIL  (POST edit / DELETE delete)
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
                'airline_logo_url':     fi.airline.logo.url if fi.airline.logo else None,
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

        fi = AirlineFlightInventory(
            sector=sector,
            airline=airline,
            departure_city=departure_city,
            destination_city=destination_city,
            departure_time=request.POST.get('departure_time', '00:00 AM').strip(),
            arrival_time=request.POST.get('arrival_time', '00:00 AM').strip(),
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
@user_passes_test(is_admin)
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
    Keys expected: baggage_weight_0, baggage_fare_0, baggage_weight_1, baggage_fare_1 …
    Stops at first index where both keys are absent.
    """
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
            except (ValueError, TypeError):
                pass   # skip malformed tier rows silently
        i += 1


# ══════════════════════════════════════════════
# GROUP FARE POLICIES  (GET list / POST create)
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
                'madinah_hotel_name':       p.madinah_hotel_name,
                'madinah_hotel_distance':   p.madinah_hotel_distance,
                'airline_id':               p.airline_id,
                'airline_name':             p.airline.name if p.airline else 'Not Specified',
                'airline_logo_url':         p.airline.logo.url if (p.airline and p.airline.logo) else None,
                'images':                   p.images or [],
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
            madinah_hotel_name=request.POST.get('madinah_hotel_name', '').strip(),
            madinah_hotel_distance=request.POST.get('madinah_hotel_distance', '').strip(),
            airline=airline,
            images=images,
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
@user_passes_test(is_admin)
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
        pkg.madinah_hotel_name = request.POST.get('madinah_hotel_name', pkg.madinah_hotel_name).strip()
        pkg.madinah_hotel_distance = request.POST.get('madinah_hotel_distance', pkg.madinah_hotel_distance).strip()

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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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
            Q(airline__name__icontains=search)
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
            'airline_logo_url':     fi.airline.logo.url if fi.airline.logo else None,
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
            'discount_type_display':     p.get_discount_type_display(),
            'discount_value':           float(p.discount_value),
            'baggage_weight_kg':        p.baggage_weight_kg,
            'return_baggage_weight_kg': p.return_baggage_weight_kg,
            'base_fare':                round(base_fare, 2),
            'group_fare':               round(group_fare, 2),
            'route_display':            f"{airline_name} — {dep_city} → {dest_city} ({dep_time})",
        })
    return JsonResponse({'success': True, 'policies': data})


@user_passes_test(is_admin)
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
                # AirlineFlightInventory has no base_fare; use the policy's own base_fare
                # or fall back to the linked baggage tier fare
                tier = fi.baggage_tiers.filter(weight_kg=p.baggage_weight_kg).first() or fi.baggage_tiers.first()
                b_fare = float(tier.fare) if tier else (float(p.base_fare) if p.base_fare else 0.0)
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
                b_fare = float(p.base_fare) if p.base_fare else 0.0

            if p.group_fare_override is not None and p.group_fare_override > 0:
                g_fare = float(p.group_fare_override)
            elif p.discount_type == 'percentage':
                disc_amt = (b_fare * float(p.discount_value)) / 100.0
                g_fare = max(0.0, b_fare - disc_amt)
            else:
                g_fare = max(0.0, b_fare - float(p.discount_value))

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
                'group_fare_override':      float(p.group_fare_override) if p.group_fare_override is not None else None,
                'group_fare':               round(g_fare, 2),
                'is_active':                p.is_active,
                'route_display':            f"{air_name} — {dep} → {dest}",
            })
        return JsonResponse({'success': True, 'policies': data})

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body)
            airline_id = payload.get('airline_id')
            airline_obj = Airline.objects.filter(id=airline_id).first() if airline_id else None

            p = GroupFarePolicy.objects.create(
                airline=airline_obj,
                airline_name_custom=payload.get('airline_name_custom', ''),
                departure_city=payload.get('departure_city', ''),
                destination_city=payload.get('destination_city', ''),
                departure_time=payload.get('departure_time', ''),
                arrival_time=payload.get('arrival_time', ''),
                return_departure_time=payload.get('return_departure_time', ''),
                return_arrival_time=payload.get('return_arrival_time', ''),
                trip_type=payload.get('trip_type', 'oneway'),
                route_type=payload.get('route_type', 'direct'),
                via_city=payload.get('via_city', ''),
                has_meal=bool(payload.get('has_meal', True)),
                total_seats=int(payload.get('total_seats', 50)),
                available_seats=int(payload.get('available_seats', 50)),
                min_group_size=int(payload.get('min_group_size', 10)),
                discount_type=payload.get('discount_type', 'percentage'),
                discount_value=Decimal(str(payload.get('discount_value', 0))),
                baggage_weight_kg=int(payload.get('baggage_weight_kg', 30)),
                return_baggage_weight_kg=int(payload.get('return_baggage_weight_kg', 30)),
                base_fare=Decimal(str(payload.get('base_fare', 0))),
                group_fare_override=Decimal(str(payload.get('group_fare_override'))) if payload.get('group_fare_override') not in [None, ''] else None,
                is_active=bool(payload.get('is_active', True))
            )
            return JsonResponse({'success': True, 'policy_id': p.id, 'message': 'Group ticket created successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@user_passes_test(is_admin)
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
                'group_fare_override':      float(policy.group_fare_override) if policy.group_fare_override is not None else None,
                'is_active':                policy.is_active,
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
            if 'base_fare' in payload: policy.base_fare = Decimal(str(payload['base_fare']))
            if 'group_fare_override' in payload:
                policy.group_fare_override = Decimal(str(payload['group_fare_override'])) if payload['group_fare_override'] not in [None, ''] else None
            if 'is_active' in payload: policy.is_active = bool(payload['is_active'])

            policy.save()
            return JsonResponse({'success': True, 'message': 'Group ticket updated successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    elif request.method == 'DELETE':
        policy.delete()
        return JsonResponse({'success': True, 'message': 'Group ticket deleted successfully!'})


@user_passes_test(is_admin)
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


@user_passes_test(is_agent)
def agent_packages_api(request):
    """
    GET → List active agent packages (supports ?type=umrah or ?type=hajj)
    Exposes available_seats, NEVER raw booked_seats
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
            'available_seats':          p.available_seats,
            'makkah_hotel_name':        p.makkah_hotel_name,
            'makkah_hotel_distance':    p.makkah_hotel_distance,
            'madinah_hotel_name':       p.madinah_hotel_name,
            'madinah_hotel_distance':   p.madinah_hotel_distance,
            'airline_name':             p.airline.name if p.airline else 'Not Specified',
            'airline_logo_url':         p.airline.logo.url if (p.airline and p.airline.logo) else None,
            'images':                   p.images or [],
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


def get_agent_wallet_balance(agent):
    from apps.accounts.models import AgentLedger
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
                is_active=True,
                min_group_size__lte=passenger_count
            )
            if baggage_weight_kg:
                policy = policy.filter(baggage_weight_kg=baggage_weight_kg)
            
            p = policy.order_by('-min_group_size').first()
            if not p:
                p = GroupFarePolicy.objects.filter(
                    flight_inventory=flight_inventory,
                    is_active=True,
                    min_group_size__lte=passenger_count
                ).order_by('-min_group_size').first()

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
        if st == 'quad' and agent_package.price_quad is not None:
            base_room_price = agent_package.price_quad
        elif st == 'triple' and agent_package.price_triple is not None:
            base_room_price = agent_package.price_triple
        elif st == 'double' and agent_package.price_double is not None:
            base_room_price = agent_package.price_double
        elif st == 'sharing' and agent_package.price_sharing is not None:
            base_room_price = agent_package.price_sharing

        if base_room_price is None:
            base_room_price = agent_package.agent_price

        adult_price = Decimal(str(agent_package.adult_price)) if agent_package.adult_price is not None else Decimal(str(base_room_price))
        child_price = Decimal(str(agent_package.child_price)) if agent_package.child_price is not None else Decimal(str(base_room_price))
        infant_price = Decimal(str(agent_package.infant_price)) if agent_package.infant_price is not None else Decimal('0.00')

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
        from apps.accounts.views import build_professional_email_html, _dispatch_email
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
                    if total_seats_requested < standalone_policy.min_group_size:
                        return JsonResponse({
                            'success': False,
                            'error': f'Minimum group size for this ticket is {standalone_policy.min_group_size} seats.'
                        }, status=400)
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

                    if booking_type == 'group':
                        matching_policy_exists = GroupFarePolicy.objects.filter(
                            flight_inventory=inventory,
                            is_active=True,
                            min_group_size__lte=total_seats_requested
                        ).exists()
                        if not matching_policy_exists:
                            min_required = GroupFarePolicy.objects.filter(
                                flight_inventory=inventory, is_active=True
                            ).order_by('min_group_size').values_list('min_group_size', flat=True).first()
                            return JsonResponse({
                                'success': False,
                                'error': f'Group bookings require at least {min_required or "the minimum"} passengers for this route. Please book as an individual ticket instead.'
                            }, status=400)

                    available = inventory.total_seats - inventory.booked_seats
                    if total_seats_requested > available:
                        return JsonResponse({
                            'success': False,
                            'error': f'Only {available} seats available for this flight.'
                        }, status=400)

                    inventory.booked_seats += total_seats_requested
                    inventory.save()

            elif booking_type in ['umrah', 'hajj']:
                # LOCK the package row
                pkg = AgentPackage.objects.select_for_update().get(id=item_id)
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
                    agent_package=pkg,
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
                from apps.accounts.models import AgentLedger
                AgentLedger.objects.create(
                    agent=request.user,
                    entry_type='debit',
                    category='ticket_purchase',
                    amount=calculated_total_fare,
                    description=f'Ticket purchase - {order.reference_number}',
                    reference=order.reference_number,
                    created_by=request.user
                )
                issue_pnr_and_tickets_for_order(order)

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

        from apps.accounts.models import AgentLedger
        AgentLedger.objects.create(
            agent=request.user,
            entry_type='debit',
            category='ticket_purchase',
            amount=order.total_fare,
            description=f'Ticket purchase - {order.reference_number}',
            reference=order.reference_number,
            created_by=request.user
        )
        issue_pnr_and_tickets_for_order(order)

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
@user_passes_test(is_admin)
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
        from apps.bookings.models import Booking
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
@user_passes_test(is_admin)
def admin_allot_tickets_api(request, pk):
    """
    POST → Admin enters ticket numbers for passengers, optional PNR, and marks status as 'ticketed' or 'paid'.
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
        from apps.bookings.models import Booking
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
    order.save()

    for p_item in passengers_list:
        p_id = p_item.get('id')
        t_num = p_item.get('ticket_number') or p_item.get('allotted_ticket_number')
        if p_id and t_num:
            passenger = OrderPassenger.objects.filter(id=p_id, order=order).first()
            if passenger:
                passenger.allotted_ticket_number = str(t_num).strip()
                passenger.save()

    return JsonResponse({
        'success': True,
        'message': f'Ticket numbers allotted and order status updated to {order.get_status_display()}.',
        'status': order.status,
        'pnr': order.pnr or ''
    })


@csrf_exempt
@user_passes_test(is_admin)
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

    return JsonResponse({
        'success': True,
        'pnr': pnr,
        'status': 'paid',
        'message': f'Payment confirmed for order {order.reference_number}. PNR {pnr} generated.'
    })


@csrf_exempt
@user_passes_test(is_admin)
def admin_cancel_ticket_order_api(request, pk):
    """
    POST → Admin cancels an AgentTicketOrder or Booking record and restores reserved seats.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    str_pk = str(pk)
    if str_pk.startswith('bkg_'):
        from apps.bookings.models import Booking
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
    POST → Agent cancels their own order (if status is 'hold' or 'paid_pending').
    Restores reserved seats back to inventory / package / group ticket.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    order = get_object_or_404(AgentTicketOrder, pk=pk, agent=request.user)
    if order.status not in ('hold', 'paid_pending'):
        return JsonResponse({
            'success': False,
            'message': f'Cannot cancel order with status "{order.get_status_display()}". Only hold or pending orders can be cancelled.'
        }, status=400)

    restore_order_seats_and_update_status(order, new_status='cancelled')
    return JsonResponse({
        'success': True,
        'message': f'Order #{order.reference_number} has been cancelled successfully. Reserved seats released.',
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
@user_passes_test(is_agent)
def agent_my_orders_api(request):
    """
    GET → List all AgentTicketOrder records belonging to the logged-in agent.
    """
    auto_expire_hold_orders_helper()
    orders = AgentTicketOrder.objects.filter(agent=request.user).select_related('flight_inventory__airline', 'agent_package').prefetch_related('passengers').all()

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
    from apps.bookings.models import Booking

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
                from apps.accounts.views import package_approval_letter_view
                return package_approval_letter_view(request, pk=booking.id)
        except Exception:
            pass

    if not order:
        booking = Booking.objects.filter(reference_number__iexact=reference_number).first()
        if booking:
            from apps.accounts.views import package_approval_letter_view
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
    from apps.accounts.models import AgentLedger

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
@user_passes_test(is_agent)
def agent_wallet_ledger_api(request):
    """
    GET → List logged-in agent's wallet ledger entries with date range, entry type (+/-), and search keyword.
    """
    from apps.accounts.models import AgentLedger
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
            Q(description__icontains=search) | Q(reference__icontains=search)
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
@user_passes_test(is_admin)
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
@user_passes_test(is_admin)
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





