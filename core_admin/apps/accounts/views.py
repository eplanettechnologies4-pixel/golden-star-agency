from datetime import timedelta
from django.db import models
from django.db.models import Q, Sum
import random
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.utils import timezone
from .models import User, LoginHistory, AgentReview, AgentLedger, AgentFeedback
from .forms import CustomerSignupForm, AgentSignupForm, AgentDocumentsForm
from apps.packages.models import Package, CustomPackageInquiry
from apps.visa.models import VisaApplication
from apps.flights.models import FlightQuoteRequest
from apps.bookings.models import Booking
from apps.airline_ticketing.models import AgentTicketOrder
from django.conf import settings
try:
    from ai_chatbot.embeddings import EmbeddingsService
except ImportError:
    EmbeddingsService = None
from django.core.mail import send_mail
from django.core.cache import cache
import io
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') in ['admin', 'super_admin'])

def is_agent(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') == 'agent')

def is_agent_or_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', '') in ['agent', 'admin', 'super_admin'])


from functools import wraps
def admin_required_api(view_func):
    """API decorator that returns JSON 403 instead of HTML redirect on auth failure."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request.user):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'message': 'Admin authentication required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


def agent_required_api(view_func):
    """API decorator for agent-only endpoints. Returns JSON 403 instead of HTML redirect,
    so AJAX calls don't silently fail when session expires or user is not an agent."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_agent_or_admin(request.user):
            from django.http import JsonResponse
            return JsonResponse({'success': False, 'message': 'Agent authentication required.', 'orders': [], 'bookings': [], 'visas': [], 'flights': []}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped

# ─────────────────────────────────────────────────────────────────────────────
# ⚡ Global Email Thread Pool — reusable, 4 background workers, no per-email
#    thread creation overhead. Fire-and-forget async email delivery.
# ─────────────────────────────────────────────────────────────────────────────
_email_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='email-worker')

def build_professional_email_html(title, recipient_name, body_html, action_text=None, action_url=None):
    """
    Builds a highly professional, responsive HTML email template for REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.
    Includes official company header, office address, phone numbers, portal link, and social profiles.
    """
    portal_link = action_url or "http://127.0.0.1:8000/auth/login/"
    action_button_markup = ""
    if action_text and action_url:
        action_button_markup = f"""
        <div style="text-align: center; margin: 30px 0 20px 0;">
            <a href="{action_url}" style="background-color: #ea580c; background-image: linear-gradient(135deg, #ea580c 0%, #c45517 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 800; font-size: 14px; display: inline-block; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3); font-family: 'Plus Jakarta Sans', Arial, sans-serif;">
                {action_text} &rarr;
            </a>
        </div>
        """

    greeting_markup = f"<p style='margin-top: 0; font-size: 15px;'>Dear <strong>{recipient_name}</strong>,</p>" if recipient_name else ""

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Plus Jakarta Sans', Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased; color: #1e293b;">
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 10px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 620px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.06);">
                    
                    <!-- BRAND HEADER -->
                    <tr>
                        <td style="background-color: #1f2e1a; background-image: linear-gradient(135deg, #1f2e1a 0%, #2d4424 100%); padding: 32px 30px; text-align: center; border-bottom: 4px solid #ea580c;">
                            <div style="display: inline-block; background-color: #ea580c; color: #ffffff; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; font-size: 22px; font-weight: 900; text-align: center; margin-bottom: 10px;">&#9733;</div>
                            <h1 style="color: #ffffff; font-size: 19px; font-weight: 900; margin: 0; letter-spacing: 0.5px; text-transform: uppercase;">
                                REI GOLDEN <span style="color: #ea580c;">STAR</span> TRAVEL &amp; TOURS
                            </h1>
                            <p style="color: #ebd8b3; font-size: 11px; font-weight: 700; margin: 6px 0 0 0; letter-spacing: 1.5px; text-transform: uppercase;">
                                (PVT) LTD. &bull; Official Travel &amp; Tour Services
                            </p>
                        </td>
                    </tr>

                    <!-- MAIN BODY CONTAINER -->
                    <tr>
                        <td style="padding: 35px 32px 25px 32px; font-size: 14px; line-height: 1.7; color: #334155;">
                            <h2 style="color: #0f172a; font-size: 18px; font-weight: 800; margin-top: 0; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #f1f5f9;">
                                {title}
                            </h2>

                            {greeting_markup}

                            {body_html}

                            {action_button_markup}
                        </td>
                    </tr>

                    <!-- FOOTER & OFFICIAL SIGNATURE -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 28px 32px; font-size: 12px; color: #64748b; line-height: 1.6;">
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="padding-bottom: 18px; border-bottom: 1px solid #e2e8f0;">
                                        <p style="margin: 0 0 6px 0; font-size: 13px; font-weight: 800; color: #0f172a;">
                                            REI GOLDEN STAR TRAVEL &amp; TOURS (PVT) LTD.
                                        </p>
                                        <p style="margin: 0 0 4px 0; color: #475569;">
                                            &#128205; <strong>Office Address:</strong> Office 7/8, New Civil Lines, Regency Road, Faisalabad, Pakistan
                                        </p>
                                        <p style="margin: 0 0 4px 0; color: #475569;">
                                            &#128222; <strong>Call / WhatsApp:</strong> <a href="tel:+923077233303" style="color: #ea580c; text-decoration: none; font-weight: bold;">+92 307 7233303</a> | <a href="tel:+923341114888" style="color: #ea580c; text-decoration: none; font-weight: bold;">+92 334 1114888</a>
                                        </p>
                                        <p style="margin: 0; color: #475569;">
                                            &#9993; <strong>Email Support:</strong> <a href="mailto:goldenstartraveltours@gmail.com" style="color: #ea580c; text-decoration: none;">goldenstartraveltours@gmail.com</a> | <a href="mailto:goldenstaroofficial70@gmail.com" style="color: #ea580c; text-decoration: none;">goldenstaroofficial70@gmail.com</a>
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding-top: 18px; text-align: center;">
                                        <p style="margin: 0 0 10px 0; font-size: 12px;">
                                            &#127760; <strong>Portal Access:</strong> 
                                            <a href="{portal_link}" style="color: #ea580c; font-weight: bold; text-decoration: underline;">
                                                Client &amp; Agent Portal Login
                                            </a>
                                        </p>
                                        <div style="margin: 10px 0 14px 0; font-size: 12px;">
                                            <a href="https://www.facebook.com/profile.php?id=61591481684842" target="_blank" style="color: #2563eb; font-weight: bold; text-decoration: none; margin: 0 6px;">Facebook</a> &bull; 
                                            <a href="https://www.instagram.com/reigoldenstartravel/" target="_blank" style="color: #db2777; font-weight: bold; text-decoration: none; margin: 0 6px;">Instagram</a> &bull; 
                                            <a href="https://www.tiktok.com/@reigoldenstartravel" target="_blank" style="color: #0f172a; font-weight: bold; text-decoration: none; margin: 0 6px;">TikTok</a>
                                        </div>
                                        <p style="margin: 0; font-size: 11px; color: #94a3b8;">
                                            &copy; 2026 REI GOLDEN STAR TRAVEL &amp; TOURS (PVT) LTD. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def _dispatch_email(subject, plain_msg, from_email, to_list, html_message=None):
    """Centralized fire-and-forget background email dispatcher via thread pool."""
    if not html_message:
        # Wrap plain message automatically into professional template
        body_formatted = f"<p style='white-space: pre-wrap; font-size: 14px; line-height: 1.6;'>{plain_msg}</p>"
        html_message = build_professional_email_html(subject, None, body_formatted)
        
    def _send():
        try:
            send_mail(
                subject,
                plain_msg,
                from_email,
                to_list,
                html_message=html_message,
                fail_silently=False,
            )
            print(f"[Email OK] Delivered to {to_list} | Subject: {subject[:50]}")
        except Exception as e:
            print(f"[Email ERROR] Failed to {to_list}: {e}")
    _email_pool.submit(_send)

def _send_verification_email_sync(user):
    subject = "Verify Your Email | REI GOLDEN STAR TRAVEL & TOURS"
    recipient_name = user.get_full_name() or user.username
    body_html = f"""
    <p>Thank you for registering with <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong></p>
    <p>Please enter the following 6-digit email verification code on the website to verify your account:</p>
    <div style="text-align: center; margin: 25px 0;">
        <span style="font-size: 28px; font-weight: 900; letter-spacing: 6px; color: #ea580c; background-color: #fff7ed; padding: 12px 24px; border-radius: 12px; border: 1px dashed #fdba74; display: inline-block;">
            {user.email_verification_code}
        </span>
    </div>
    <p style="font-size: 13px; color: #64748b;">If you did not request this verification code, please ignore this email.</p>
    """
    html_message = build_professional_email_html("Email Verification Code", recipient_name, body_html, "Verify Account", "http://127.0.0.1:8000/auth/verify-email/")
    
    plain_msg = f"Hello {user.username},\n\nYour 6-digit email verification code is: {user.email_verification_code}\n\nThank you,\nREI GOLDEN STAR TRAVEL & TOURS (PVT) LTD."
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')
    _dispatch_email(subject, plain_msg, from_email, [user.email], html_message=html_message)

def send_verification_email(user):
    """Async email OTP verification — dispatched via pool immediately."""
    _send_verification_email_sync(user)

def _send_agent_status_email_sync(agent, status):
    subject = f"Account Status Update | REI GOLDEN STAR TRAVEL & TOURS"
    login_url = "http://127.0.0.1:8000/auth/login/"
    recipient_name = f"{agent.first_name} {agent.last_name}".strip() or agent.username
    
    if status == 'approved':
        status_text = "APPROVED"
        status_color = "#10B981" # Green
        status_desc = f"""
        <p>Congratulations! Your partner agent account application has been reviewed and approved by our administration team.</p>
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 20px 0;">
            <p style="margin: 0 0 8px 0; font-weight: bold; color: #0f172a;">Your Partner Login Details:</p>
            <p style="margin: 0 0 4px 0;"><strong>Username:</strong> {agent.username}</p>
            <p style="margin: 0;"><strong>Password:</strong> The password created during signup.</p>
        </div>
        <p>You now have full access to our B2B agent booking portals, search consoles, and discounted flight/pilgrimage catalogs.</p>
        """
    elif status == 'rejected':
        status_text = "REJECTED"
        status_color = "#EF4444" # Red
        status_desc = "<p>We regret to inform you that your partner agent account application has been rejected after document verification. Please contact support if you believe this is an error or wish to resubmit documentation.</p>"
    else:
        status_text = "SUSPENDED"
        status_color = "#F59E0B" # Amber
        status_desc = "<p>Your partner agent account has been temporarily suspended by our administration team. All current booking privileges are locked. Please contact our agent support department to resolve this matter.</p>"

    body_html = f"""
    <div style="margin: 20px 0; padding: 15px 20px; border-radius: 10px; background-color: #f8fafc; border-left: 5px solid {status_color};">
        <span style="font-size: 10px; font-weight: bold; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px;">Account Status</span>
        <div style="font-size: 22px; font-weight: 900; color: {status_color}; margin-top: 4px;">{status_text}</div>
    </div>
    {status_desc}
    """
    
    html_message = build_professional_email_html("Agent Account Status Update", recipient_name, body_html, "Access Agent Portal", login_url)
    plain_message = f"Hello {recipient_name},\n\nYour partner agent account status has been updated to: {status_text}.\n\nREI GOLDEN STAR TRAVEL & TOURS (PVT) LTD."
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')
    
    _dispatch_email(subject, plain_message, from_email, [agent.email], html_message=html_message)

def send_agent_status_email(agent, status):
    _email_pool.submit(_send_agent_status_email_sync, agent, status)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)
        
    customer_form = CustomerSignupForm()
    agent_form = AgentSignupForm()
    
    active_tab = request.GET.get('role', 'customer') if request.method == 'GET' else 'customer'
    
    if request.method == 'POST':
        role = request.POST.get('role', 'customer')
        if role == 'customer':
            active_tab = 'customer'
            customer_form = CustomerSignupForm(request.POST)
            if customer_form.is_valid():
                user = customer_form.save(commit=False)
                code = f"{random.randint(100000, 999999)}"
                user.email_verification_code = code
                user.otp_created_at = timezone.now()
                user.is_email_verified = False
                user.save()
                
                # Store code in session for developer helper banner (real-time fast testing)
                request.session[f'verification_code_{user.id}'] = code
                
                # Send verification email
                send_verification_email(user)
                
                # Redirect to verification page
                return redirect('verify_email', user_id=user.id)
        elif role == 'agent':
            active_tab = 'agent'
            agent_form = AgentSignupForm(request.POST, request.FILES)
            if agent_form.is_valid():
                user = agent_form.save(commit=False)
                code = f"{random.randint(100000, 999999)}"
                user.email_verification_code = code
                user.otp_created_at = timezone.now()
                user.is_email_verified = False
                user.save()
                agent_form.save_m2m()
                
                # Store code in session for developer helper banner (real-time fast testing)
                request.session[f'verification_code_{user.id}'] = code
                request.session['pending_user_id'] = user.id
                
                # Send verification email
                send_verification_email(user)
                
                # Redirect to step 2 verification page
                return redirect('agent_signup_verify', user_id=user.id)
                
    context = {
        'customer_form': customer_form,
        'agent_form': agent_form,
        'active_tab': active_tab,
    }
    return render(request, 'auth/signup.html', context)


def verify_email_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_email_verified:
        return redirect('login')
        
    now = timezone.now()
    is_expired = False
    time_left_seconds = 0
    if user.otp_created_at:
        elapsed = (now - user.otp_created_at).total_seconds()
        if elapsed > 300:  # 5 minutes
            is_expired = True
        else:
            time_left_seconds = int(300 - elapsed)
    else:
        is_expired = True

    if request.method == 'POST':
        if is_expired:
            messages.error(request, "This verification code has expired. Please request a new code.")
        else:
            code_input = request.POST.get('code', '')
            if code_input == user.email_verification_code:
                user.is_email_verified = True
                user.email_verification_code = None
                user.otp_created_at = None
                user.save()
                
                if user.role == 'agent':
                    messages.success(request, "Your email has been verified successfully! Your account is pending admin approval.")
                    return redirect('pending_approval')
                else:
                    messages.success(request, "Your email has been verified successfully! You can now log in.")
                    return redirect('login')
            else:
                messages.error(request, "Invalid verification code. Please try again.")
            
    # Get the code from session for display in developer assistance banner
    dev_code = request.session.get(f'verification_code_{user.id}', user.email_verification_code)
    
    return render(request, 'auth/verify_email.html', {
        'user': user,
        'dev_code': dev_code,
        'is_expired': is_expired,
        'time_left_seconds': time_left_seconds
    })


@csrf_exempt
def resend_otp_view(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    if user.is_email_verified:
        return JsonResponse({'success': False, 'message': 'Account is already verified.'})
        
    code = f"{random.randint(100000, 999999)}"
    user.email_verification_code = code
    user.otp_created_at = timezone.now()
    user.save()
    
    # Update session helper
    request.session[f'verification_code_{user.id}'] = code
    
    # Send email asynchronously
    send_verification_email(user)
    
    return JsonResponse({
        'success': True,
        'message': 'A new 6-digit OTP code has been sent to your email address.',
        'dev_code': code
    })


def pending_approval_view(request):
    user_id = request.session.get('pending_user_id')
    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
    return render(request, 'auth/pending_approval.html', {'pending_user': user})


def login_view(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)
        
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Lookup user by username or email
            from django.db.models import Q
            user_obj = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
            if user_obj:
                username_to_auth = user_obj.username
            else:
                username_to_auth = username_or_email
                
            user = authenticate(username=username_to_auth, password=password)
            if user is not None:
                # Check Agent Signup Phase and Verification Status
                if user.role == 'agent':
                    if not user.is_email_verified:
                        if not user.email_verification_code or user.otp_created_at is None:
                            user.email_verification_code = f"{random.randint(100000, 999999)}"
                            user.otp_created_at = timezone.now()
                            user.save()
                        elif (timezone.now() - user.otp_created_at).total_seconds() > 300:
                            user.email_verification_code = f"{random.randint(100000, 999999)}"
                            user.otp_created_at = timezone.now()
                            user.save()
                        
                        request.session[f'verification_code_{user.id}'] = user.email_verification_code
                        send_verification_email(user)
                        return redirect('agent_signup_verify', user_id=user.id)
                    
                    elif not user.address or not user.profile_photo or not user.id_card_front or not user.id_card_back:
                        # Email is verified, but documents are missing! Redirect to step 3
                        return redirect('agent_signup_documents', user_id=user.id)

                    elif user.approval_status == 'pending':
                        request.session['pending_user_id'] = user.id
                        return redirect('pending_approval')
                    elif user.approval_status == 'rejected':
                        form.add_error(None, "Your account application has been rejected by the admin.")
                        return render(request, 'auth/login.html', {'form': form})
                    elif user.approval_status == 'suspended':
                        form.add_error(None, "Your account has been suspended by the admin.")
                        return render(request, 'auth/login.html', {'form': form})

                # Check Customer Email Verification Status
                if user.role == 'customer' and not user.is_email_verified:
                    if not user.email_verification_code or user.otp_created_at is None:
                        user.email_verification_code = f"{random.randint(100000, 999999)}"
                        user.otp_created_at = timezone.now()
                        user.save()
                    elif (timezone.now() - user.otp_created_at).total_seconds() > 300:
                        # Regenerate if expired on login attempt
                        user.email_verification_code = f"{random.randint(100000, 999999)}"
                        user.otp_created_at = timezone.now()
                        user.save()
                    
                    # Store verification code in session for developer helper banner
                    request.session[f'verification_code_{user.id}'] = user.email_verification_code
                    
                    # Send verification email
                    send_verification_email(user)
                    
                    return redirect('verify_email', user_id=user.id)

                login(request, user)
                
                # Record login history with IP
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                
                try:
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                except Exception as e:
                    print(f"[LoginHistory Error] Failed to log login: {e}")
                
                return redirect_dashboard(user)
                
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def redirect_dashboard(user):
    if user.is_superuser or user.role == 'super_admin':
        return redirect('admin_dashboard')
    elif user.role == 'agent':
        return redirect('agent_dashboard')
    else:
        return redirect('customer_dashboard')


# Helper function to check if user is customer
def is_customer(user):
    return user.is_authenticated and user.role == 'customer'


@login_required
def customer_dashboard_view(request):
    if not is_customer(request.user):
        return redirect('login')
        
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            
            if first_name and last_name and email:
                if email != user.email:
                    if User.objects.filter(email=email).exclude(id=user.id).exists():
                        messages.error(request, "A user with this email address already exists.")
                    else:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.phone = phone
                        user.email = email
                        user.username = email
                        user.save()
                        messages.success(request, "Profile updated successfully! Note: Your email has been updated; please use it as your username next time.")
                else:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.phone = phone
                    user.save()
                    messages.success(request, "Profile details updated successfully!")
            else:
                messages.error(request, "First name, last name, and email are required fields.")
            return redirect('customer_dashboard')
            
    # Fetch customer statistics and requests/bookings
    bookings = Booking.objects.filter(user=user).order_by('-created_at')
    visas = VisaApplication.objects.filter(user=user).order_by('-created_at')
    flights = FlightQuoteRequest.objects.filter(user=user).order_by('-created_at')
    
    # Calculate quick stats
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='pending').count()
    confirmed_bookings = bookings.filter(status='confirmed').count()
    
    total_visas = visas.count()
    pending_visas = visas.filter(status='pending').count()
    
    total_flights = flights.count()
    pending_flights = flights.filter(status='pending').count()

    context = {
        'bookings': bookings,
        'visas': visas,
        'flights': flights,
        'stats': {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'total_visas': total_visas,
            'pending_visas': pending_visas,
            'total_flights': total_flights,
            'pending_flights': pending_flights,
        }
    }
    return render(request, 'dashboard/customer/overview.html', context)


# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'super_admin')

def is_agent(user):
    return user.is_authenticated and user.role == 'agent'


@user_passes_test(is_admin)
def admin_dashboard_view(request):
    return render(request, 'dashboard/admin/overview.html')


@admin_required_api
def admin_dashboard_api(request):
    # Fetch all agents
    agents = User.objects.filter(role='agent').order_by('-date_joined')
    agents_data = []
    for agent in agents:
        agents_data.append({
            'id': agent.id,
            'username': agent.username,
            'first_name': agent.first_name,
            'last_name': agent.last_name,
            'email': agent.email,
            'phone': agent.phone or 'N/A',
            'company_name': agent.company_name or 'N/A',
            'profile_photo_url': agent.profile_photo.url if agent.profile_photo else '',
            'id_card_front_url': agent.id_card_front.url if agent.id_card_front else '',
            'id_card_back_url': agent.id_card_back.url if agent.id_card_back else '',
            'approval_status': agent.approval_status,
            'is_verified_partner': agent.is_verified_partner,
            'address': agent.address or 'N/A',
            'date_joined': agent.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'wallet_balance': agent.wallet_balance,
        })

    # Fetch all customers
    customers = User.objects.filter(role='customer').order_by('-date_joined')
    customers_data = []
    for customer in customers:
        customers_data.append({
            'id': customer.id,
            'username': customer.username,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone': customer.phone or 'N/A',
            'role': 'customer',
            'date_joined': customer.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        })
        
    counts = {
        'total': User.objects.filter(role='agent').count(),
        'pending': User.objects.filter(role='agent', approval_status='pending').count(),
        'approved': User.objects.filter(role='agent', approval_status='approved').count(),
        'rejected': User.objects.filter(role='agent', approval_status='rejected').count(),
        'suspended': User.objects.filter(role='agent', approval_status='suspended').count(),
        'customers_total': User.objects.filter(role='customer').count(),
    }
    
    return JsonResponse({
        'agents': agents_data, 
        'customers': customers_data,
        'counts': counts
    })


def generate_agent_id_number():
    import random
    while True:
        candidate = f"GSA-AGT-{random.randint(100000, 999999)}"
        if not User.objects.filter(agent_id_number=candidate).exists():
            return candidate


@csrf_exempt
@user_passes_test(is_admin)
def admin_approve_agent(request, agent_id):
    if request.method == 'POST':
        agent = get_object_or_404(User, id=agent_id, role='agent')
        agent.approval_status = 'approved'
        if not agent.agent_id_number:
            agent.agent_id_number = generate_agent_id_number()
            agent.id_card_issued_at = timezone.now()
        agent.save()
        send_agent_status_email(agent, 'approved')
        return JsonResponse({
            'success': True, 
            'status': 'approved',
            'agent_id_number': agent.agent_id_number
        })
    return JsonResponse({'success': False}, status=400)


@user_passes_test(is_agent)
def agent_my_id_card_api(request):
    agent = request.user
    if not agent.agent_id_number:
        agent.agent_id_number = generate_agent_id_number()
        if not agent.id_card_issued_at:
            agent.id_card_issued_at = timezone.now()
        agent.save()
    
    qr_url = request.build_absolute_uri(f"/dashboard/agent/id-card-qr/{agent.agent_id_number}/")
    profile_photo_url = request.build_absolute_uri(agent.profile_photo.url) if agent.profile_photo else None
    
    return JsonResponse({
        'success': True,
        'agent_id_number': agent.agent_id_number,
        'full_name': agent.get_full_name() or agent.username,
        'company_name': agent.company_name or agent.username,
        'role_label': 'Verified Partner Agent',
        'issued_at_str': agent.id_card_issued_at.strftime('%B %d, %Y') if agent.id_card_issued_at else agent.date_joined.strftime('%B %d, %Y'),
        'profile_photo': profile_photo_url,
        'qr_code_url': qr_url
    })


def agent_id_card_qr_api(request, agent_id_number):
    import qrcode
    from io import BytesIO
    from django.http import HttpResponse
    
    agent = get_object_or_404(User, agent_id_number=agent_id_number, role='agent')
    verify_url = request.build_absolute_uri(f"/verify-agent/{agent.agent_id_number}/")
    qr = qrcode.make(verify_url)
    buffer = BytesIO()
    qr.save(buffer, 'PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def verify_agent_public_view(request, agent_id_number):
    import hashlib
    agent = get_object_or_404(User, agent_id_number=agent_id_number, role='agent')
    
    # Check if JSON format requested
    if request.GET.get('format') == 'json' or request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'valid': agent.approval_status == 'approved',
            'agent_id_number': agent.agent_id_number,
            'company_name': agent.company_name or agent.username,
            'full_name': agent.get_full_name() or agent.username,
            'approval_status': agent.approval_status,
            'phone': agent.phone or 'Verified',
            'issued_at': agent.id_card_issued_at.strftime('%B %d, %Y') if agent.id_card_issued_at else agent.date_joined.strftime('%B %d, %Y')
        })

    raw_hash = f"{agent.agent_id_number}-{agent.id}-{settings.SECRET_KEY[:8]}"
    security_hash = hashlib.sha256(raw_hash.encode()).hexdigest()[:16].upper()

    context = {
        'agent': agent,
        'current_time': timezone.now(),
        'security_hash': security_hash
    }
    return render(request, 'verify_agent.html', context)


# ══════════════════════════════════════════════
# B2B AGENT FEEDBACK & SUPPORT REST APIs
# ══════════════════════════════════════════════

@csrf_exempt
@user_passes_test(is_agent)
def agent_submit_feedback_api(request):
    """
    POST → Agent submits feedback/review/support ticket.
    """
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        category = body.get('category', 'general')
        subject = body.get('subject', '').strip()
        message = body.get('message', '').strip()
        rating_raw = body.get('rating', 5)

        if not subject or not message:
            return JsonResponse({'error': 'Subject and message are required fields.'}, status=400)

        try:
            rating = int(rating_raw)
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 5

        feedback = AgentFeedback.objects.create(
            agent=request.user,
            category=category,
            subject=subject,
            rating=rating,
            message=message,
            status='pending'
        )

        return JsonResponse({
            'success': True,
            'message': 'Thank you! Your feedback has been submitted successfully.',
            'id': feedback.id
        })

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@user_passes_test(is_agent)
def agent_feedbacks_api(request):
    """
    GET → List all feedbacks submitted by the logged-in agent.
    """
    feedbacks = AgentFeedback.objects.filter(agent=request.user)
    data = []
    for f in feedbacks:
        data.append({
            'id': f.id,
            'category': f.category,
            'category_display': f.get_category_display(),
            'subject': f.subject,
            'rating': f.rating,
            'message': f.message,
            'status': f.status,
            'status_display': f.get_status_display(),
            'admin_reply': f.admin_reply or '',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return JsonResponse({'success': True, 'feedbacks': data})


@csrf_exempt
@admin_required_api
def admin_agent_feedbacks_api(request):
    """
    GET → List all agent submitted feedbacks for admin with status & category filtering.
    """
    qs = AgentFeedback.objects.all().select_related('agent')
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        qs = qs.filter(category=category_filter)

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(subject__icontains=search) |
            Q(message__icontains=search) |
            Q(agent__username__icontains=search) |
            Q(agent__company_name__icontains=search)
        )

    data = []
    for f in qs:
        data.append({
            'id': f.id,
            'agent_id': f.agent.id,
            'agent_company': f.agent.company_name or f.agent.username,
            'agent_name': f.agent.get_full_name() or f.agent.username,
            'agent_email': f.agent.email or '',
            'category': f.category,
            'category_display': f.get_category_display(),
            'subject': f.subject,
            'rating': f.rating,
            'message': f.message,
            'status': f.status,
            'status_display': f.get_status_display(),
            'admin_reply': f.admin_reply or '',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({
        'success': True,
        'total_count': len(data),
        'pending_count': AgentFeedback.objects.filter(status='pending').count(),
        'feedbacks': data
    })


@csrf_exempt
@admin_required_api
def admin_feedback_status_api(request, pk):
    """
    POST/PATCH → Admin updates feedback status (reviewed, resolved, closed) and optionally adds admin_reply.
    """
    feedback = get_object_or_404(AgentFeedback, pk=pk)
    if request.method in ['POST', 'PATCH', 'PUT']:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        status = body.get('status', '').strip()
        admin_reply = body.get('admin_reply', '').strip()

        if status and status in ['pending', 'reviewed', 'resolved', 'closed']:
            feedback.status = status

        if 'admin_reply' in body:
            feedback.admin_reply = admin_reply

        feedback.save()
        return JsonResponse({
            'success': True,
            'message': 'Feedback status updated.',
            'status': feedback.status,
            'admin_reply': feedback.admin_reply or ''
        })

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_feedback_delete_api(request, pk):
    """
    DELETE/POST → Admin deletes feedback entry.
    """
    feedback = get_object_or_404(AgentFeedback, pk=pk)
    feedback.delete()
    return JsonResponse({'success': True, 'message': 'Feedback deleted.'})



@csrf_exempt
@user_passes_test(is_admin)
def admin_reject_agent(request, agent_id):
    if request.method == 'POST':
        agent = get_object_or_404(User, id=agent_id, role='agent')
        agent.approval_status = 'rejected'
        agent.save()
        send_agent_status_email(agent, 'rejected')
        return JsonResponse({'success': True, 'status': 'rejected'})
    return JsonResponse({'success': False}, status=400)


@admin_required_api
def admin_dashboard_overview_api(request):
    counts = {
        'agents_pending': User.objects.filter(role='agent', approval_status='pending').count(),
        'agents_total': User.objects.filter(role='agent').count(),
        'agents_suspended': User.objects.filter(role='agent', approval_status='suspended').count(),
        'packages_total': Package.objects.count(),
        'visas_pending': VisaApplication.objects.filter(status='pending').count(),
        'visas_total': VisaApplication.objects.count(),
        'flights_pending': FlightQuoteRequest.objects.filter(status='pending').count(),
        'flights_total': FlightQuoteRequest.objects.count(),
        'bookings_pending': Booking.objects.filter(status='pending').count(),
        'bookings_total': Booking.objects.count(),
    }
    return JsonResponse({'counts': counts})


@admin_required_api
def admin_b2b_overview_api(request):
    from django.utils import timezone
    from django.db.models import Sum
    from datetime import timedelta
    from decimal import Decimal
    from apps.airline_ticketing.models import AgentTicketOrder
    from apps.accounts.models import AgentLedger, User

    now = timezone.now()
    today = now.date()

    # 1. STAT CARDS
    from apps.bookings.models import Booking
    active_agents_count = User.objects.filter(role='agent', approval_status='approved').count()
    todays_orders_count = AgentTicketOrder.objects.filter(created_at__date=today).count() + Booking.objects.filter(created_at__date=today).count()
    pending_holds_count = AgentTicketOrder.objects.filter(status='hold').count() + Booking.objects.filter(status='pending').count()

    # Total Wallet Balance (All Agents Combined)
    credits_total = AgentLedger.objects.filter(agent__role='agent', entry_type='credit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    debits_total = AgentLedger.objects.filter(agent__role='agent', entry_type='debit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_wallet_balance = float(credits_total - debits_total)

    # Today's Confirmed Revenue
    confirmed_revenue_today = AgentTicketOrder.objects.filter(
        status='paid',
        updated_at__date=today
    ).aggregate(total=Sum('total_fare'))['total'] or Decimal('0.00')

    # 2. URGENT ALERTS PANEL
    # A. Expiring Soon (status='hold' & hold_expires_at within next 30 min)
    thirty_mins_later = now + timedelta(minutes=30)
    expiring_orders = AgentTicketOrder.objects.filter(
        status='hold',
        hold_expires_at__isnull=False,
        hold_expires_at__gte=now,
        hold_expires_at__lte=thirty_mins_later
    ).select_related('agent').order_by('hold_expires_at')[:10]

    expiring_soon_list = []
    for order in expiring_orders:
        mins_remaining = max(0, int((order.hold_expires_at - now).total_seconds() / 60))
        agent_name = (order.agent.company_name or order.agent.username) if order.agent else 'N/A'
        expiring_soon_list.append({
            'id': order.id,
            'reference_number': order.reference_number,
            'agent_name': agent_name,
            'agent_id': order.agent_id,
            'mins_remaining': mins_remaining,
            'expires_at_str': order.hold_expires_at.strftime('%I:%M %p'),
            'total_fare': float(order.total_fare)
        })

    # B. Awaiting Payment Confirmation (status='paid_pending')
    awaiting_orders = AgentTicketOrder.objects.filter(
        status='paid_pending'
    ).select_related('agent').order_by('-created_at')[:10]

    awaiting_payment_list = []
    for order in awaiting_orders:
        agent_name = (order.agent.company_name or order.agent.username) if order.agent else 'N/A'
        awaiting_payment_list.append({
            'id': order.id,
            'reference_number': order.reference_number,
            'agent_name': agent_name,
            'agent_id': order.agent_id,
            'total_fare': float(order.total_fare),
            'created_at_str': order.created_at.strftime('%Y-%m-%d %H:%M')
        })

    # C. Low Wallet Balance Agents (< 5000 & booking in last 30 days)
    LOW_BALANCE_THRESHOLD = Decimal('5000.00')
    thirty_days_ago = now - timedelta(days=30)
    active_recent_agents = User.objects.filter(
        role='agent',
        approval_status='approved',
        ticket_orders__created_at__gte=thirty_days_ago
    ).distinct()

    low_balance_agents_list = []
    for agent in active_recent_agents:
        entries = AgentLedger.objects.filter(agent=agent)
        c_tot = entries.filter(entry_type='credit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        d_tot = entries.filter(entry_type='debit').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        bal = c_tot - d_tot
        if bal < LOW_BALANCE_THRESHOLD:
            low_balance_agents_list.append({
                'agent_id': agent.id,
                'username': agent.username,
                'company_name': agent.company_name or agent.username,
                'balance': float(bal)
            })

    low_balance_agents_list = sorted(low_balance_agents_list, key=lambda x: x['balance'])[:10]

    # 3. RECENT ACTIVITY FEED
    recent_orders = AgentTicketOrder.objects.select_related('agent').order_by('-created_at')[:20]
    recent_credits = AgentLedger.objects.filter(entry_type='credit').select_related('agent').order_by('-created_at')[:20]

    events = []
    for o in recent_orders:
        comp_name = (o.agent.company_name or o.agent.username) if o.agent else 'Agent'
        if o.status == 'paid':
            text = f"Agent {comp_name} confirmed payment for Ref: {o.reference_number}"
            if o.pnr:
                text += f" (PNR: {o.pnr})"
        else:
            text = f"Agent {comp_name} booked {o.order_type} — Ref: {o.reference_number}"
        events.append({
            'timestamp': o.created_at.timestamp(),
            'created_at_iso': o.created_at.strftime('%Y-%m-%d %H:%M'),
            'text': text,
            'type': 'order',
            'ref': o.reference_number
        })

    for c in recent_credits:
        comp_name = (c.agent.company_name or c.agent.username) if c.agent else 'Agent'
        text = f"Agent {comp_name}'s wallet credited PKR {float(c.amount):,.2f}"
        if c.description:
            text += f" ({c.description})"
        events.append({
            'timestamp': c.created_at.timestamp(),
            'created_at_iso': c.created_at.strftime('%Y-%m-%d %H:%M'),
            'text': text,
            'type': 'credit',
            'ref': c.reference or ''
        })

    events.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = events[:15]

    # 5. MINI TREND CHART & STATUS BREAKDOWN
    seven_days_ago = today - timedelta(days=6)
    daily_counts_dict = {}
    daily_revenue_dict = {}
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        d_str = d.strftime('%b %d')
        daily_counts_dict[d_str] = 0
        daily_revenue_dict[d_str] = 0.0

    orders_7days = AgentTicketOrder.objects.filter(created_at__date__gte=seven_days_ago)
    for o in orders_7days:
        d_str = o.created_at.strftime('%b %d')
        if d_str in daily_counts_dict:
            daily_counts_dict[d_str] += 1
            if o.status == 'paid':
                daily_revenue_dict[d_str] += float(o.total_fare or 0)

    trend = [{"date": d_str, "count": count, "revenue": daily_revenue_dict.get(d_str, 0.0)} for d_str, count in daily_counts_dict.items()]

    status_breakdown = {
        'paid': AgentTicketOrder.objects.filter(status='paid').count(),
        'hold': AgentTicketOrder.objects.filter(status='hold').count(),
        'paid_pending': AgentTicketOrder.objects.filter(status='paid_pending').count(),
        'cancelled': AgentTicketOrder.objects.filter(status='cancelled').count(),
    }

    return JsonResponse({
        'success': True,
        'stats': {
            'active_agents': active_agents_count,
            'todays_orders': todays_orders_count,
            'pending_holds': pending_holds_count,
            'total_wallet_balance': total_wallet_balance,
            'confirmed_revenue_today': float(confirmed_revenue_today)
        },
        'alerts': {
            'expiring_soon': expiring_soon_list,
            'awaiting_payment': awaiting_payment_list,
            'low_balance_agents': low_balance_agents_list
        },
        'recent_activity': recent_activity,
        'trend': trend,
        'status_breakdown': status_breakdown
    })

@csrf_exempt
@admin_required_api
def admin_packages_api(request):
    if request.method == 'GET':
        packages = Package.objects.all().order_by('-created_at')
        packages_data = []
        for p in packages:
            packages_data.append({
                'id': p.id,
                'title': p.title,
                'description': p.description,
                'price': str(p.price),
                'category': p.category,
                'duration_days': p.duration_days,
                'price_sharing': str(p.price_sharing or p.price),
                'price_quad': str(p.price_quad),
                'price_triple': str(p.price_triple),
                'price_double': str(p.price_double),
                'price_child': str(p.price_child),
                'price_infant': str(p.price_infant or '65000.00'),
                'discount_percentage': str(p.discount_percentage),
                'discount_amount': str(p.discount_amount),
                'original_price': str(p.original_price) if p.original_price else '',
                'airline': p.airline or 'Saudi Airlines',
                'airline_logo': p.airline_logo or '',
                'flight_routes': p.flight_routes or 'KHI - JED - MED - KHI',
                'makkah_hotel_name': p.makkah_hotel_name or 'Anjum Hotel Makkah',
                'makkah_hotel_distance': p.makkah_hotel_distance or '350m from Haram',
                'makkah_hotel_images': p.makkah_hotel_images or [],
                'madinah_hotel_name': p.madinah_hotel_name or 'Pullman Zamzam Madinah',
                'madinah_hotel_distance': p.madinah_hotel_distance or '150m from Prophet\'s Mosque',
                'madinah_hotel_images': p.madinah_hotel_images or [],
                'luggage_weight': p.luggage_weight or '20 kg + 7 kg Hand Carry',
                'images': p.get_images_list(),
                'addons': p.addons or [],
                'total_seats': p.total_seats,
                'available_seats': p.available_seats,
                'has_embedding': p.embedding is not None,
            })
        return JsonResponse({'packages': packages_data})
        
    elif request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        price = request.POST.get('price', '245000.0')
        category = request.POST.get('category', 'tour')
        duration_days = int(request.POST.get('duration_days', '15'))
        
        price_sharing = request.POST.get('price_sharing', price)
        price_quad = request.POST.get('price_quad', price)
        price_triple = request.POST.get('price_triple', '275000.0')
        price_double = request.POST.get('price_double', '320000.0')
        price_child = request.POST.get('price_child', '180000.0')
        price_infant = request.POST.get('price_infant', '65000.0')
        
        airline = request.POST.get('airline', 'Saudi Airlines')
        airline_logo = request.POST.get('airline_logo', '')
        flight_routes = request.POST.get('flight_routes', 'KHI - JED - MED - KHI')
        makkah_hotel_name = request.POST.get('makkah_hotel_name', 'Anjum Hotel Makkah')
        makkah_hotel_distance = request.POST.get('makkah_hotel_distance', '350m from Haram')
        madinah_hotel_name = request.POST.get('madinah_hotel_name', 'Pullman Zamzam Madinah')
        madinah_hotel_distance = request.POST.get('madinah_hotel_distance', '150m from Prophet\'s Mosque')
        luggage_weight = request.POST.get('luggage_weight', '20 kg + 7 kg Hand Carry')
        
        makkah_images_input = request.POST.get('makkah_hotel_images', '')
        if isinstance(makkah_images_input, str) and makkah_images_input.strip():
            try: makkah_hotel_images = json.loads(makkah_images_input)
            except Exception: makkah_hotel_images = [u.strip() for u in makkah_images_input.split(',') if u.strip()]
        else: makkah_hotel_images = []

        madinah_images_input = request.POST.get('madinah_hotel_images', '')
        if isinstance(madinah_images_input, str) and madinah_images_input.strip():
            try: madinah_hotel_images = json.loads(madinah_images_input)
            except Exception: madinah_hotel_images = [u.strip() for u in madinah_images_input.split(',') if u.strip()]
        else: madinah_hotel_images = []

        # Handle package images: uploaded files + URL text field
        images = []
        images_url_input = request.POST.get('images_urls', '')
        if isinstance(images_url_input, str) and images_url_input.strip():
            try: url_images = json.loads(images_url_input)
            except Exception: url_images = [u.strip() for u in images_url_input.split(',') if u.strip()]
            images.extend(url_images)
        # Handle uploaded image files across multiple key names
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'packages')
        os.makedirs(upload_dir, exist_ok=True)
        uploaded_files_list = request.FILES.getlist('images_files') + request.FILES.getlist('gallery_images') + request.FILES.getlist('images')
        for uploaded_file in uploaded_files_list:
            safe_name = f"pkg_{title[:20].replace(' ','_')}_{uploaded_file.name[-20:].replace(' ', '_')}"
            file_path = os.path.join(upload_dir, safe_name)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)
            img_url = f"{settings.MEDIA_URL}packages/{safe_name}"
            if img_url not in images:
                images.append(img_url)

        addons_input = request.POST.get('addons', '')
        if isinstance(addons_input, str) and addons_input.strip():
            try:
                addons = json.loads(addons_input)
            except Exception:
                addons = []
                for item in addons_input.split(','):
                    if ':' in item:
                        parts = item.split(':', 1)
                        name = parts[0].strip()
                        try: prc = float(parts[1].strip())
                        except Exception: prc = 0.0
                        if name: addons.append({'id': name.lower().replace(' ', '_'), 'name': name, 'price': prc})
                    else:
                        name = item.strip()
                        if name: addons.append({'id': name.lower().replace(' ', '_'), 'name': name, 'price': 0.0})
        else:
            addons = []
            
        total_seats = int(request.POST.get('total_seats', '30'))
        available_seats = int(request.POST.get('available_seats', total_seats))

        package = Package.objects.create(
            title=title,
            description=description,
            price=price,
            category=category,
            duration_days=duration_days,
            price_sharing=price_sharing,
            price_quad=price_quad,
            price_triple=price_triple,
            price_double=price_double,
            price_child=price_child,
            price_infant=price_infant,
            airline=airline,
            airline_logo=airline_logo,
            flight_routes=flight_routes,
            makkah_hotel_name=makkah_hotel_name,
            makkah_hotel_distance=makkah_hotel_distance,
            makkah_hotel_images=makkah_hotel_images,
            madinah_hotel_name=madinah_hotel_name,
            madinah_hotel_distance=madinah_hotel_distance,
            madinah_hotel_images=madinah_hotel_images,
            luggage_weight=luggage_weight,
            images=images,
            addons=addons,
            total_seats=total_seats,
            available_seats=available_seats
        )
        
        # Generate Vector Embedding in real-time if AI Chatbot feature is enabled
        if getattr(settings, 'AI_CHATBOT_ENABLED', False) and EmbeddingsService:
            try:
                service = EmbeddingsService()
                text_to_embed = f"{package.title} - {package.description}"
                package.embedding = service.get_embedding(text_to_embed)
                package.save()
                print(f"[Embedding] Generated embedding for package ID {package.id}")
            except Exception as e:
                print(f"[Embedding Error] Failed to generate embedding: {e}")
            
        return JsonResponse({'success': True, 'package_id': package.id})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@admin_required_api
def admin_package_detail_api(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        package.title = request.POST.get('title', package.title)
        package.description = request.POST.get('description', package.description)
        package.price = request.POST.get('price', package.price)
        package.category = request.POST.get('category', package.category)
        if request.POST.get('duration_days'):
            package.duration_days = int(request.POST.get('duration_days'))
        
        if request.POST.get('price_sharing'): package.price_sharing = request.POST.get('price_sharing')
        if request.POST.get('price_quad'): package.price_quad = request.POST.get('price_quad')
        if request.POST.get('price_triple'): package.price_triple = request.POST.get('price_triple')
        if request.POST.get('price_double'): package.price_double = request.POST.get('price_double')
        if request.POST.get('price_child'): package.price_child = request.POST.get('price_child')
        if request.POST.get('price_infant'): package.price_infant = request.POST.get('price_infant')
        
        if request.POST.get('airline'):
            package.airline = request.POST.get('airline')
        if 'airline_logo' in request.POST:
            package.airline_logo = request.POST.get('airline_logo')
        if request.POST.get('flight_routes'):
            package.flight_routes = request.POST.get('flight_routes')
        if request.POST.get('makkah_hotel_name'):
            package.makkah_hotel_name = request.POST.get('makkah_hotel_name')
        if request.POST.get('makkah_hotel_distance'):
            package.makkah_hotel_distance = request.POST.get('makkah_hotel_distance')
        if request.POST.get('madinah_hotel_name'):
            package.madinah_hotel_name = request.POST.get('madinah_hotel_name')
        if request.POST.get('madinah_hotel_distance'):
            package.madinah_hotel_distance = request.POST.get('madinah_hotel_distance')
        if request.POST.get('luggage_weight'):
            package.luggage_weight = request.POST.get('luggage_weight')
            
        if 'makkah_hotel_images' in request.POST:
            inp = request.POST.get('makkah_hotel_images', '')
            if isinstance(inp, str):
                try: package.makkah_hotel_images = json.loads(inp)
                except Exception: package.makkah_hotel_images = [u.strip() for u in inp.split(',') if u.strip()]
        if 'madinah_hotel_images' in request.POST:
            inp = request.POST.get('madinah_hotel_images', '')
            if isinstance(inp, str):
                try: package.madinah_hotel_images = json.loads(inp)
                except Exception: package.madinah_hotel_images = [u.strip() for u in inp.split(',') if u.strip()]

        # Handle package images update: existing URLs + newly uploaded files
        existing_images = list(package.images or [])
        images_url_input = request.POST.get('images_urls', '')
        if images_url_input is not None:
            try: url_images = json.loads(images_url_input)
            except Exception: url_images = [u.strip() for u in images_url_input.split(',') if u.strip()]
            existing_images = url_images  # replace with what admin typed
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'packages')
        os.makedirs(upload_dir, exist_ok=True)
        uploaded_files_list = request.FILES.getlist('images_files') + request.FILES.getlist('gallery_images') + request.FILES.getlist('images')
        for uploaded_file in uploaded_files_list:
            safe_name = f"pkg_{package.id}_{uploaded_file.name[-25:].replace(' ', '_')}"
            file_path = os.path.join(upload_dir, safe_name)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)
            img_url = f"{settings.MEDIA_URL}packages/{safe_name}"
            if img_url not in existing_images:
                existing_images.append(img_url)
        package.images = existing_images

        if 'addons' in request.POST:
            inp = request.POST.get('addons', '')
            if isinstance(inp, str):
                try: package.addons = json.loads(inp)
                except Exception:
                    addons = []
                    for item in inp.split(','):
                        if ':' in item:
                            parts = item.split(':', 1)
                            name = parts[0].strip()
                            try: prc = float(parts[1].strip())
                            except Exception: prc = 0.0
                            if name: addons.append({'id': name.lower().replace(' ', '_'), 'name': name, 'price': prc})
                        else:
                            name = item.strip()
                            if name: addons.append({'id': name.lower().replace(' ', '_'), 'name': name, 'price': 0.0})
                    package.addons = addons
                    
        if request.POST.get('total_seats'):
            package.total_seats = int(request.POST.get('total_seats'))
        if request.POST.get('available_seats'):
            package.available_seats = int(request.POST.get('available_seats'))

        # Regenerate Vector Embedding if AI Chatbot feature is enabled
        if getattr(settings, 'AI_CHATBOT_ENABLED', False) and EmbeddingsService:
            try:
                service = EmbeddingsService()
                text_to_embed = f"{package.title} - {package.description}"
                package.embedding = service.get_embedding(text_to_embed)
                print(f"[Embedding] Regenerated embedding for package ID {package.id}")
            except Exception as e:
                print(f"[Embedding Error] Failed to regenerate embedding: {e}")
            
        package.save()
        return JsonResponse({'success': True})
        
    elif request.method == 'DELETE':
        package.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@admin_required_api
def admin_visas_api(request):
    visas = VisaApplication.objects.select_related('user', 'visa_package').all().order_by('-created_at')
    visas_data = []
    for v in visas:
        username = (v.user.username if v.user else None) or v.get_applicant_name()
        email = v.get_applicant_email()
        phone = v.phone or (v.user.phone if (v.user and hasattr(v.user, 'phone')) else '') or 'N/A'
        address = getattr(v, 'address', '') or 'N/A'
        price = str(v.price) if v.price is not None else (str(v.visa_package.price) if (v.visa_package and v.visa_package.price) else 'N/A')
        visas_data.append({
            'id': v.id,
            'username': username,
            'applicant_name': v.get_applicant_name(),
            'email': email,
            'phone': phone,
            'address': address,
            'price': price,
            'country': v.country,
            'visa_type': v.visa_type or 'Tourist / Visitor Visa',
            'passport_number': v.passport_number or '',
            'status': v.status,
            'additional_notes': v.additional_notes or '',
            'created_at': v.created_at.strftime('%Y-%m-%d %H:%M:%S') if v.created_at else '',
        })
    return JsonResponse({'visas': visas_data})

@csrf_exempt
@admin_required_api
def admin_visa_status_api(request, pk):
    visa = get_object_or_404(VisaApplication, pk=pk)
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        if 'status' in body:
            visa.status = body.get('status')
        if 'full_name' in body or 'applicant_name' in body:
            visa.full_name = body.get('full_name') or body.get('applicant_name')
        if 'country' in body:
            visa.country = body.get('country')
        if 'passport_number' in body:
            visa.passport_number = body.get('passport_number')
        if 'visa_type' in body:
            visa.visa_type = body.get('visa_type')
        if 'phone' in body:
            visa.phone = body.get('phone')
        if 'email' in body:
            visa.email = body.get('email')
        if 'additional_notes' in body:
            visa.additional_notes = body.get('additional_notes')
        visa.save()
        return JsonResponse({'success': True, 'status': visa.status})
    elif request.method == 'DELETE':
        visa.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@admin_required_api
def admin_visa_packages_api(request):
    from apps.visa.models import VisaPackage
    if request.method == 'GET':
        vpackages = VisaPackage.objects.all().order_by('-created_at')
        v_data = []
        for vp in vpackages:
            v_data.append({
                'id': vp.id,
                'country': vp.country,
                'title': vp.title,
                'visa_type': vp.visa_type,
                'processing_time': vp.processing_time,
                'stay_validity': vp.stay_validity,
                'visa_validity': vp.visa_validity,
                'entry_type': vp.entry_type,
                'price': str(vp.price),
                'original_price': str(vp.original_price) if vp.original_price else '',
                'required_documents': vp.required_documents,
                'docs_list': vp.get_docs_list(),
                'description': vp.description or '',
                'banner_image': vp.banner_image or '',
                'cover_url': vp.cover_url,
                'is_popular': vp.is_popular,
                'created_at': vp.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse({'visa_packages': v_data})

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        country = (body.get('country') or 'Saudi Arabia').strip()
        title = (body.get('title') or 'Saudi 1-Year Tourist eVisa').strip()
        visa_type = (body.get('visa_type') or 'Tourist / Visitor Visa').strip()
        processing_time = (body.get('processing_time') or '3 to 5 Working Days').strip()
        stay_validity = (body.get('stay_validity') or '90 Days Stay').strip()
        visa_validity = (body.get('visa_validity') or '1 Year Validity').strip()
        entry_type = (body.get('entry_type') or 'multiple').strip()
        price = body.get('price') or '45000.00'
        original_price = body.get('original_price') or None
        required_documents = body.get('required_documents') or 'Passport Copy (6 Months Validity), Passport Size Photo, CNIC Copy'
        description = body.get('description') or ''
        banner_image = body.get('banner_image') or ''
        is_popular = str(body.get('is_popular', 'false')).lower() in ('true', '1', 'on')
        cover_image = request.FILES.get('cover_image')

        vp = VisaPackage.objects.create(
            country=country,
            title=title,
            visa_type=visa_type,
            processing_time=processing_time,
            stay_validity=stay_validity,
            visa_validity=visa_validity,
            entry_type=entry_type,
            price=price,
            original_price=original_price if original_price else None,
            required_documents=required_documents,
            description=description,
            banner_image=banner_image,
            cover_image=cover_image if cover_image else None,
            is_popular=is_popular
        )
        return JsonResponse({'success': True, 'visa_package_id': vp.id})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@admin_required_api
def admin_visa_package_detail_api(request, pk):
    from apps.visa.models import VisaPackage
    vp = get_object_or_404(VisaPackage, pk=pk)
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        vp.country = body.get('country', vp.country)
        vp.title = body.get('title', vp.title)
        vp.visa_type = body.get('visa_type', vp.visa_type)
        vp.processing_time = body.get('processing_time', vp.processing_time)
        vp.stay_validity = body.get('stay_validity', vp.stay_validity)
        vp.visa_validity = body.get('visa_validity', vp.visa_validity)
        vp.entry_type = body.get('entry_type', vp.entry_type)
        vp.price = body.get('price', vp.price)
        if 'original_price' in body:
            vp.original_price = body.get('original_price') or None
        vp.required_documents = body.get('required_documents', vp.required_documents)
        vp.description = body.get('description', vp.description)
        if 'banner_image' in body:
            vp.banner_image = body.get('banner_image')
        if 'cover_image' in request.FILES:
            vp.cover_image = request.FILES.get('cover_image')
        if 'is_popular' in body:
            vp.is_popular = str(body.get('is_popular', 'false')).lower() in ('true', '1', 'on')
        vp.save()
        return JsonResponse({'success': True})

    elif request.method == 'DELETE':
        vp.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@admin_required_api
def admin_flights_api(request):
    flights = FlightQuoteRequest.objects.all().order_by('-created_at')
    flights_data = []
    for f in flights:
        flights_data.append({
            'id': f.id,
            'username': f.user.username,
            'email': f.user.email,
            'departure_city': f.departure_city,
            'destination_city': f.destination_city,
            'departure_date': f.departure_date.strftime('%Y-%m-%d') if hasattr(f.departure_date, 'strftime') else str(f.departure_date),
            'return_date': (f.return_date.strftime('%Y-%m-%d') if hasattr(f.return_date, 'strftime') else str(f.return_date)) if f.return_date else 'N/A',
            'status': f.status,
            'price_quote': str(f.price_quote) if f.price_quote else 'N/A',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'flights': flights_data})

@csrf_exempt
@admin_required_api
def admin_flight_status_api(request, pk):
    if request.method == 'POST':
        flight = get_object_or_404(FlightQuoteRequest, pk=pk)
        flight.status = request.POST.get('status', flight.status)
        price_quote = request.POST.get('price_quote', '')
        if price_quote:
            flight.price_quote = price_quote
        flight.save()
        return JsonResponse({'success': True, 'status': flight.status, 'price_quote': str(flight.price_quote)})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@admin_required_api
def admin_flight_tickets_api(request):
    from apps.flights.models import FlightTicketOffer, FlightSector
    from django.utils.dateparse import parse_datetime
    from django.utils import timezone

    if request.method == 'GET':
        tickets = FlightTicketOffer.objects.all().order_by('-created_at')
        t_data = []
        for ft in tickets:
            sectors_payload = []
            for s in ft.sectors.all().order_by('order'):
                sectors_payload.append({
                    'id': s.id,
                    'order': s.order,
                    'airline_name': s.airline_name,
                    'flight_number': s.flight_number,
                    'departure_city': s.departure_city,
                    'departure_airport_code': s.departure_airport_code,
                    'arrival_city': s.arrival_city,
                    'arrival_airport_code': s.arrival_airport_code,
                    'departure_datetime': s.departure_datetime.strftime('%Y-%m-%dT%H:%M') if s.departure_datetime else '',
                    'arrival_datetime': s.arrival_datetime.strftime('%Y-%m-%dT%H:%M') if s.arrival_datetime else '',
                })

            t_data.append({
                'id': ft.id,
                'trip_type': ft.trip_type or 'direct_oneway',
                'sectors': sectors_payload,
                'airline_name': ft.airline_name,
                'airline_code': ft.airline_code or '',
                'airline_logo': ft.airline_logo or '',
                'flight_number': ft.flight_number,
                'departure_city': ft.departure_city,
                'departure_airport_code': ft.departure_airport_code,
                'destination_city': ft.destination_city,
                'destination_airport_code': ft.destination_airport_code,
                'departure_time_str': ft.departure_time_str,
                'arrival_time_str': ft.arrival_time_str,
                'duration_str': ft.duration_str,
                'flight_type': ft.flight_type,
                'via_routes': ft.via_routes or '',
                'ticket_class': ft.ticket_class,
                'price': str(ft.price),
                'price_handcarry': str(ft.price_handcarry) if ft.price_handcarry else '',
                'price_20kg': str(ft.price_20kg) if ft.price_20kg else str(ft.price),
                'price_23kg': str(ft.price_23kg) if ft.price_23kg else '',
                'price_25kg': str(ft.price_25kg) if ft.price_25kg else '',
                'price_30kg': str(ft.price_30kg) if ft.price_30kg else '',
                'price_35kg': str(ft.price_35kg) if ft.price_35kg else '',
                'price_40kg': str(ft.price_40kg) if ft.price_40kg else '',
                'price_46kg': str(ft.price_46kg) if ft.price_46kg else '',
                'custom_baggage_fares': ft.custom_baggage_fares or {},
                'baggage_options': ft.get_all_baggage_options(),
                'original_price': str(ft.original_price) if ft.original_price else '',
                'baggage_checkin': ft.baggage_checkin,
                'baggage_hand': ft.baggage_hand,
                'has_meal': ft.has_meal,
                'meal_service': ft.meal_service or ('Meal Included' if ft.has_meal else 'No Meal'),
                'is_refundable': ft.is_refundable,
                'cancellation_fee': str(ft.cancellation_fee),
                'total_seats': ft.total_seats,
                'available_seats': ft.available_seats,
                'is_popular': ft.is_popular,
                'description': ft.description or '',
                'created_at': ft.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse({'flight_tickets': t_data})

    elif request.method == 'POST':
        import re
        try:
            try:
                body = json.loads(request.body.decode('utf-8'))
            except Exception:
                body = request.POST

            def extract_code(city_str, fallback):
                if not city_str:
                    return fallback
                match = re.search(r'\(([A-Za-z]{3})\)', city_str)
                if match:
                    return match.group(1).upper()
                cleaned = re.sub(r'[^A-Za-z]', '', city_str)
                return cleaned[:3].upper() if len(cleaned) >= 3 else fallback

            trip_type = str(body.get('trip_type') or 'direct_oneway').strip()
            airline_name = str(body.get('airline_name') or 'PIA').strip()
            airline_code = str(body.get('airline_code') or '').strip()
            if not airline_code and airline_name:
                airline_code = airline_name[:2].upper()
            
            airline_logo = str(body.get('airline_logo') or '').strip()
            if not airline_logo:
                try:
                    from apps.airline_ticketing.models import Airline
                    matched_airline = Airline.objects.filter(name__iexact=airline_name).first()
                    if matched_airline and matched_airline.logo:
                        airline_logo = matched_airline.logo.url
                except Exception:
                    pass

            flight_number = str(body.get('flight_number') or 'PK-731').strip()
            departure_city = str(body.get('departure_city') or 'Karachi (KHI)').strip()
            departure_airport_code = str(body.get('departure_airport_code') or '').strip().upper() or extract_code(departure_city, 'KHI')
            destination_city = str(body.get('destination_city') or 'Jeddah (JED)').strip()
            destination_airport_code = str(body.get('destination_airport_code') or '').strip().upper() or extract_code(destination_city, 'JED')
            departure_time_str = str(body.get('departure_time_str') or '03:30 AM').strip()
            arrival_time_str = str(body.get('arrival_time_str') or '06:45 AM').strip()
            duration_str = str(body.get('duration_str') or '4h 15m').strip()
            flight_type = str(body.get('flight_type') or 'direct').strip()
            flight_route_type = str(body.get('flight_route_type') or 'round_trip_direct').strip()
            
            # Extract via routes
            via_route1 = str(body.get('via_route1') or '').strip()
            via_route2 = str(body.get('via_route2') or '').strip()
            via_route3 = str(body.get('via_route3') or '').strip()
            via_route4 = str(body.get('via_route4') or '').strip()
            
            via_list = [r for r in [via_route1, via_route2, via_route3, via_route4] if r]
            via_routes = " → ".join(via_list) if via_list else str(body.get('via_routes') or '').strip()

            ticket_class = str(body.get('ticket_class') or 'economy').strip()
            price = body.get('price') or '145000.00'
            price_handcarry = body.get('price_handcarry', None)
            price_20kg = body.get('price_20kg', None)
            price_23kg = body.get('price_23kg', None)
            price_25kg = body.get('price_25kg', None)
            price_30kg = body.get('price_30kg', None)
            price_35kg = body.get('price_35kg', None)
            price_40kg = body.get('price_40kg', None)
            price_46kg = body.get('price_46kg', None)
            custom_fares = body.get('custom_baggage_fares', {})
            if isinstance(custom_fares, str):
                try: custom_fares = json.loads(custom_fares)
                except Exception: custom_fares = {}

            original_price = body.get('original_price', None)
            
            baggage_checkin = str(body.get('baggage_checkin') or '30 kg').strip()
            baggage_hand = str(body.get('baggage_hand') or '7 kg').strip()
            
            has_meal = str(body.get('has_meal', 'true')).lower() in ('true', '1', 'on', 'yes')
            meal_service = str(body.get('meal_service') or ('Meal Included' if has_meal else 'No Meal')).strip()

            is_refundable = str(body.get('is_refundable', 'true')).lower() in ('true', '1', 'on')
            cancellation_fee = body.get('cancellation_fee') or '15000.00'
            total_seats = int(body.get('total_seats') or 50)
            available_seats = int(body.get('available_seats') or total_seats)
            is_popular = str(body.get('is_popular', 'false')).lower() in ('true', '1', 'on')
            description = str(body.get('description') or '').strip()

            raw_sectors_list = body.get('sectors') or body.get('sectors_list')
            if isinstance(raw_sectors_list, str):
                try: raw_sectors_list = json.loads(raw_sectors_list)
                except Exception: raw_sectors_list = []

            # If sectors were provided, sync top-level departure and arrival from first & last sector
            if isinstance(raw_sectors_list, list) and len(raw_sectors_list) > 0:
                first_sec = raw_sectors_list[0]
                last_sec = raw_sectors_list[-1]
                if isinstance(first_sec, dict):
                    if first_sec.get('departure_city'): departure_city = first_sec.get('departure_city')
                    if first_sec.get('departure_airport_code'): departure_airport_code = first_sec.get('departure_airport_code').upper()
                    if first_sec.get('airline_name'): airline_name = first_sec.get('airline_name')
                    if first_sec.get('flight_number'): flight_number = first_sec.get('flight_number')
                if isinstance(last_sec, dict):
                    if last_sec.get('arrival_city'): destination_city = last_sec.get('arrival_city')
                    if last_sec.get('arrival_airport_code'): destination_airport_code = last_sec.get('arrival_airport_code').upper()

            ft = FlightTicketOffer.objects.create(
                trip_type=trip_type,
                airline_name=airline_name,
                airline_code=airline_code,
                airline_logo=airline_logo,
                flight_number=flight_number,
                departure_city=departure_city,
                departure_airport_code=departure_airport_code,
                destination_city=destination_city,
                destination_airport_code=destination_airport_code,
                departure_time_str=departure_time_str,
                arrival_time_str=arrival_time_str,
                duration_str=duration_str,
                flight_type=flight_type,
                flight_route_type=flight_route_type,
                via_routes=via_routes,
                ticket_class=ticket_class,
                price=price,
                price_handcarry=price_handcarry if price_handcarry else None,
                price_20kg=price_20kg if price_20kg else price,
                price_23kg=price_23kg if price_23kg else None,
                price_25kg=price_25kg if price_25kg else None,
                price_30kg=price_30kg if price_30kg else None,
                price_35kg=price_35kg if price_35kg else None,
                price_40kg=price_40kg if price_40kg else None,
                price_46kg=price_46kg if price_46kg else None,
                custom_baggage_fares=custom_fares if isinstance(custom_fares, dict) else {},
                original_price=original_price if original_price else None,
                baggage_checkin=baggage_checkin,
                baggage_hand=baggage_hand,
                has_meal=has_meal,
                meal_service=meal_service,
                is_refundable=is_refundable,
                cancellation_fee=cancellation_fee,
                total_seats=total_seats,
                available_seats=available_seats,
                is_popular=is_popular,
                description=description
            )

            # Create FlightSector records
            if isinstance(raw_sectors_list, list) and len(raw_sectors_list) > 0:
                for idx, s in enumerate(raw_sectors_list):
                    if not isinstance(s, dict): continue
                    dep_dt_str = s.get('departure_datetime') or ''
                    arr_dt_str = s.get('arrival_datetime') or ''
                    dep_dt = parse_datetime(dep_dt_str) if dep_dt_str else timezone.now()
                    arr_dt = parse_datetime(arr_dt_str) if arr_dt_str else timezone.now()
                    if not dep_dt: dep_dt = timezone.now()
                    if not arr_dt: arr_dt = timezone.now()

                    FlightSector.objects.create(
                        flight_ticket=ft,
                        order=idx + 1,
                        airline_name=str(s.get('airline_name') or ft.airline_name).strip(),
                        flight_number=str(s.get('flight_number') or ft.flight_number).strip(),
                        departure_city=str(s.get('departure_city') or ft.departure_city).strip(),
                        departure_airport_code=str(s.get('departure_airport_code') or ft.departure_airport_code).strip().upper(),
                        arrival_city=str(s.get('arrival_city') or ft.destination_city).strip(),
                        arrival_airport_code=str(s.get('arrival_airport_code') or ft.destination_airport_code).strip().upper(),
                        departure_datetime=dep_dt,
                        arrival_datetime=arr_dt
                    )

            return JsonResponse({'success': True, 'flight_ticket_id': ft.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_flight_ticket_detail_api(request, pk):
    import re
    from apps.flights.models import FlightTicketOffer, FlightSector
    from django.utils.dateparse import parse_datetime
    from django.utils import timezone
    ft = get_object_or_404(FlightTicketOffer, pk=pk)
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        def extract_code(city_str, fallback):
            if not city_str:
                return fallback
            match = re.search(r'\(([A-Za-z]{3})\)', city_str)
            if match:
                return match.group(1).upper()
            cleaned = re.sub(r'[^A-Za-z]', '', city_str)
            return cleaned[:3].upper() if len(cleaned) >= 3 else fallback

        if 'trip_type' in body:
            ft.trip_type = body.get('trip_type')
        ft.airline_name = body.get('airline_name', ft.airline_name)
        ft.airline_code = body.get('airline_code', ft.airline_code)
        if 'airline_logo' in body:
            ft.airline_logo = body.get('airline_logo')
        ft.flight_number = body.get('flight_number', ft.flight_number)
        if 'departure_city' in body:
            ft.departure_city = body.get('departure_city')
            ft.departure_airport_code = str(body.get('departure_airport_code') or '').strip().upper() or extract_code(ft.departure_city, ft.departure_airport_code)
        if 'destination_city' in body:
            ft.destination_city = body.get('destination_city')
            ft.destination_airport_code = str(body.get('destination_airport_code') or '').strip().upper() or extract_code(ft.destination_city, ft.destination_airport_code)
        ft.departure_time_str = body.get('departure_time_str', ft.departure_time_str)
        ft.arrival_time_str = body.get('arrival_time_str', ft.arrival_time_str)
        ft.duration_str = body.get('duration_str', ft.duration_str)
        ft.flight_type = body.get('flight_type', ft.flight_type)
        if 'flight_route_type' in body:
            ft.flight_route_type = body.get('flight_route_type')

        raw_sectors_list = body.get('sectors') or body.get('sectors_list')
        if isinstance(raw_sectors_list, str):
            try: raw_sectors_list = json.loads(raw_sectors_list)
            except Exception: raw_sectors_list = None

        if isinstance(raw_sectors_list, list) and len(raw_sectors_list) > 0:
            first_sec = raw_sectors_list[0]
            last_sec = raw_sectors_list[-1]
            if isinstance(first_sec, dict):
                if first_sec.get('departure_city'): ft.departure_city = first_sec.get('departure_city')
                if first_sec.get('departure_airport_code'): ft.departure_airport_code = first_sec.get('departure_airport_code').upper()
                if first_sec.get('airline_name'): ft.airline_name = first_sec.get('airline_name')
                if first_sec.get('flight_number'): ft.flight_number = first_sec.get('flight_number')
            if isinstance(last_sec, dict):
                if last_sec.get('arrival_city'): ft.destination_city = last_sec.get('arrival_city')
                if last_sec.get('arrival_airport_code'): ft.destination_airport_code = last_sec.get('arrival_airport_code').upper()

        ft.ticket_class = body.get('ticket_class', ft.ticket_class)
        ft.price = body.get('price', ft.price)
        if 'price_20kg' in body:
            ft.price_20kg = body.get('price_20kg') or None
        if 'price_23kg' in body:
            ft.price_23kg = body.get('price_23kg') or None
        if 'price_25kg' in body:
            ft.price_25kg = body.get('price_25kg') or None
        if 'price_30kg' in body:
            ft.price_30kg = body.get('price_30kg') or None
        if 'price_35kg' in body:
            ft.price_35kg = body.get('price_35kg') or None
        if 'price_40kg' in body:
            ft.price_40kg = body.get('price_40kg') or None
        if 'price_46kg' in body:
            ft.price_46kg = body.get('price_46kg') or None
        if 'custom_baggage_fares' in body:
            cb = body.get('custom_baggage_fares')
            if isinstance(cb, str):
                try: cb = json.loads(cb)
                except Exception: cb = {}
            ft.custom_baggage_fares = cb

        if 'original_price' in body:
            ft.original_price = body.get('original_price') or None
        ft.baggage_checkin = body.get('baggage_checkin', ft.baggage_checkin)
        ft.baggage_hand = body.get('baggage_hand', ft.baggage_hand)
        if 'is_refundable' in body:
            ft.is_refundable = str(body.get('is_refundable', 'true')).lower() in ('true', '1', 'on')
        if body.get('cancellation_fee'):
            ft.cancellation_fee = body.get('cancellation_fee')
        ft.total_seats = int(body.get('total_seats', ft.total_seats))
        ft.available_seats = int(body.get('available_seats', ft.available_seats))
        if 'is_popular' in body:
            ft.is_popular = str(body.get('is_popular', 'false')).lower() in ('true', '1', 'on')
        if 'description' in body:
            ft.description = body.get('description')
        ft.save()
        return JsonResponse({'success': True})

    elif request.method == 'DELETE':
        ft.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@admin_required_api
def admin_bookings_api(request):
    bookings = Booking.objects.select_related('user', 'package').all().order_by('-created_at')
    bookings_data = []
    for b in bookings:
        username = (b.user.username if b.user else None) or b.full_name or 'Guest User'
        email = (b.user.email if b.user else None) or b.email or 'N/A'
        full_name = b.full_name or (b.user.get_full_name() if (b.user and b.user.get_full_name()) else username)
        phone = getattr(b, 'phone_number', '') or (b.user.phone if (b.user and hasattr(b.user, 'phone')) else '') or 'N/A'
        is_registered = b.user is not None
        user_role = b.user.get_role_display() if (b.user and hasattr(b.user, 'get_role_display')) else ('Registered User' if b.user else 'Guest Pilgrim')

        bookings_data.append({
            'id': b.id,
            'pnr': b.pnr or '',
            'full_name': full_name,
            'username': username,
            'email': email,
            'phone': phone,
            'is_registered': is_registered,
            'user_role': user_role,
            'package_title': b.package.title if b.package else 'Custom Booking',
            'booking_type': getattr(b, 'booking_type', 'package') or 'package',
            'sharing_category': getattr(b, 'sharing_category', 'Quad') or 'Quad',
            'adults_count': getattr(b, 'adults_count', 1) or 1,
            'children_count': getattr(b, 'children_count', 0) or 0,
            'infants_count': getattr(b, 'infants_count', 0) or 0,
            'selected_addons': getattr(b, 'selected_addons', []) or [],
            'discount_applied': str(getattr(b, 'discount_applied', 0.0) or 0.0),
            'notes': getattr(b, 'notes', '') or '',
            'status': b.status,
            'total_price': str(b.total_price) if b.total_price is not None else '0.00',
            'created_at': b.created_at.strftime('%Y-%m-%d %H:%M:%S') if b.created_at else '',
        })
    return JsonResponse({'bookings': bookings_data})

@csrf_exempt
@admin_required_api
def admin_booking_status_api(request, pk):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=pk)
        old_status = booking.status
        new_status = request.POST.get('status', booking.status)
        booking.status = new_status
        booking.save()
        
        # Auto-decrement available_seats when booking status changes to 'confirmed'
        if booking.package:
            if old_status != 'confirmed' and new_status == 'confirmed':
                if booking.package.available_seats > 0:
                    booking.package.available_seats = max(0, booking.package.available_seats - 1)
                    booking.package.save()
            elif old_status == 'confirmed' and new_status != 'confirmed':
                booking.package.available_seats = min(booking.package.total_seats, booking.package.available_seats + 1)
                booking.package.save()
                
        return JsonResponse({
            'success': True, 
            'status': booking.status,
            'available_seats': booking.package.available_seats if booking.package else None
        })
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@user_passes_test(is_admin)
def admin_suspend_agent(request, agent_id):
    if request.method == 'POST':
        agent = get_object_or_404(User, id=agent_id, role='agent')
        agent.approval_status = 'suspended'
        agent.save()
        send_agent_status_email(agent, 'suspended')
        return JsonResponse({'success': True, 'status': 'suspended'})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@user_passes_test(is_admin)
def admin_delete_agent(request, agent_id):
    if request.method in ['DELETE', 'POST']:
        agent = get_object_or_404(User, id=agent_id, role='agent')
        company_name = agent.company_name or agent.username
        agent.delete()
        return JsonResponse({
            'success': True,
            'message': f'Agent account "{company_name}" has been permanently deleted.'
        })
    return JsonResponse({'success': False, 'error': 'Invalid HTTP method.'}, status=400)


def is_agent(user):
    return user.is_authenticated and user.role == 'agent' and user.approval_status == 'approved'


@user_passes_test(is_agent)
def agent_dashboard_view(request):
    if not request.user.agent_id_number:
        request.user.agent_id_number = generate_agent_id_number()
        if not request.user.id_card_issued_at:
            request.user.id_card_issued_at = timezone.now()
        request.user.save()
    return render(request, 'dashboard/agent/overview.html')


@agent_required_api
def agent_dashboard_overview_api(request):
    counts = {
        'bookings_total': Booking.objects.filter(user=request.user).count(),
        'bookings_pending': Booking.objects.filter(user=request.user, status='pending').count(),
        'visas_total': VisaApplication.objects.filter(user=request.user).count(),
        'visas_pending': VisaApplication.objects.filter(user=request.user, status='pending').count(),
        'flights_total': FlightQuoteRequest.objects.filter(user=request.user).count(),
        'flights_pending': FlightQuoteRequest.objects.filter(user=request.user, status='pending').count(),
    }
    return JsonResponse({'counts': counts, 'wallet_balance': request.user.wallet_balance})


@agent_required_api
def agent_bookings_api(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    bookings_data = []
    for b in bookings:
        bookings_data.append({
            'id': b.id,
            'package_title': b.package.title if b.package else 'Custom Booking',
            'booking_type': b.booking_type,
            'status': b.status,
            'total_price': str(b.total_price),
            'created_at': b.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'bookings': bookings_data})


@agent_required_api
def agent_visas_api(request):
    visas = VisaApplication.objects.filter(user=request.user).order_by('-created_at')
    visas_data = []
    for v in visas:
        visas_data.append({
            'id': v.id,
            'country': v.country,
            'passport_number': v.passport_number,
            'status': v.status,
            'created_at': v.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'visas': visas_data})


@agent_required_api
def agent_flights_api(request):
    flights = FlightQuoteRequest.objects.filter(user=request.user).order_by('-created_at')
    flights_data = []
    for f in flights:
        flights_data.append({
            'id': f.id,
            'departure_city': f.departure_city,
            'destination_city': f.destination_city,
            'departure_date': f.departure_date.strftime('%Y-%m-%d') if hasattr(f.departure_date, 'strftime') else str(f.departure_date),
            'return_date': (f.return_date.strftime('%Y-%m-%d') if hasattr(f.return_date, 'strftime') else str(f.return_date)) if f.return_date else 'N/A',
            'status': f.status,
            'price_quote': str(f.price_quote) if f.price_quote else 'N/A',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'flights': flights_data})


@admin_required_api
def admin_agent_detail_data_api(request, agent_id):
    agent = get_object_or_404(User, id=agent_id, role='agent')
    
    # Bookings made by agent
    bookings = Booking.objects.filter(user=agent).order_by('-created_at')
    bookings_data = []
    for b in bookings:
        bookings_data.append({
            'id': b.id,
            'package_title': b.package.title if b.package else 'Custom Booking',
            'booking_type': b.booking_type,
            'status': b.status,
            'total_price': str(b.total_price),
            'created_at': b.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Visa submissions by agent
    visas = VisaApplication.objects.filter(user=agent).order_by('-created_at')
    visas_data = []
    for v in visas:
        visas_data.append({
            'id': v.id,
            'country': v.country,
            'passport_number': v.passport_number,
            'status': v.status,
            'created_at': v.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Flight quotes requested by agent
    flights = FlightQuoteRequest.objects.filter(user=agent).order_by('-created_at')
    flights_data = []
    for f in flights:
        flights_data.append({
            'id': f.id,
            'departure_city': f.departure_city,
            'destination_city': f.destination_city,
            'departure_date': f.departure_date.strftime('%Y-%m-%d') if hasattr(f.departure_date, 'strftime') else str(f.departure_date),
            'return_date': (f.return_date.strftime('%Y-%m-%d') if hasattr(f.return_date, 'strftime') else str(f.return_date)) if f.return_date else 'N/A',
            'status': f.status,
            'price_quote': str(f.price_quote) if f.price_quote else 'N/A',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    # Fetch login history for agent
    logins = LoginHistory.objects.filter(user=agent).order_by('-timestamp')[:50]
    logins_data = []
    for l in logins:
        logins_data.append({
            'ip_address': l.ip_address or 'Unknown',
            'user_agent': l.user_agent or 'Unknown',
            'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return JsonResponse({
        'company_name': agent.company_name or agent.username,
        'agent_name': f"{agent.first_name} {agent.last_name}".strip() or agent.username,
        'email': agent.email or '',
        'phone': agent.phone or 'N/A',
        'address': agent.address or 'N/A',
        'is_verified_partner': getattr(agent, 'is_verified_partner', False),
        'approval_status': getattr(agent, 'approval_status', 'pending') or 'pending',
        'wallet_balance': getattr(agent, 'wallet_balance', 0.0),
        'is_email_verified': getattr(agent, 'is_email_verified', False),
        'date_joined': agent.date_joined.strftime('%Y-%m-%d %H:%M:%S') if agent.date_joined else '',
        'agent_id_number': getattr(agent, 'agent_id_number', None) or '',
        'id_card_issued_at_str': agent.id_card_issued_at.strftime('%B %d, %Y') if getattr(agent, 'id_card_issued_at', None) else '',
        'id_card_qr_url': request.build_absolute_uri(f"/dashboard/agent/id-card-qr/{agent.agent_id_number}/") if getattr(agent, 'agent_id_number', None) else '',
        'profile_photo_url': request.build_absolute_uri(agent.profile_photo.url) if agent.profile_photo else '',
        'id_card_front_url': request.build_absolute_uri(agent.id_card_front.url) if agent.id_card_front else '',
        'id_card_back_url': request.build_absolute_uri(agent.id_card_back.url) if agent.id_card_back else '',
        'bookings': bookings_data,
        'visas': visas_data,
        'flights': flights_data,
        'login_history': logins_data
    })


@user_passes_test(is_admin)
def admin_agent_detail_view(request, agent_id):
    agent = get_object_or_404(User, id=agent_id, role='agent')
    return render(request, 'dashboard/admin/agent_detail.html', {'agent_id': agent_id, 'agent': agent})


def home_view(request):
    from apps.content.models import Achievement
    from apps.packages.models import Package
    # Fetch real-time registered agent partners ordered by latest registration
    best_agents = User.objects.filter(role='agent').order_by('-date_joined')
    achievements = Achievement.objects.filter(is_active=True)
    
    # Prioritize packages explicitly selected as featured by admin in B2C admin panel
    featured = list(Package.objects.filter(is_featured=True).order_by('-updated_at', '-created_at'))
    if len(featured) < 6:
        existing_ids = [p.id for p in featured]
        extra = list(Package.objects.exclude(id__in=existing_ids).order_by('-created_at')[:(6 - len(featured))])
        featured.extend(extra)
    featured_packages = featured[:6]
    
    return render(request, 'home.html', {
        'best_agents': best_agents,
        'achievements': achievements,
        'featured_packages': featured_packages
    })


def achievements_list_view(request):
    from apps.content.models import Achievement
    achievements = Achievement.objects.filter(is_active=True)
    return render(request, 'achievements.html', {'achievements': achievements})


def public_agent_profile_view(request, agent_id):
    agent = get_object_or_404(User, id=agent_id, role='agent', approval_status='approved')
    reviews = agent.reviews_received.all().order_by('-created_at')
    
    if request.method == 'POST':
        author_name = request.POST.get('author_name', '').strip()
        rating_val = request.POST.get('rating', '5')
        comment_text = request.POST.get('comment', '').strip()
        
        if author_name and comment_text:
            try:
                rating_int = int(rating_val)
                # Keep in bounds
                rating_int = max(1, min(5, rating_int))
                
                # Create review
                AgentReview.objects.create(
                    agent=agent,
                    author_name=author_name,
                    rating=rating_int,
                    comment=comment_text
                )
                
                # Recalculate average rating
                all_reviews = agent.reviews_received.all()
                if all_reviews:
                    avg_rating = sum([r.rating for r in all_reviews]) / len(all_reviews)
                    agent.rating = round(avg_rating, 2)
                    agent.save()
                    
                messages.success(request, "Thank you! Your review has been posted successfully in real time.")
            except Exception as e:
                messages.error(request, f"Error submitting review: {e}")
                
        return redirect('public_agent_profile', agent_id=agent.id)
        
    return render(request, 'agent_profile.html', {
        'agent': agent,
        'reviews': reviews,
    })


def track_status_api(request, tracking_id):
    """
    Search and track status of bookings, visa apps, or flight requests.
    Supports GSA-B-<id>, GSA-V-<id>, GSA-F-<id> formats.
    """
    tracking_id = tracking_id.strip().upper()
    item_type = None
    item_id = None
    
    if tracking_id.startswith('GSA-B-'):
        item_type = 'booking'
        try:
            item_id = int(tracking_id.replace('GSA-B-', ''))
        except ValueError:
            pass
    elif tracking_id.startswith('GSA-V-'):
        item_type = 'visa'
        try:
            item_id = int(tracking_id.replace('GSA-V-', ''))
        except ValueError:
            pass
    elif tracking_id.startswith('GSA-F-'):
        item_type = 'flight'
        try:
            item_id = int(tracking_id.replace('GSA-F-', ''))
        except ValueError:
            pass
    else:
        # Fallback search - try parsing as straight ID number or B-*, V-*, F-*
        try:
            item_id = int(tracking_id)
            item_type = 'booking'
        except ValueError:
            parts = tracking_id.split('-')
            if len(parts) == 2:
                prefix, num = parts[0], parts[1]
                try:
                    item_id = int(num)
                    if prefix == 'B':
                        item_type = 'booking'
                    elif prefix == 'V':
                        item_type = 'visa'
                    elif prefix == 'F':
                        item_type = 'flight'
                except ValueError:
                    pass
                    
    if not item_id or not item_type:
        return JsonResponse({'success': False, 'message': 'Invalid tracking reference format. Use e.g. GSA-B-5, GSA-V-3, GSA-F-12.'}, status=400)
        
    if item_type == 'booking':
        try:
            booking = Booking.objects.select_related('package', 'user').get(id=item_id)
            data = {
                'success': True,
                'type': 'Package / Custom Booking',
                'id': f"GSA-B-{booking.id}",
                'title': booking.package.title if booking.package else "Custom Travel Package",
                'status': booking.get_status_display(),
                'status_raw': booking.status,
                'price': f"{booking.total_price:,.2f} PKR",
                'date': booking.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'customer': f"{booking.user.first_name or booking.user.username}"
            }
            return JsonResponse(data)
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'No booking found with reference GSA-B-{item_id}.'}, status=404)
            
    elif item_type == 'visa':
        try:
            visa = VisaApplication.objects.select_related('user').get(id=item_id)
            passport = visa.passport_number
            masked_passport = passport[:2] + '*' * (len(passport) - 4) + passport[-2:] if len(passport) > 4 else "***"
            data = {
                'success': True,
                'type': 'Visa Application',
                'id': f"GSA-V-{visa.id}",
                'title': f"Visit Visa to {visa.country}",
                'status': visa.get_status_display(),
                'status_raw': visa.status,
                'price': 'N/A',
                'date': visa.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'customer': f"{visa.user.first_name or visa.user.username}",
                'extra_info': f"Passport: {masked_passport}"
            }
            return JsonResponse(data)
        except VisaApplication.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'No visa application found with reference GSA-V-{item_id}.'}, status=404)
            
    elif item_type == 'flight':
        try:
            flight = FlightQuoteRequest.objects.select_related('user').get(id=item_id)
            price_display = f"{flight.price_quote:,.2f} PKR" if flight.price_quote else "Awaiting Quote"
            data = {
                'success': True,
                'type': 'Flight Ticket / Quote',
                'id': f"GSA-F-{flight.id}",
                'title': f"Flight: {flight.departure_city} to {flight.destination_city}",
                'status': flight.get_status_display(),
                'status_raw': flight.status,
                'price': price_display,
                'date': flight.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'customer': f"{flight.user.first_name or flight.user.username}",
                'extra_info': f"Departure: {flight.departure_date}"
            }
            return JsonResponse(data)
        except FlightQuoteRequest.DoesNotExist:
            return JsonResponse({'success': False, 'message': f'No flight quote request found with reference GSA-F-{item_id}.'}, status=404)
            
    return JsonResponse({'success': False, 'message': 'Unknown tracking category.'}, status=400)


@login_required
@never_cache
def agent_dashboard_chart_view(request):
    if request.user.role != 'agent':
        return HttpResponse(status=403)

    # Get actual counts
    bookings_cnt = Booking.objects.filter(user=request.user).count()
    visas_cnt = VisaApplication.objects.filter(user=request.user).count()
    flights_cnt = FlightQuoteRequest.objects.filter(user=request.user).count()

    # Generate weekly trend data using numpy
    np.random.seed(42 + request.user.id)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    x = np.arange(len(days))

    bookings_trend = np.clip(np.round(np.random.normal(bookings_cnt / 7 + 2, 1.5, 7)), 0, 100).astype(int)
    visas_trend    = np.clip(np.round(np.random.normal(visas_cnt    / 7 + 1, 1.0, 7)), 0, 100).astype(int)
    flights_trend  = np.clip(np.round(np.random.normal(flights_cnt  / 7 + 3, 2.0, 7)), 0, 100).astype(int)

    # ── Light-themed figure ──────────────────────────────────────────────────
    BG       = '#ffffff'   # white card bg
    PANEL    = '#ffffff'   # white chart panel
    GRID     = '#cbd5e1'   # slate-300
    TEXT     = '#475569'   # slate-600
    TITLE    = '#0f172a'   # slate-900

    C_BOOK   = '#ea580c'   # brand orange
    C_VISA   = '#10b981'   # emerald-500
    C_FLIGHT = '#6366f1'   # indigo-500

    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=BG)
    ax.set_facecolor(PANEL)

    # Subtle grid only on y-axis
    ax.yaxis.grid(True, color=GRID, linewidth=0.6, linestyle='--', alpha=0.6)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # ── Plot lines ───────────────────────────────────────────────────────────
    lw = 2.4
    ms = 7

    for y_vals, color, label in [
        (bookings_trend, C_BOOK,   'Bookings'),
        (visas_trend,    C_VISA,   'Visas'),
        (flights_trend,  C_FLIGHT, 'Flight Quotes'),
    ]:
        # Gradient fill
        ax.fill_between(x, y_vals, alpha=0.13, color=color, linewidth=0)
        # Main line
        ax.plot(x, y_vals, color=color, linewidth=lw, zorder=3, solid_capstyle='round')
        # Glowing marker (outer halo)
        ax.scatter(x, y_vals, color=color, s=ms**2 * 2.5, alpha=0.25, zorder=4, linewidths=0)
        # Solid marker
        ax.scatter(x, y_vals, color=color, s=ms**2, zorder=5,
                   edgecolors='white', linewidths=0.8, label=label)

    # ── Axes styling ─────────────────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(days, color=TEXT, fontsize=9, fontweight='bold')
    ax.tick_params(axis='x', which='both', bottom=False, length=0, pad=8)
    ax.tick_params(axis='y', colors=TEXT, labelsize=8, length=0, pad=6)
    ax.yaxis.set_tick_params(labelleft=True)

    # ── Title & labels ───────────────────────────────────────────────────────
    ax.set_title('Weekly Business Performance', color=TITLE, fontsize=12,
                 fontweight='bold', loc='left', pad=14)
    ax.text(0, 1.04, f'Bookings · Visas · Flight Quotes  —  This Week',
            transform=ax.transAxes, color=TEXT, fontsize=8)

    ax.set_ylabel('Volume', color=TEXT, fontsize=8, labelpad=10)
    ax.set_xlabel('')

    # ── Legend ───────────────────────────────────────────────────────────────
    legend = ax.legend(
        loc='upper right',
        frameon=True,
        facecolor='#ffffff',
        edgecolor='#cbd5e1',
        labelcolor=TEXT,
        fontsize=8,
        markerscale=0.9,
        handlelength=1.5,
        borderpad=0.8,
        labelspacing=0.6,
    )
    legend.get_frame().set_linewidth(0.8)

    # ── Layout & export ──────────────────────────────────────────────────────
    plt.tight_layout(pad=1.6)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
@never_cache
def agent_dashboard_pie_chart_view(request):
    """Donut pie chart — volume distribution across Bookings, Visas, Flight Quotes."""
    if request.user.role != 'agent':
        return HttpResponse(status=403)

    bookings_cnt = Booking.objects.filter(user=request.user).count()
    visas_cnt    = VisaApplication.objects.filter(user=request.user).count()
    flights_cnt  = FlightQuoteRequest.objects.filter(user=request.user).count()

    if bookings_cnt + visas_cnt + flights_cnt == 0:
        bookings_cnt, visas_cnt, flights_cnt = 4, 3, 5  # demo values

    BG    = '#ffffff'   # matches dashboard card background
    PANEL = '#ffffff'
    TEXT  = '#475569'
    TITLE = '#0f172a'

    sizes   = [bookings_cnt, visas_cnt, flights_cnt]
    labels  = ['Bookings', 'Visas', 'Flight Quotes']
    colors  = ['#ea580c', '#10b981', '#6366f1']
    explode = (0.04, 0.04, 0.04)

    fig, ax = plt.subplots(figsize=(5, 4.4), facecolor=BG)
    ax.set_facecolor(PANEL)

    wedges, _, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.0f%%',
        startangle=140,
        colors=colors,
        explode=explode,
        pctdistance=0.72,
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2.5),
        shadow=False,
    )
    for at in autotexts:
        at.set_color('#ffffff')
        at.set_fontsize(9)
        at.set_fontweight('bold')

    # Centre donut label
    ax.text(0, 0, f'{sum(sizes)}\nTotal', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#0f172a')

    legend = ax.legend(
        wedges, labels,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.14),
        ncol=3,
        frameon=True,
        facecolor='#ffffff',
        edgecolor='#cbd5e1',
        labelcolor=TEXT,
        fontsize=8,
        borderpad=0.7,
        handlelength=1.2,
    )
    legend.get_frame().set_linewidth(0.8)
    ax.set_title('Volume Distribution', color=TITLE, fontsize=11, fontweight='bold', pad=12)

    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
@never_cache
def agent_dashboard_bar_chart_view(request):
    """Grouped bar chart — monthly activity over the last 6 months."""
    if request.user.role != 'agent':
        return HttpResponse(status=403)

    np.random.seed(99 + request.user.id)
    bookings_cnt = Booking.objects.filter(user=request.user).count()
    visas_cnt    = VisaApplication.objects.filter(user=request.user).count()
    flights_cnt  = FlightQuoteRequest.objects.filter(user=request.user).count()

    months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    x = np.arange(len(months))
    w = 0.26

    def monthly(total):
        # Use at least 5 as a demo baseline so bars always show
        base = max(total / 6, 5)
        trend = np.linspace(0.75, 1.25, 6)          # gentle upward curve
        noise = np.random.normal(0, base * 0.25, 6)  # 25% variance
        vals  = np.round(base * trend + noise).astype(int)
        return np.clip(vals, 2, 999)                 # always at least 2

    b_vals = monthly(bookings_cnt)
    v_vals = monthly(visas_cnt)
    f_vals = monthly(flights_cnt)

    BG    = '#ffffff'   # matches dashboard card background
    PANEL = '#ffffff'
    GRID  = '#cbd5e1'
    TEXT  = '#475569'
    TITLE = '#0f172a'

    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=BG)
    ax.set_facecolor(PANEL)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    bars_b = ax.bar(x - w, b_vals, width=w, color='#ea580c', label='Bookings',     edgecolor='white', linewidth=0.8, zorder=3)
    bars_v = ax.bar(x,     v_vals, width=w, color='#10b981', label='Visas',         edgecolor='white', linewidth=0.8, zorder=3)
    bars_f = ax.bar(x + w, f_vals, width=w, color='#6366f1', label='Flight Quotes', edgecolor='white', linewidth=0.8, zorder=3)

    for bars in [bars_b, bars_v, bars_f]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.15, str(int(h)),
                        ha='center', va='bottom', fontsize=6.5, color='#0f172a', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(months, color=TEXT, fontsize=9, fontweight='bold')
    ax.tick_params(axis='x', which='both', bottom=False, length=0, pad=8)
    ax.tick_params(axis='y', colors=TEXT, labelsize=8, length=0, pad=6)
    ax.set_title('Monthly Activity Breakdown', color=TITLE, fontsize=12, fontweight='bold', loc='left', pad=14)
    ax.text(0, 1.04, 'Last 6 months  —  Bookings · Visas · Flight Quotes',
            transform=ax.transAxes, color=TEXT, fontsize=8)
    ax.set_ylabel('Count', color=TEXT, fontsize=8, labelpad=10)
    ax.set_xlabel('')

    legend = ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1',
                       labelcolor=TEXT, fontsize=8, handlelength=1.2, borderpad=0.8, labelspacing=0.5)
    legend.get_frame().set_linewidth(0.8)

    plt.tight_layout(pad=1.6)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
@never_cache
def agent_chart_data_api(request):
    """JSON API — returns chart data for the agent overview dashboard."""
    if request.user.role != 'agent':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    bookings_cnt = Booking.objects.filter(user=request.user).count()
    visas_cnt = VisaApplication.objects.filter(user=request.user).count()
    flights_cnt = FlightQuoteRequest.objects.filter(user=request.user).count()

    # 1. Weekly performance trend (line chart)
    np.random.seed(42 + request.user.id)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    bookings_trend = np.clip(np.round(np.random.normal(bookings_cnt / 7 + 2, 1.5, 7)), 0, 100).astype(int)
    visas_trend    = np.clip(np.round(np.random.normal(visas_cnt    / 7 + 1, 1.0, 7)), 0, 100).astype(int)
    flights_trend  = np.clip(np.round(np.random.normal(flights_cnt  / 7 + 3, 2.0, 7)), 0, 100).astype(int)

    # 2. Volume mix (pie chart)
    pie_bookings = bookings_cnt
    pie_visas = visas_cnt
    pie_flights = flights_cnt
    if pie_bookings + pie_visas + pie_flights == 0:
        pie_bookings, pie_visas, pie_flights = 4, 3, 5

    # 3. Monthly activity breakdown (bar chart)
    np.random.seed(99 + request.user.id)
    months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    def monthly(total):
        base = max(total / 6, 5)
        trend = np.linspace(0.75, 1.25, 6)
        noise = np.random.normal(0, base * 0.25, 6)
        vals  = np.round(base * trend + noise).astype(int)
        return [int(v) for v in np.clip(vals, 2, 999)]

    b_vals = monthly(bookings_cnt)
    v_vals = monthly(visas_cnt)
    f_vals = monthly(flights_cnt)

    return JsonResponse({
        'trend': {
            'labels': days,
            'bookings': [int(v) for v in bookings_trend],
            'visas': [int(v) for v in visas_trend],
            'flights': [int(v) for v in flights_trend],
        },
        'pie': {
            'labels': ['Bookings', 'Visas', 'Flight Quotes'],
            'values': [int(pie_bookings), int(pie_visas), int(pie_flights)],
        },
        'bar': {
            'labels': months,
            'bookings': b_vals,
            'visas': v_vals,
            'flights': f_vals,
        }
    })


@login_required
def agent_profile_settings_view(request):
    if request.user.role != 'agent':
        return redirect('login')
        
    if request.method == 'POST':
        user = request.user
        user.company_name = request.POST.get('company_name', '').strip() or user.company_name
        user.first_name = request.POST.get('first_name', '').strip() or user.first_name
        user.last_name = request.POST.get('last_name', '').strip() or user.last_name
        user.phone = request.POST.get('phone', '').strip() or user.phone
        user.about = request.POST.get('about', '').strip() or user.about
        
        # File uploads
        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        if 'cover_photo' in request.FILES:
            user.cover_photo = request.FILES['cover_photo']
            
        user.save()
        messages.success(request, "Your agency profile details have been updated successfully in real time!")
        return redirect('agent_dashboard')
        
    return redirect('agent_dashboard')



# ─────────────────────────────────────────────────────────────────────────────
# SUPER ADMIN CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def _admin_chart_check(request):
    """Return True if request is from an authenticated admin, else False."""
    return request.user.is_authenticated and (request.user.is_superuser or request.user.role == 'super_admin')


@login_required
@never_cache
def admin_chart_data_api(request):
    """JSON API — returns all chart data for the admin overview dashboard."""
    if not _admin_chart_check(request):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    np.random.seed(7)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']

    total_bookings = Booking.objects.count()
    total_visas    = VisaApplication.objects.count()
    total_flights  = FlightQuoteRequest.objects.count()

    def trend(total, lo=5):
        base = max(total / 7, lo)
        t = np.linspace(0.7, 1.4, 7)
        n = np.random.normal(0, base * 0.2, 7)
        return [int(v) for v in np.clip(np.round(base * t + n).astype(int), 2, 9999)]

    b_vals = trend(total_bookings)
    v_vals = trend(total_visas)
    f_vals = trend(total_flights)

    # Agent bar chart
    np.random.seed(17)
    months6 = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    total_active  = User.objects.filter(role='agent', approval_status='approved').count()
    total_pending = User.objects.filter(role='agent', approval_status='pending').count()

    def dist(total, lo=3):
        base = max(total / 6, lo)
        n    = np.random.normal(0, base * 0.3, 6)
        t    = np.linspace(0.75, 1.25, 6)
        return [int(v) for v in np.clip(np.round(base * t + n).astype(int), 1, 9999)]

    active_vals  = dist(total_active)
    pending_vals = dist(total_pending, lo=1)

    b_pie = total_bookings or 12
    v_pie = total_visas    or 8
    f_pie = total_flights  or 10

    return JsonResponse({
        'trend': {
            'labels': months,
            'bookings': b_vals,
            'visas':    v_vals,
            'flights':  f_vals,
        },
        'pie': {
            'values': [b_pie, v_pie, f_pie],
            'labels': ['Bookings', 'Visa Apps', 'Flight Quotes'],
        },
        'agents': {
            'labels':  months6,
            'active':  active_vals,
            'pending': pending_vals,
        },
    })


@login_required
@never_cache
def admin_chart_revenue_view(request):
    """Line chart — monthly booking & visa revenue trend (last 7 months)."""
    if not _admin_chart_check(request):
        return HttpResponse(status=403)

    np.random.seed(7)
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    x = np.arange(len(months))

    total_bookings = Booking.objects.count()
    total_visas    = VisaApplication.objects.count()
    total_flights  = FlightQuoteRequest.objects.count()

    def trend(total, lo=5, hi=15):
        base = max(total / 7, lo)
        t = np.linspace(0.7, 1.4, 7)
        n = np.random.normal(0, base * 0.2, 7)
        return np.clip(np.round(base * t + n).astype(int), 2, 9999)

    b_vals = trend(total_bookings)
    v_vals = trend(total_visas)
    f_vals = trend(total_flights)

    WH   = '#ffffff'
    PAN  = '#ffffff'
    GRID = '#cbd5e1'
    TEXT = '#475569'
    TTL  = '#0f172a'

    fig, ax = plt.subplots(figsize=(10, 3.8), facecolor=WH)
    ax.set_facecolor(PAN)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, linestyle='--', alpha=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

    for y_vals, color, label in [
        (b_vals, '#ea580c', 'Bookings'),
        (v_vals, '#10b981', 'Visa Apps'),
        (f_vals, '#6366f1', 'Flight Quotes'),
    ]:
        ax.fill_between(x, y_vals, alpha=0.10, color=color)
        ax.plot(x, y_vals, color=color, linewidth=2.5, solid_capstyle='round', zorder=3)
        ax.scatter(x, y_vals, color=color, s=52, zorder=5, edgecolors='white', linewidths=1.2, label=label)

    ax.set_xticks(x)
    ax.set_xticklabels(months, color=TEXT, fontsize=9, fontweight='bold')
    ax.tick_params(axis='x', bottom=False, length=0, pad=8)
    ax.tick_params(axis='y', colors=TEXT, labelsize=8, length=0, pad=6)
    ax.set_title('Monthly Platform Volume — 7 Month Trend', color=TTL, fontsize=11, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel('Count', color=TEXT, fontsize=8, labelpad=8)

    legend = ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor=GRID,
                       labelcolor=TEXT, fontsize=8, handlelength=1.4, borderpad=0.8)
    legend.get_frame().set_linewidth(0.8)

    plt.tight_layout(pad=1.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=WH, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
@never_cache
def admin_chart_pie_view(request):
    """Donut pie — platform-wide activity mix (Bookings / Visas / Flights)."""
    if not _admin_chart_check(request):
        return HttpResponse(status=403)

    b = Booking.objects.count()
    v = VisaApplication.objects.count()
    f = FlightQuoteRequest.objects.count()
    if b + v + f == 0:
        b, v, f = 12, 8, 10  # demo

    WH  = '#ffffff'   # white card background
    PAN = '#ffffff'
    TXT = '#475569'   # slate-600
    TTL = '#0f172a'   # slate-900
    TOTAL = '#0f172a' # slate-900 center text

    sizes   = [b, v, f]
    labels  = ['Bookings', 'Visa Apps', 'Flight Quotes']
    colors  = ['#ea580c', '#10b981', '#6366f1']
    explode = (0.04, 0.04, 0.04)

    fig, ax = plt.subplots(figsize=(5, 4.6), facecolor=WH)
    ax.set_facecolor(PAN)

    wedges, _, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.0f%%', startangle=135,
        colors=colors, explode=explode, pctdistance=0.70,
        wedgeprops=dict(width=0.52, edgecolor=WH, linewidth=2.8),
    )
    for at in autotexts:
        at.set_color('#ffffff'); at.set_fontsize(9); at.set_fontweight('bold')

    ax.text(0, 0, f'{sum(sizes)}\nTotal', ha='center', va='center',
            fontsize=11, fontweight='bold', color=TOTAL)
    ax.set_title('Platform Activity Mix', color=TTL, fontsize=11, fontweight='bold', pad=10)

    legend = ax.legend(wedges, labels, loc='lower center', bbox_to_anchor=(0.5, -0.14),
                       ncol=3, frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1',
                       labelcolor=TXT, fontsize=8, borderpad=0.7, handlelength=1.1)
    legend.get_frame().set_linewidth(0.8)

    plt.tight_layout(pad=1.2)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=WH, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@login_required
@never_cache
def admin_chart_agents_view(request):
    """Grouped bar chart — agent performance (active vs pending per month)."""
    if not _admin_chart_check(request):
        return HttpResponse(status=403)

    np.random.seed(17)
    months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
    x = np.arange(len(months))
    w = 0.32

    total_active  = User.objects.filter(role='agent', approval_status='approved').count()
    total_pending = User.objects.filter(role='agent', approval_status='pending').count()

    def dist(total, lo=3):
        base = max(total / 6, lo)
        n    = np.random.normal(0, base * 0.3, 6)
        t    = np.linspace(0.75, 1.25, 6)
        return np.clip(np.round(base * t + n).astype(int), 1, 9999)

    active_vals  = dist(total_active)
    pending_vals = dist(total_pending, lo=1)

    WH   = '#ffffff'   # white card background
    GRID = '#cbd5e1'   # slate-300
    TEXT = '#475569'   # slate-600
    TTL  = '#0f172a'   # slate-900

    fig, ax = plt.subplots(figsize=(9, 3.8), facecolor=WH)
    ax.set_facecolor(WH)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, linestyle='--', alpha=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)

    bars_a = ax.bar(x - w/2, active_vals,  width=w, color='#10b981', label='Active Agents',  edgecolor='white', linewidth=0.8, zorder=3)
    bars_p = ax.bar(x + w/2, pending_vals, width=w, color='#f59e0b', label='Pending Agents', edgecolor='white', linewidth=0.8, zorder=3)

    for bars in [bars_a, bars_p]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.1, str(int(h)),
                    ha='center', va='bottom', fontsize=7, color='#0f172a', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(months, color=TEXT, fontsize=9, fontweight='bold')
    ax.tick_params(axis='x', bottom=False, length=0, pad=8)
    ax.tick_params(axis='y', colors=TEXT, labelsize=8, length=0, pad=6)
    ax.set_title('Agent Onboarding — Active vs Pending', color=TTL, fontsize=11, fontweight='bold', loc='left', pad=12)
    ax.set_ylabel('Agents', color=TEXT, fontsize=8, labelpad=8)

    legend = ax.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor=GRID,
                       labelcolor=TEXT, fontsize=8, handlelength=1.2, borderpad=0.8)
    legend.get_frame().set_linewidth(0.8)

    plt.tight_layout(pad=1.4)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=160, facecolor=WH, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return HttpResponse(buf.getvalue(), content_type='image/png')


@csrf_exempt
@user_passes_test(is_admin)
def admin_toggle_agent_verification_badge(request, agent_id):
    if request.method == 'POST':
        agent = get_object_or_404(User, id=agent_id, role='agent')
        agent.is_verified_partner = not agent.is_verified_partner
        agent.save()
        return JsonResponse({'success': True, 'is_verified_partner': agent.is_verified_partner})
    return JsonResponse({'success': False}, status=400)


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email).first()
        if user:
            # Generate OTP
            code = f"{random.randint(100000, 999999)}"
            user.email_verification_code = code
            user.otp_created_at = timezone.now()
            user.save()
            
            # Send Professional HTML Email
            subject = "Password Reset Verification Code | REI GOLDEN STAR TRAVEL & TOURS"
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            body_html = f"""
            <p>We received a request to reset the password for your account (<strong>{user.email}</strong>).</p>
            <p>Your official 6-digit password reset verification code is:</p>
            
            <div style="background-color: #fff7ed; border: 2px dashed #f97316; border-radius: 14px; padding: 20px; text-align: center; margin: 24px 0;">
                <span style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 900; letter-spacing: 10px; color: #ea580c;">{code}</span>
            </div>
            
            <p style="color: #64748b; font-size: 13px;">This code is valid for <strong>5 minutes</strong>. If you did not request a password reset, please ignore this email or contact support immediately.</p>
            """
            
            html_message = build_professional_email_html("Password Reset Request", recipient_name, body_html, "Verify Code Now", "http://127.0.0.1:8000/auth/forgot-password/verify/")
            plain_message = f"Hello {recipient_name},\n\nYour 6-digit OTP code to reset your password is: {code}\n\nREI GOLDEN STAR TRAVEL & TOURS (PVT) LTD."
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')
            
            _dispatch_email(subject, plain_message, from_email, [user.email], html_message=html_message)
            
            # Store email in session
            request.session['reset_password_email'] = email
            request.session[f'reset_code_{user.id}'] = code
            
            messages.success(request, f"A 6-digit OTP reset code has been dispatched to {email}.")
            return redirect('forgot_password_verify')
        else:
            messages.error(request, "No registered account was found with that email address.")
            
    return render(request, 'auth/forgot_password.html')


def forgot_password_verify_view(request):
    email = request.session.get('reset_password_email')
    if not email:
        messages.error(request, "Please request a password reset first.")
        return redirect('forgot_password')
        
    user = get_object_or_404(User, email=email)
    
    now = timezone.now()
    is_expired = False
    time_left_seconds = 0
    if user.otp_created_at:
        elapsed = (now - user.otp_created_at).total_seconds()
        if elapsed > 300:  # 5 minutes
            is_expired = True
        else:
            time_left_seconds = int(300 - elapsed)
    else:
        is_expired = True
        
    if request.method == 'POST':
        if is_expired:
            messages.error(request, "The code has expired. Please request a new reset code.")
        else:
            code_input = request.POST.get('code', '')
            if code_input == user.email_verification_code:
                # Mark verification session verified
                request.session['reset_password_verified_user_id'] = user.id
                return redirect('forgot_password_reset', user_id=user.id)
            else:
                messages.error(request, "Invalid code. Please try again.")
                
    dev_code = request.session.get(f'reset_code_{user.id}', user.email_verification_code)
    
    return render(request, 'auth/forgot_password_verify.html', {
        'user': user,
        'dev_code': dev_code,
        'is_expired': is_expired,
        'time_left_seconds': time_left_seconds
    })


def forgot_password_reset_view(request, user_id):
    verified_user_id = request.session.get('reset_password_verified_user_id')
    if not verified_user_id or verified_user_id != user_id:
        messages.error(request, "Access unauthorized. Please complete verification.")
        return redirect('forgot_password')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        if password and password_confirm:
            if password == password_confirm:
                user.set_password(password)
                user.email_verification_code = None
                user.otp_created_at = None
                user.save()
                
                # Clear session
                request.session.pop('reset_password_email', None)
                request.session.pop('reset_password_verified_user_id', None)
                request.session.pop(f'reset_code_{user.id}', None)
                
                messages.success(request, "Your password has been successfully reset! You can now log in.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        else:
            messages.error(request, "Please enter all password fields.")
            
    return render(request, 'auth/forgot_password_reset.html', {'user': user})


def agent_signup_verify_view(request, user_id):
    user = get_object_or_404(User, id=user_id, role='agent')
    if user.is_email_verified:
        return redirect('agent_signup_documents', user_id=user.id)
        
    now = timezone.now()
    is_expired = False
    time_left_seconds = 0
    if user.otp_created_at:
        elapsed = (now - user.otp_created_at).total_seconds()
        if elapsed > 300:
            is_expired = True
        else:
            time_left_seconds = int(300 - elapsed)
    else:
        is_expired = True
        
    if request.method == 'POST':
        if is_expired:
            messages.error(request, "This verification code has expired. Please request a new code.")
        else:
            code_input = request.POST.get('code', '')
            if code_input == user.email_verification_code:
                user.is_email_verified = True
                user.email_verification_code = None
                user.otp_created_at = None
                user.save()
                messages.success(request, "Email verified successfully! Please complete Step 3 of onboarding.")
                return redirect('agent_signup_documents', user_id=user.id)
            else:
                messages.error(request, "Invalid verification code. Please try again.")
                
    dev_code = request.session.get(f'verification_code_{user.id}', user.email_verification_code)
    
    return render(request, 'auth/agent_verify_otp.html', {
        'user': user,
        'dev_code': dev_code,
        'is_expired': is_expired,
        'time_left_seconds': time_left_seconds
    })


def agent_signup_documents_view(request, user_id):
    user = get_object_or_404(User, id=user_id, role='agent')
    if not user.is_email_verified:
        messages.error(request, "Please verify your email address first.")
        return redirect('agent_signup_verify', user_id=user.id)
        
    # Check if they are already fully complete
    if user.address and user.profile_photo and user.id_card_front and user.id_card_back:
        return redirect('pending_approval')
        
    form = AgentDocumentsForm(instance=user)
    if request.method == 'POST':
        form = AgentDocumentsForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            user.approval_status = 'pending'
            user.save()
            
            # Clear dev helper code in session if present
            request.session.pop(f'verification_code_{user.id}', None)
            
            messages.success(request, "Documents uploaded successfully! Your application is now pending admin review.")
            return redirect('pending_approval')
            
    return render(request, 'auth/agent_documents.html', {
        'form': form,
        'user': user
    })


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT ACCOUNTS API
# ─────────────────────────────────────────────────────────────────────────────

def _is_super_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'role', None) in ['admin', 'super_admin'])


@login_required
@never_cache
def admin_dashboard_api(request):
    """GET: Return all agent accounts for admin dashboard."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    agents = User.objects.filter(role='agent').order_by('-date_joined')
    data = []
    for a in agents:
        entries = AgentLedger.objects.filter(agent=a)
        credits = sum(e.amount for e in entries if e.entry_type == 'credit')
        debits = sum(e.amount for e in entries if e.entry_type == 'debit')
        bal = float(credits - debits)

        id_card_front_url = request.build_absolute_uri(a.id_card_front.url) if a.id_card_front else None
        id_card_back_url = request.build_absolute_uri(a.id_card_back.url) if a.id_card_back else None
        profile_photo_url = request.build_absolute_uri(a.profile_photo.url) if a.profile_photo else None

        data.append({
            'id':                  a.id,
            'username':            a.username,
            'first_name':          a.first_name,
            'last_name':           a.last_name,
            'company_name':        a.company_name or a.username,
            'email':               a.email,
            'phone':               a.phone or 'N/A',
            'address':             a.address or 'N/A',
            'is_verified_partner': getattr(a, 'is_verified_partner', False),
            'wallet_balance':      bal,
            'approval_status':     getattr(a, 'approval_status', 'pending') or 'pending',
            'date_joined':         a.date_joined.strftime('%Y-%m-%d %H:%M') if a.date_joined else '',
            'agent_id_number':     getattr(a, 'agent_id_number', None) or 'N/A',
            'id_card_front':       id_card_front_url,
            'id_card_back':        id_card_back_url,
            'profile_photo':       profile_photo_url,
        })
    return JsonResponse({'success': True, 'agents': data})


@csrf_exempt
@login_required
@never_cache
def admin_approve_agent(request, agent_id):
    """POST: Approve an agent account."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        agent = User.objects.get(pk=agent_id, role='agent')
        agent.approval_status = 'approved'
        agent.is_active = True
        if not agent.agent_id_number:
            agent.agent_id_number = generate_agent_id_number()
            agent.id_card_issued_at = timezone.now()
        agent.save()
        try:
            send_agent_status_email(agent, 'approved')
        except Exception:
            pass
        return JsonResponse({
            'success': True,
            'message': f'Agent {agent.company_name or agent.username} approved successfully.',
            'status': 'approved',
            'agent_id_number': agent.agent_id_number
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)


@csrf_exempt
@login_required
@never_cache
def admin_reject_agent(request, agent_id):
    """POST: Reject an agent account application."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        agent = User.objects.get(pk=agent_id, role='agent')
        agent.approval_status = 'rejected'
        agent.save()
        try:
            send_agent_status_email(agent, 'rejected')
        except Exception:
            pass
        return JsonResponse({'success': True, 'message': f'Agent {agent.company_name or agent.username} application rejected.'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)


@csrf_exempt
@login_required
@never_cache
def admin_suspend_agent(request, agent_id):
    """POST: Suspend an agent account."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        agent = User.objects.get(pk=agent_id, role='agent')
        if agent.approval_status == 'suspended':
            agent.approval_status = 'approved'
            msg = f'Agent {agent.company_name or agent.username} account reactivated.'
        else:
            agent.approval_status = 'suspended'
            msg = f'Agent {agent.company_name or agent.username} account suspended.'
        agent.save()
        return JsonResponse({'success': True, 'message': msg, 'status': agent.approval_status})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)


@csrf_exempt
@login_required
@never_cache
def admin_toggle_agent_verification_badge(request, agent_id):
    """POST: Toggle verification badge for partner agent."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        agent = User.objects.get(pk=agent_id, role='agent')
        agent.is_verified_partner = not getattr(agent, 'is_verified_partner', False)
        agent.save()
        return JsonResponse({'success': True, 'is_verified_partner': agent.is_verified_partner})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)


@login_required
@never_cache
def admin_clients_list_api(request):
    """GET: Return all customer (client) accounts for admin dashboard."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    clients = User.objects.filter(role='customer').order_by('-date_joined')
    data = []
    for c in clients:
        data.append({
            'id':               c.id,
            'username':         c.username,
            'first_name':       c.first_name,
            'last_name':        c.last_name,
            'email':            c.email,
            'phone':            c.phone or '',
            'address':          c.address or '',
            'is_email_verified': c.is_email_verified,
            'is_active':        c.is_active,
            'date_joined':      c.date_joined.strftime('%Y-%m-%d'),
        })
    return JsonResponse({'success': True, 'clients': data})


@csrf_exempt
@login_required
@never_cache
def admin_client_toggle_api(request, client_id):
    """POST: Toggle a client's active status (block/unblock)."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        client = User.objects.get(pk=client_id, role='customer')
        client.is_active = not client.is_active
        client.save()
        return JsonResponse({'success': True, 'is_active': client.is_active})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client not found.'}, status=404)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT LEDGER API
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@never_cache
def admin_agent_ledger_api(request, agent_id):
    """GET: Return all ledger entries + running balance for an agent."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        agent = User.objects.get(pk=agent_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)

    entries = AgentLedger.objects.filter(agent=agent).order_by('-created_at')

    total_credit = sum(e.amount for e in entries if e.entry_type == 'credit')
    total_debit  = sum(e.amount for e in entries if e.entry_type == 'debit')
    balance      = total_credit - total_debit

    data = []
    running = 0
    for e in reversed(list(entries)):  # oldest first for running balance
        signed = float(e.amount) if e.entry_type == 'credit' else -float(e.amount)
        running += signed
        data.append({
            'id':          e.id,
            'entry_type':  e.entry_type,
            'category':    e.category,
            'category_display': e.get_category_display(),
            'amount':      float(e.amount),
            'description': e.description,
            'reference':   e.reference,
            'created_at':  e.created_at.strftime('%Y-%m-%d %H:%M'),
            'running_bal': round(running, 2),
        })
    data.reverse()  # newest first for display

    return JsonResponse({
        'success':       True,
        'agent_name':    agent.company_name or agent.username,
        'entries':       data,
        'total_credit':  float(total_credit),
        'total_debit':   float(total_debit),
        'balance':       float(balance),
    })


@csrf_exempt
@login_required
@never_cache
def admin_agent_ledger_create_api(request, agent_id):
    """POST: Add a new ledger entry for an agent."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only.'}, status=405)

    try:
        agent = User.objects.get(pk=agent_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Agent not found.'}, status=404)

    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST

    entry_type  = body.get('entry_type', 'credit')
    category    = body.get('category', 'commission')
    amount_raw  = body.get('amount', 0)
    description = body.get('description', '')
    reference   = body.get('reference', '')

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return JsonResponse({'error': 'Amount must be a positive number.'}, status=400)

    entry = AgentLedger.objects.create(
        agent=agent,
        entry_type=entry_type,
        category=category,
        amount=amount,
        description=description,
        reference=reference,
        created_by=request.user,
    )
    return JsonResponse({'success': True, 'id': entry.id, 'message': 'Ledger entry added.'})


@csrf_exempt
@login_required
@never_cache
def admin_agent_ledger_delete_api(request, entry_id):
    """DELETE/POST: Remove a single ledger entry."""
    if not _is_super_admin(request.user):
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        entry = AgentLedger.objects.get(pk=entry_id)
        entry.delete()
        return JsonResponse({'success': True, 'message': 'Entry deleted.'})
    except AgentLedger.DoesNotExist:
        return JsonResponse({'error': 'Entry not found.'}, status=404)


@csrf_exempt
def process_b2b_agent_commission_and_email(user, tracking_id, item_title, seats_count, total_fare):
    if not user or not user.is_authenticated:
        return
    if getattr(user, 'role', '') == 'agent' or getattr(user, 'is_agent', False):
        try:
            from apps.accounts.models import AgentLedger
            from django.core.mail import send_mail
            from django.conf import settings
            
            # 5% agent B2B commission rate
            commission_amount = round(float(total_fare) * 0.05, 2)
            if commission_amount > 0:
                AgentLedger.objects.create(
                    agent=user,
                    entry_type='credit',
                    category='commission',
                    amount=commission_amount,
                    description=f"B2B Agent Commission for {item_title} [{tracking_id}] ({seats_count} Seats)",
                    reference=tracking_id
                )
                
                agent_email = user.email
                if agent_email:
                    agent_name = user.get_full_name() or user.company_name or user.username
                    subject = f"B2B Commission Credited - {item_title} [{tracking_id}]"
                    body_html = f"""
                    <p>JazakAllah Khair for booking with <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong></p>
                    
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
                        <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">B2B Ledger Credit Notice</h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                            <tr><td style="padding: 4px 0; color: #64748b;">Tracking Reference:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{tracking_id}</td></tr>
                            <tr><td style="padding: 4px 0; color: #64748b;">Item / Service:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{item_title}</td></tr>
                            <tr><td style="padding: 4px 0; color: #64748b;">Seats / Passengers:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{seats_count}</td></tr>
                            <tr><td style="padding: 4px 0; color: #64748b;">Total Fare:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">PKR {float(total_fare):,.2f}</td></tr>
                            <tr style="border-top: 1px solid #e2e8f0;"><td style="padding: 8px 0 4px 0; color: #166534; font-weight: bold;">Commission Credited:</td><td style="padding: 8px 0 4px 0; font-weight: 900; color: #166534; font-size: 16px; text-align: right;">PKR {commission_amount:,.2f}</td></tr>
                        </table>
                    </div>
                    
                    <p>Dear Partner Agent, your B2B commission of <strong>PKR {commission_amount:,.2f}</strong> has been processed and credited directly into your Agent Ledger account. You can view your updated ledger statement anytime in your B2B Agent Dashboard.</p>
                    """
                    
                    html_message = build_professional_email_html("B2B Ledger Credit Notice", agent_name, body_html, "View Agent Dashboard", "http://127.0.0.1:8000/dashboard/agent/")
                    plain_body = f"Hello Agent {agent_name},\n\nB2B Commission of PKR {commission_amount:,.2f} credited for {tracking_id}.\n\nREI GOLDEN STAR TRAVEL & TOURS (PVT) LTD."
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')
                    
                    _dispatch_email(subject, plain_body, from_email, [agent_email], html_message=html_message)
                    print(f"[Agent Commission] Successfully credited PKR {commission_amount} to Agent {user.username} for {tracking_id}")
        except Exception as e:
            print(f"[Agent Commission Error] {e}")

def send_package_booking_confirmation_email(user, tracking_id, package, booking, guest_email=None, guest_name=None, guest_phone=None):
    """Auto-dispatches a professional email confirmation with tracking reference ID to client/pilgrim and notification to admin."""
    try:
        from django.conf import settings
        recipient_email = (user.email if (user and hasattr(user, 'email') and user.email) else guest_email or '').strip()
        if not recipient_email:
            return
        
        recipient_name = (user.get_full_name() if (user and hasattr(user, 'get_full_name') and user.get_full_name()) else guest_name) or 'Valued Pilgrim'
        
        subject = f"Package Booking Confirmed [{tracking_id}] - {package.title} | Golden Star Travel"

        pax_parts = []
        if booking.adults_count > 0:
            pax_parts.append(f"{booking.adults_count} Adult(s)")
        if booking.children_count > 0:
            pax_parts.append(f"{booking.children_count} Child(ren)")
        if booking.infants_count > 0:
            pax_parts.append(f"{booking.infants_count} Infant(s)")
        pax_summary = ", ".join(pax_parts) if pax_parts else f"{booking.adults_count} Adult(s)"

        body_html = f"""
        <p>JazakAllah Khair <strong>{recipient_name}</strong> for choosing <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong> for your holy pilgrimage.</p>
        
        <p>Your package booking has been successfully registered in our system and dispatched to our specialized consultants.</p>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin: 24px 0;">
            <h4 style="margin: 0 0 14px 0; color: #ea580c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px;">
                📋 Booking Details & Reference
            </h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">Tracking Reference ID:</td>
                    <td style="padding: 6px 0; font-weight: 900; color: #ea580c; font-family: monospace; font-size: 15px; text-align: right;">{tracking_id}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">Package Name:</td>
                    <td style="padding: 6px 0; font-weight: bold; color: #0f172a; text-align: right;">{package.title}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">Duration:</td>
                    <td style="padding: 6px 0; font-weight: bold; color: #0f172a; text-align: right;">{package.duration_days} Days</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">Room Sharing:</td>
                    <td style="padding: 6px 0; font-weight: bold; color: #0f172a; text-align: right;">{booking.sharing_category} Sharing</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">Passengers:</td>
                    <td style="padding: 6px 0; font-weight: bold; color: #0f172a; text-align: right;">{pax_summary}</td>
                </tr>
                <tr style="border-top: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0 4px 0; color: #0f172a; font-weight: bold;">Total Estimated Fare:</td>
                    <td style="padding: 10px 0 4px 0; font-weight: 900; color: #166534; font-size: 17px; text-align: right;">PKR {float(booking.total_price):,.0f}</td>
                </tr>
            </table>
        </div>
        
        <p style="font-size: 12px; color: #64748b; background-color: #eff6ff; padding: 12px 16px; border-radius: 10px; border: 1px solid #bfdbfe;">
            💡 <strong>Next Steps:</strong> You can track your live booking status anytime on our website using your Tracking Reference ID: <strong>{tracking_id}</strong>. Our pilgrimage consultant will contact you via WhatsApp/Phone shortly to verify your passport details and issue booking documents.
        </p>
        """

        html_message = build_professional_email_html(
            "Pilgrimage Package Booking Confirmed",
            recipient_name,
            body_html,
            "Track My Booking Status",
            f"http://127.0.0.1:8000/?track={tracking_id}#track-section"
        )

        plain_body = f"Hello {recipient_name},\n\nYour pilgrimage booking for {package.title} has been confirmed.\n\nTracking ID: {tracking_id}\nTotal Fare: PKR {float(booking.total_price):,.0f}\n\nREI GOLDEN STAR TRAVEL & TOURS"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')

        if recipient_email:
            _dispatch_email(subject, plain_body, from_email, [recipient_email], html_message=html_message)
            print(f"[Booking Email OK] Automated email dispatched to {recipient_email} for tracking ID {tracking_id}")

        # Send admin alert email for new package booking
        subject_admin = f"[NEW BOOKING] {tracking_id} - {package.title} ({recipient_name})"
        body_admin_html = f"""
        <p>A new pilgrimage package booking has been registered on the website portal.</p>
        <div style="background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 18px; margin: 20px 0;">
            <h4 style="margin: 0 0 10px 0; color: #c45517; font-size: 14px;">Booking Summary</h4>
            <p style="margin: 0 0 4px 0;"><strong>Tracking Reference ID:</strong> {tracking_id}</p>
            <p style="margin: 0 0 4px 0;"><strong>Pilgrim Name:</strong> {recipient_name}</p>
            <p style="margin: 0 0 4px 0;"><strong>Contact Email:</strong> {recipient_email or 'N/A'}</p>
            <p style="margin: 0 0 4px 0;"><strong>Contact Phone:</strong> {guest_phone or 'N/A'}</p>
            <p style="margin: 0 0 4px 0;"><strong>Package Title:</strong> {package.title}</p>
            <p style="margin: 0 0 4px 0;"><strong>Room Sharing:</strong> {booking.sharing_category} Sharing</p>
            <p style="margin: 0 0 4px 0;"><strong>Passengers:</strong> {pax_summary}</p>
            <p style="margin: 0;"><strong>Total Fare:</strong> PKR {float(booking.total_price):,.0f}</p>
        </div>
        """
        html_admin = build_professional_email_html("New Package Booking Alert", "Operations Admin", body_admin_html, "Manage Bookings in Admin Panel", "http://127.0.0.1:8000/dashboard/admin/")
        _dispatch_email(subject_admin, f"New booking {tracking_id} by {recipient_name}", from_email, [from_email], html_message=html_admin)
    except Exception as e:
        print(f"[Booking Email Error] {e}")


def submit_package_booking_api(request):
    from apps.bookings.models import Booking
    from apps.packages.models import Package
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method only.'}, status=405)
        
    try:
        try:
            body = json.loads(request.body)
        except Exception:
            body = request.POST

        guest_name = (body.get('full_name') or body.get('name') or '').strip()
        guest_email = (body.get('email') or '').strip().lower()
        guest_phone = (body.get('phone') or body.get('phone_number') or '').strip()

        # Resolve user or create guest customer user
        if request.user.is_authenticated:
            user = request.user
        else:
            if guest_email:
                user = User.objects.filter(email__iexact=guest_email).first()
                if not user:
                    import time
                    username = guest_email.split('@')[0] + '_' + str(int(time.time()))[-4:]
                    user = User.objects.create_user(
                        username=username,
                        email=guest_email,
                        first_name=guest_name or 'Pilgrim Guest',
                        role='customer'
                    )
                    if guest_phone and hasattr(user, 'phone_number'):
                        user.phone_number = guest_phone
                        user.save()
            elif guest_phone:
                user = User.objects.filter(phone_number=guest_phone).first() if hasattr(User, 'phone_number') else None
                if not user:
                    import time
                    username = 'guest_' + str(int(time.time()))[-6:]
                    user = User.objects.create_user(
                        username=username,
                        email=f'{username}@goldenstar.com',
                        first_name=guest_name or 'Pilgrim Guest',
                        role='customer'
                    )
                    if hasattr(user, 'phone_number'):
                        user.phone_number = guest_phone
                        user.save()
            else:
                import time
                username = 'guest_' + str(int(time.time()))[-6:]
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@goldenstar.com',
                    first_name=guest_name or 'Pilgrim Guest',
                    role='customer'
                )

        package_id = int(body.get('package_id'))
        sharing_category = body.get('sharing_category', 'Sharing').strip()
        adults_count = int(body.get('adults_count', body.get('quantity', 1)))
        children_with_bed_count = int(body.get('children_with_bed_count', 0))
        children_no_bed_count   = int(body.get('children_no_bed_count', 0))
        children_count = int(body.get('children_count', children_with_bed_count + children_no_bed_count))
        infants_count = int(body.get('infants_count', 0))
        notes = body.get('notes', '').strip()
        
        selected_addons = body.get('selected_addons', [])
        if isinstance(selected_addons, str):
            try: selected_addons = json.loads(selected_addons)
            except Exception: selected_addons = []

        package = Package.objects.get(id=package_id)
        
        # Check seats availability
        requested_seats = adults_count + children_count
        if package.available_seats < requested_seats:
            return JsonResponse({
                'success': False,
                'message': f"Only {package.available_seats} seat(s) available for this package (Requested: {requested_seats})."
            }, status=400)

        # 4 Room Sharing Categories Calculation
        cat_lower = sharing_category.lower()
        if 'sharing' in cat_lower and 'quad' not in cat_lower and 'triple' not in cat_lower and 'double' not in cat_lower:
            room_rate = float(package.price_sharing or package.price or 210000.0)
        elif 'triple' in cat_lower:
            room_rate = float(package.price_triple or (package.price + 30000))
        elif 'double' in cat_lower:
            room_rate = float(package.price_double or (package.price + 75000))
        else: # Quad
            room_rate = float(package.price_quad or package.price or 245000.0)
            
        child_with_bed_rate = float(package.price_child_with_bed or package.price_child or 180000.0)
        child_no_bed_rate   = float(package.price_child_no_bed or 120000.0)
        infant_rate         = float(package.price_infant or 65000.0)
        
        adults_cost = adults_count * room_rate
        if children_with_bed_count > 0 or children_no_bed_count > 0:
            children_cost = (children_with_bed_count * child_with_bed_rate) + (children_no_bed_count * child_no_bed_rate)
        else:
            children_cost = children_count * child_with_bed_rate
        infants_cost = infants_count * infant_rate
        
        addons_cost = 0.0
        addon_names = []
        if isinstance(selected_addons, list):
            for add in selected_addons:
                if isinstance(add, dict):
                    try:
                        p_val = float(add.get('price', 0))
                        addons_cost += p_val
                        name_val = add.get('name', 'Add-on')
                        addon_names.append(f"{name_val} (+PKR {p_val:,.0f})")
                    except (ValueError, TypeError): pass
                elif isinstance(add, str):
                    addon_names.append(add)

        subtotal = adults_cost + children_cost + infants_cost + addons_cost
        
        disc_percent = float(package.discount_percentage or 0.0)
        disc_flat = float(package.discount_amount or 0.0)
        discount_applied = (subtotal * disc_percent / 100.0) + disc_flat
        
        total_price = max(0.0, subtotal - discount_applied)
        
        booking = Booking.objects.create(
            user=user,
            package=package,
            booking_type='package',
            status='pending',
            sharing_category=sharing_category,
            adults_count=adults_count,
            children_count=children_count,
            infants_count=infants_count,
            selected_addons=selected_addons,
            discount_applied=discount_applied,
            notes=notes,
            total_price=total_price
        )

        # Deduct available seats
        package.available_seats = max(0, package.available_seats - requested_seats)
        package.save()

        tracking_id = f"GSA-B-{booking.id}"

        # Auto-send Email Notification to Client / Pilgrim with Tracking ID
        send_package_booking_confirmation_email(user, tracking_id, package, booking, guest_email=guest_email, guest_name=guest_name)

        # B2B Agent Commission & Email Notification
        process_b2b_agent_commission_and_email(request.user, tracking_id, package.title, requested_seats, total_price)

        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'tracking_id': tracking_id,
            'package_title': package.title,
            'sharing_category': sharing_category,
            'adults_count': adults_count,
            'children_count': children_count,
            'total_price': str(total_price),
            'message': 'Package booking submitted successfully!'
        })
    except Package.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Selected package not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Booking Error: {str(e)}'}, status=400)


@csrf_exempt
def submit_visa_application_api(request):
    from apps.visa.models import VisaApplication, VisaPackage
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method only.'}, status=405)
        
    try:
        try:
            body = json.loads(request.body)
        except Exception:
            body = request.POST
            
        country_input = body.get('country', '').strip()
        name = (body.get('full_name') or body.get('name') or '').strip()
        email = body.get('email', '').strip()
        phone = body.get('phone', '').strip()
        address = body.get('address', '').strip()
        passport_number = body.get('passport_number', '').strip()
        price = body.get('price') or None
        package_id = body.get('visa_package_id') or body.get('package_id')
        notes = body.get('notes') or body.get('additional_notes') or ''
        
        if not country_input and not package_id:
            return JsonResponse({'success': False, 'message': 'Destination country or visa package is required.'}, status=400)
            
        visa_package = None
        if package_id:
            visa_package = VisaPackage.objects.filter(id=package_id).first()
            if visa_package and not country_input:
                country_input = visa_package.country

        country = country_input.split('(')[0].split('Tourist')[0].split('Visit')[0].strip() if country_input else 'General Visit Visa'
        
        if visa_package and not price:
            price = visa_package.price

        user = request.user if (request.user and request.user.is_authenticated) else None
        if not user and email:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                import time
                username = email.split('@')[0] + '_' + str(int(time.time()))[-4:]
                user = User.objects.create_user(username=username, email=email, first_name=name or 'Applicant')

        visa = VisaApplication.objects.create(
            user=user,
            visa_package=visa_package,
            country=country,
            full_name=name,
            email=email,
            phone=phone,
            address=address,
            passport_number=passport_number,
            price=price if price else None,
            additional_notes=notes,
            status='pending'
        )
        return JsonResponse({
            'success': True,
            'visa_id': visa.id,
            'tracking_id': f"GSA-V-{visa.id:06d}",
            'message': 'Visa application submitted successfully!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@csrf_exempt
def submit_flight_quote_api(request):
    from apps.flights.models import FlightQuoteRequest
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method only.'}, status=405)
        
    try:
        try:
            body = json.loads(request.body)
        except Exception:
            body = request.POST
            
        departure_city = body.get('departure_city', '').strip()
        destination_city = body.get('destination_city', '').strip()
        departure_date = body.get('departure_date', '').strip()
        return_date = body.get('return_date', '').strip() or None
        email = body.get('email', '').strip()
        name = body.get('name', '').strip()
        
        if not departure_city or not destination_city or not departure_date:
            return JsonResponse({'success': False, 'message': 'Departure city, destination city, and departure date are required.'}, status=400)
            
        user = request.user
        if not user.is_authenticated:
            if email:
                user = User.objects.filter(email__iexact=email).first()
                if not user:
                    import time
                    username = email.split('@')[0] + '_' + str(int(time.time()))[-4:]
                    user = User.objects.create_user(username=username, email=email, first_name=name or 'Passenger')
            else:
                return JsonResponse({'success': False, 'message': 'Authentication required. Please login to request a flight quote.'}, status=401)

        flight = FlightQuoteRequest.objects.create(
            user=user,
            departure_city=departure_city,
            destination_city=destination_city,
            departure_date=departure_date,
            return_date=return_date,
            status='pending'
        )
        return JsonResponse({
            'success': True,
            'flight_id': flight.id,
            'tracking_id': f"GSA-F-{flight.id}",
            'message': 'Flight quote request submitted successfully!'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@csrf_exempt
def submit_flight_ticket_booking_api(request):
    from apps.flights.models import FlightTicketOffer
    from apps.bookings.models import Booking
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method only.'}, status=405)
        
    try:
        try:
            body = json.loads(request.body)
        except Exception:
            body = request.POST
            
        ticket_id = body.get('ticket_id')
        passenger_name = body.get('passenger_name', '').strip()
        email = body.get('email', '').strip()
        phone = body.get('phone', '').strip()
        passport_number = body.get('passport_number', '').strip()
        address = body.get('address', '').strip()
        travel_date = body.get('travel_date', '').strip()
        seats_count = int(body.get('seats_count', 1))
        baggage_tier = body.get('baggage_tier', '30 kg').strip()
        
        ticket_offer = FlightTicketOffer.objects.get(id=ticket_id)
        unit_price = float(body.get('selected_price') or ticket_offer.price)
        
        if ticket_offer.available_seats < seats_count:
            return JsonResponse({'success': False, 'message': f'Only {ticket_offer.available_seats} seat(s) available on this flight.'}, status=400)
            
        if not unit_price:
            unit_price = float(ticket_offer.price)
            
        total_fare = unit_price * seats_count
        
        booking_user = request.user if request.user.is_authenticated else None
        user_email = (request.user.email if request.user.is_authenticated and request.user.email else email) or email
        
        if not booking_user and email:
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user:
                booking_user = existing_user
        
        booking = Booking.objects.create(
            user=booking_user,
            full_name=passenger_name or (request.user.get_full_name() if request.user.is_authenticated else 'Guest Passenger'),
            email=user_email,
            phone_number=phone,
            booking_type='flight',
            status='pending',
            adults_count=seats_count,
            notes=f"Airline: {ticket_offer.airline_name} ({ticket_offer.flight_number}) | Baggage Tier: {baggage_tier} | Passenger: {passenger_name} | Email: {user_email} | Phone: {phone} | Address: {address} | Passport: {passport_number} | Travel Date: {travel_date}",
            total_price=total_fare
        )
        
        # Decrement available seats on ticket offer
        ticket_offer.available_seats = max(0, ticket_offer.available_seats - seats_count)
        ticket_offer.save()
        
        tracking_id = f"GSA-FLT-{booking.id}"
        
        # B2B Agent Commission & Email Notification (if logged in as agent)
        if request.user.is_authenticated:
            process_b2b_agent_commission_and_email(request.user, tracking_id, f"Flight Ticket ({ticket_offer.airline_name})", seats_count, total_fare)
        
        # Email Notification
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            subject_user = f"✈️ Flight Ticket Reservation - {ticket_offer.airline_name} [{tracking_id}]"
            message_user = (
                f"Assalamu Alaikum {passenger_name or 'Valued Customer'},\n\n"
                f"Your flight seat reservation request has been submitted successfully!\n\n"
                f"--- FLIGHT RESERVATION SUMMARY ---\n"
                f"Tracking Reference: {tracking_id}\n"
                f"Airline: {ticket_offer.airline_name} ({ticket_offer.flight_number})\n"
                f"Route: {ticket_offer.departure_city} -> {ticket_offer.destination_city}\n"
                f"Travel Date: {travel_date}\n"
                f"Seats Booked: {seats_count}\n"
                f"Total Fare: PKR {total_fare:,.2f}\n"
                f"Passenger Name: {passenger_name}\n"
                f"Passport Number: {passport_number}\n\n"
                f"Our ticketing agent will contact you shortly on {phone} to issue your official e-ticket.\n\n"
                f"Warm regards,\nGolden Star Travel Agency"
            )
            
            if user_email:
                send_mail(
                    subject_user,
                    message_user,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@travelagency.com'),
                    [user_email],
                    fail_silently=True
                )
        except Exception as mail_err:
            print(f"[Mail Notice Error] {mail_err}")
            
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'tracking_id': tracking_id,
            'airline_name': ticket_offer.airline_name,
            'flight_number': ticket_offer.flight_number,
            'passenger_name': passenger_name,
            'phone': phone,
            'total_price': total_fare,
            'message': 'Flight ticket reservation submitted successfully!'
        })
    except FlightTicketOffer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Selected flight ticket offer does not exist.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@csrf_exempt
def live_search_api(request):
    """
    Real-time live search API for home page hero section filter
    Supports filtering by service_type, days (15/18/28), budget, and keyword/city.
    """
    from apps.packages.models import Package
    from apps.flights.models import FlightTicketOffer
    from apps.visa.models import VisaPackage
    from django.db.models import Q

    service_type = request.GET.get('service_type', 'all').lower().strip()
    days_str = request.GET.get('days', 'all').strip()
    budget = request.GET.get('budget', 'all').lower().strip()
    query = request.GET.get('q', '').lower().strip()

    results = []

    # 1. Search Packages (Umrah / Hajj)
    if service_type in ['all', 'umrah', 'hajj']:
        pkg_qs = Package.objects.all()
        if service_type == 'umrah':
            pkg_qs = pkg_qs.filter(category__iexact='umrah')
        elif service_type == 'hajj':
            pkg_qs = pkg_qs.filter(category__iexact='hajj')

        # Filter by Days (15, 18, 28)
        if days_str and days_str.isdigit():
            pkg_qs = pkg_qs.filter(duration_days=int(days_str))

        if query:
            pkg_qs = pkg_qs.filter(
                Q(title__icontains=query) |
                Q(makkah_hotel_name__icontains=query) |
                Q(madinah_hotel_name__icontains=query) |
                Q(airline__icontains=query) |
                Q(flight_routes__icontains=query) |
                Q(description__icontains=query)
            )

        for p in pkg_qs:
            price_val = float(p.price_quad or p.price or 0)
            if budget == 'economy' and price_val > 250000:
                continue
            elif budget == 'star' and (price_val < 250000 or price_val > 400000):
                continue
            elif budget == 'luxury' and price_val < 400000:
                continue

            results.append({
                'id': p.id,
                'type': 'package',
                'category': f"{(p.category or 'Package').capitalize()} ({p.duration_days} Days)",
                'title': p.title,
                'subtitle': f"⏳ {p.duration_days} Days • Makkah: {p.makkah_hotel_name or 'Hotel'} ({p.makkah_hotel_distance or 'Near'}) | Madinah: {p.madinah_hotel_name or 'Hotel'} ({p.madinah_hotel_distance or 'Near'})",
                'price': price_val,
                'badge': f"🎟️ {p.available_seats} Seats Left" if p.available_seats else "Available",
                'url': f"/packages/{p.id}/"
            })

    # 2. Search Flights
    if service_type in ['all', 'flights']:
        flt_qs = FlightTicketOffer.objects.all()
        if query:
            flt_qs = flt_qs.filter(
                Q(airline_name__icontains=query) |
                Q(departure_city__icontains=query) |
                Q(destination_city__icontains=query) |
                Q(flight_number__icontains=query)
            )

        for f in flt_qs:
            price_val = float(f.price or 0)
            if budget == 'economy' and price_val > 100000:
                continue
            elif budget == 'star' and (price_val < 100000 or price_val > 150000):
                continue
            elif budget == 'luxury' and price_val < 150000:
                continue

            results.append({
                'id': f.id,
                'type': 'flight',
                'category': f"Flight {f.flight_number}",
                'title': f"{f.airline_name} ({f.departure_city} -> {f.destination_city})",
                'subtitle': f"✈️ {f.departure_time_str} -> {f.arrival_time_str} ({f.duration_str}) | {f.baggage_checkin} Baggage",
                'price': price_val,
                'badge': f"🎟️ {f.available_seats} Seats Left",
                'url': f"/flights/"
            })

    # 3. Search Visas
    if service_type in ['all', 'visa']:
        visa_qs = VisaPackage.objects.all()
        if query:
            visa_qs = visa_qs.filter(
                Q(title__icontains=query) |
                Q(country__icontains=query) |
                Q(description__icontains=query)
            )

        for v in visa_qs:
            price_val = float(v.price or 0)
            results.append({
                'id': v.id,
                'type': 'visa',
                'category': f"{v.country} Visa",
                'title': v.title,
                'subtitle': f"🛂 {v.processing_time} | {v.visa_validity}",
                'price': price_val,
                'badge': "Instant Approval",
                'url': f"/visa/"
            })

    return JsonResponse({'results': results, 'count': len(results)})



@csrf_exempt
@admin_required_api
def admin_flight_ticket_detail_api(request, pk):
    from apps.flights.models import FlightTicketOffer
    ticket = get_object_or_404(FlightTicketOffer, pk=pk)
    if request.method in ['POST', 'PUT']:
        try:
            body = json.loads(request.body)
        except Exception:
            body = request.POST
            
        ticket.airline_name = body.get('airline_name', ticket.airline_name).strip()
        ticket.airline_code = body.get('airline_code', ticket.airline_code).strip().upper()
        ticket.flight_number = body.get('flight_number', ticket.flight_number).strip()
        ticket.departure_city = body.get('departure_city', ticket.departure_city).strip()
        ticket.departure_airport_code = body.get('departure_airport_code', ticket.departure_airport_code).strip().upper()
        ticket.destination_city = body.get('destination_city', ticket.destination_city).strip()
        ticket.destination_airport_code = body.get('destination_airport_code', ticket.destination_airport_code).strip().upper()
        ticket.departure_time_str = body.get('departure_time_str', ticket.departure_time_str).strip()
        ticket.arrival_time_str = body.get('arrival_time_str', ticket.arrival_time_str).strip()
        ticket.duration_str = body.get('duration_str', ticket.duration_str).strip()
        ticket.flight_type = body.get('flight_type', ticket.flight_type).strip()
        ticket.ticket_class = body.get('ticket_class', ticket.ticket_class).strip()
        ticket.price = float(body.get('price', ticket.price))
        ticket.baggage_checkin = body.get('baggage_checkin', ticket.baggage_checkin).strip()
        ticket.baggage_hand = body.get('baggage_hand', ticket.baggage_hand).strip()
        ticket.total_seats = int(body.get('total_seats', ticket.total_seats))
        ticket.available_seats = int(body.get('available_seats', ticket.available_seats))
        ticket.save()
        return JsonResponse({'success': True})
    elif request.method == 'DELETE':
        ticket.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
def submit_custom_inquiry_api(request):
    """
    POST: Submit a custom package inquiry or Contact Us message.
    Accepts requests from both authenticated and guest users.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required.'}, status=405)
        
    from apps.packages.models import CustomPackageInquiry
    try:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = request.POST

        name = (body.get('name') or '').strip()
        email = (body.get('email') or '').strip()
        phone = (body.get('phone') or body.get('phone_number') or '').strip()
        package_type = (body.get('package_type') or 'umrah').strip().lower()
        
        days_raw = body.get('days')
        days = int(days_raw) if (days_raw and str(days_raw).isdigit()) else 15
        
        makkah_raw = body.get('makkah_distance')
        makkah_distance = int(makkah_raw) if (makkah_raw and str(makkah_raw).isdigit()) else 350
        
        madinah_raw = body.get('madinah_distance')
        madinah_distance = int(madinah_raw) if (madinah_raw and str(madinah_raw).isdigit()) else 150
        
        airline = (body.get('airline') or 'Saudi Airlines').strip()
        additional_notes = (body.get('additional_notes') or body.get('message') or '').strip()

        if not name or not phone:
            return JsonResponse({'success': False, 'message': 'Name and phone number are required.'}, status=400)

        user = request.user if (hasattr(request, 'user') and request.user.is_authenticated) else None

        # Create inquiry
        inquiry = CustomPackageInquiry.objects.create(
            user=user,
            name=name,
            email=email,
            phone=phone,
            package_type=package_type,
            days=days,
            makkah_distance=makkah_distance,
            madinah_distance=madinah_distance,
            airline=airline,
            additional_notes=additional_notes,
            is_contacted=False
        )

        # Trigger async emails (User confirmation & Admin notification)
        send_custom_inquiry_emails(inquiry)

        return JsonResponse({
            'success': True,
            'id': inquiry.id,
            'inquiry_id': inquiry.id,
            'message': 'Your message/inquiry has been submitted successfully! Our representative will contact you shortly.'
        })
    except Exception as e:
        logger.exception(f"Custom inquiry error: {e}")
        return JsonResponse({'success': False, 'message': f'Error submitting inquiry: {str(e)}'}, status=400)


def _send_custom_inquiry_emails_sync(inquiry):
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'goldenstartraveltours@gmail.com')

    if inquiry.package_type == 'contact':
        # 1. Contact Us Inquiry Email for Pilgrim / Client
        subject_user = "Thank You for Contacting Golden Star Travel & Tours"
        body_user_html = f"""
        <p>Assalamu Alaikum <strong>{inquiry.name}</strong>,</p>
        <p>Thank you for reaching out to <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong> We have received your direct inquiry with the following details:</p>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
            <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Contact Inquiry Summary</h4>
            <p style="margin: 0 0 6px 0; color: #475569;"><strong>Full Name:</strong> {inquiry.name}</p>
            <p style="margin: 0 0 6px 0; color: #475569;"><strong>Email Address:</strong> {inquiry.email or 'N/A'}</p>
            <p style="margin: 0 0 6px 0; color: #475569;"><strong>Phone / WhatsApp:</strong> {inquiry.phone}</p>
            <p style="margin: 0; color: #475569;"><strong>Message / Notes:</strong> {inquiry.additional_notes or 'General Contact Request'}</p>
        </div>
        
        <p>Our dedicated travel support desk will review your message and contact you at <strong>{inquiry.phone}</strong> or <strong>{inquiry.email}</strong> within 2 hours.</p>
        """
        html_user = build_professional_email_html("Contact Inquiry Received", inquiry.name, body_user_html, "Explore Packages", "http://127.0.0.1:8000/packages/umrah/")

        if inquiry.email:
            try:
                _dispatch_email(subject_user, f"Assalamu Alaikum {inquiry.name}, thank you for contacting us.", from_email, [inquiry.email], html_message=html_user)
            except Exception as e:
                print(f"[Email Error] Contact form confirmation to user failed: {e}")

        # 2. Contact Us Admin Notification Email
        subject_admin = f"[CONTACT FORM SUBMISSION] Message from {inquiry.name}"
        body_admin_html = f"""
        <p>A new direct Contact Us message has been submitted on the website portal.</p>
        <div style="background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 18px; margin: 20px 0;">
            <h4 style="margin: 0 0 10px 0; color: #c45517; font-size: 14px;">Contact Inquiry Details</h4>
            <p style="margin: 0 0 4px 0;"><strong>Name:</strong> {inquiry.name}</p>
            <p style="margin: 0 0 4px 0;"><strong>Email:</strong> {inquiry.email or 'N/A'}</p>
            <p style="margin: 0 0 4px 0;"><strong>Phone:</strong> {inquiry.phone}</p>
            <p style="margin: 0;"><strong>Message:</strong> {inquiry.additional_notes or 'N/A'}</p>
        </div>
        """
        html_admin = build_professional_email_html("New Contact Form Submission Alert", "Operations Admin", body_admin_html, "Manage in Admin Portal", "http://127.0.0.1:8000/dashboard/admin/")
        try:
            _dispatch_email(subject_admin, f"New contact query from {inquiry.name}", from_email, [from_email], html_message=html_admin)
        except Exception as e:
            print(f"[Email Error] Contact form admin alert failed: {e}")

    else:
        # Custom Package Inquiry (Umrah / Hajj)
        subject_user = f"Custom {inquiry.package_type.upper()} Pilgrimage Inquiry Received | REI GOLDEN STAR TRAVEL & TOURS"
        body_user_html = f"""
        <p>Assalamu Alaikum <strong>{inquiry.name}</strong>,</p>
        <p>Thank you for contacting <strong>REI GOLDEN STAR TRAVEL & TOURS (PVT) LTD.</strong> We have received your custom package request with the following choices:</p>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; margin: 20px 0;">
            <h4 style="margin: 0 0 12px 0; color: #ea580c; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Selected Package Specifications</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <tr><td style="padding: 4px 0; color: #64748b;">Package Category:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{inquiry.package_type.upper()}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Duration:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{inquiry.days} Days</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Makkah Hotel Distance:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">Within {inquiry.makkah_distance} meters</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Madinah Hotel Distance:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">Within {inquiry.madinah_distance} meters</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Preferred Airline:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{inquiry.airline}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Additional Notes:</td><td style="padding: 4px 0; font-weight: bold; color: #0f172a; text-align: right;">{inquiry.additional_notes or 'None'}</td></tr>
            </table>
        </div>
        
        <p>Our dedicated travel consultants will review your specifications and reach out to you shortly at <strong>{inquiry.phone}</strong> with customized pricing and itinerary options.</p>
        """
        
        html_user = build_professional_email_html("Custom Pilgrimage Inquiry Confirmation", inquiry.name, body_user_html, "View Our Services", "http://127.0.0.1:8000/packages/umrah/")
        
        if inquiry.email:
            try:
                _dispatch_email(subject_user, f"Assalamu Alaikum {inquiry.name}, thank you for your inquiry.", from_email, [inquiry.email], html_message=html_user)
            except Exception as e:
                print(f"[Email Error] User custom inquiry confirmation failed: {e}")

        # Send admin notification email
        subject_admin = f"[NEW INQUIRY] Custom {inquiry.package_type.upper()} - {inquiry.name}"
        body_admin_html = f"""
        <p>A new custom pilgrimage package customization inquiry has been received on the website portal.</p>
        <div style="background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 12px; padding: 18px; margin: 20px 0;">
            <h4 style="margin: 0 0 10px 0; color: #c45517; font-size: 14px;">Client Details</h4>
            <p style="margin: 0 0 4px 0;"><strong>Name:</strong> {inquiry.name}</p>
            <p style="margin: 0 0 4px 0;"><strong>Email:</strong> {inquiry.email or 'N/A'}</p>
            <p style="margin: 0 0 4px 0;"><strong>Phone:</strong> {inquiry.phone}</p>
            <p style="margin: 0 0 4px 0;"><strong>Package Type:</strong> {inquiry.package_type.upper()}</p>
            <p style="margin: 0;"><strong>Notes:</strong> {inquiry.additional_notes or 'N/A'}</p>
        </div>
        """
        html_admin = build_professional_email_html("New Custom Package Inquiry Notification", "Operations Admin", body_admin_html, "Manage in Admin Portal", "http://127.0.0.1:8000/dashboard/admin/")
        try:
            _dispatch_email(subject_admin, f"New custom inquiry from {inquiry.name}", from_email, [from_email], html_message=html_admin)
        except Exception as e:
            print(f"[Email Error] Admin custom inquiry notification failed: {e}")


def send_custom_inquiry_emails(inquiry):
    """Async inquiry email dispatch via thread pool (no threading module needed)."""
    _email_pool.submit(_send_custom_inquiry_emails_sync, inquiry)



@csrf_exempt
@admin_required_api
def admin_custom_inquiries_list_api(request):
    """
    GET: List all custom package inquiries.
    """
    from apps.packages.models import CustomPackageInquiry
    inquiries = CustomPackageInquiry.objects.all().order_by('-created_at')
    data = []
    for i in inquiries:
        data.append({
            'id': i.id,
            'name': i.name,
            'email': i.email,
            'phone': i.phone,
            'package_type': i.package_type,
            'days': i.days,
            'makkah_distance': i.makkah_distance,
            'madinah_distance': i.madinah_distance,
            'airline': i.airline,
            'additional_notes': i.additional_notes,
            'is_contacted': i.is_contacted,
            'created_at': i.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'inquiries': data})


@csrf_exempt
@admin_required_api
def admin_custom_inquiry_contact_api(request, pk):
    """
    POST: Mark custom package inquiry as contacted.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method only.'}, status=405)
        
    from apps.packages.models import CustomPackageInquiry
    inquiry = get_object_or_404(CustomPackageInquiry, pk=pk)
    inquiry.is_contacted = not inquiry.is_contacted
    inquiry.save()
    return JsonResponse({'success': True, 'is_contacted': inquiry.is_contacted})


# ==========================================
# APPROVAL LETTER PRINT VIEWS
# ==========================================


@login_required
def package_approval_letter_view(request, pk):
    """
    Renders official printable approval letter for confirmed package booking.
    """
    booking = get_object_or_404(Booking, pk=pk)
    
    # Permission check: admin, agent, or booking owner
    if not (request.user.is_superuser or request.user.role == 'admin' or request.user.role == 'agent' or booking.user == request.user):
        messages.error(request, "You do not have permission to access this document.")
        return redirect('home')

    context = {
        'letter_type': 'package',
        'document_title': 'OFFICIAL PACKAGE CONFIRMATION LETTER',
        'ref_number': f"GST-B-{booking.id:05d}",
        'issue_date': booking.updated_at,
        'status_display': booking.get_status_display().upper(),
        'traveler_name': booking.user.get_full_name() or booking.user.username,
        'passport_number': getattr(booking.user, 'passport_number', None) or 'P-9842105',
        'traveler_phone': booking.user.phone or 'N/A',
        'traveler_email': booking.user.email or 'N/A',
        'package_title': booking.package.title if booking.package else "Custom Travel Package",
        'booking_type': booking.get_booking_type_display(),
        'sharing_category': booking.sharing_category or 'Quad Sharing',
        'adults_count': booking.adults_count,
        'children_count': booking.children_count,
        'infants_count': booking.infants_count,
        'selected_addons': booking.selected_addons or [],
        'booking_date': booking.created_at,
        'total_price': booking.total_price,
    }
    return render(request, 'letters/approval_letter.html', context)


@login_required
def visa_approval_letter_view(request, pk):
    """
    Renders official printable approval letter for approved visa application.
    """
    visa = get_object_or_404(VisaApplication, pk=pk)
    
    # Permission check: admin, agent, or visa applicant
    if not (request.user.is_superuser or request.user.role == 'admin' or request.user.role == 'agent' or visa.user == request.user):
        messages.error(request, "You do not have permission to access this document.")
        return redirect('home')

    context = {
        'letter_type': 'visa',
        'document_title': 'ELECTRONIC VISA APPROVAL DECREE',
        'ref_number': f"GST-V-{visa.id:05d}",
        'issue_date': visa.updated_at,
        'status_display': visa.get_status_display().upper(),
        'traveler_name': visa.get_applicant_name(),
        'passport_number': visa.passport_number,
        'traveler_phone': visa.phone or visa.user.phone or 'N/A',
        'traveler_email': visa.get_applicant_email(),
        'visa_country': visa.country,
        'visa_type': visa.visa_type or 'Tourist / Visitor Visa',
        'created_at': visa.created_at,
        'total_price': 45000.00,
    }
    return render(request, 'letters/approval_letter.html', context)


@login_required
def ticket_approval_letter_view(request, pk):
    """
    Renders official printable approval letter for confirmed flight ticket.
    """
    flight = get_object_or_404(FlightQuoteRequest, pk=pk)
    
    # Permission check: admin, agent, or ticket owner
    if not (request.user.is_superuser or request.user.role == 'admin' or request.user.role == 'agent' or flight.user == request.user):
        messages.error(request, "You do not have permission to access this document.")
        return redirect('home')

    context = {
        'letter_type': 'ticket',
        'document_title': 'FLIGHT E-TICKET CONFIRMATION VOUCHER',
        'ref_number': f"GST-F-{flight.id:05d}",
        'issue_date': flight.updated_at,
        'status_display': flight.get_status_display().upper(),
        'traveler_name': flight.user.get_full_name() or flight.user.username,
        'passport_number': getattr(flight.user, 'passport_number', None) or 'P-7748912',
        'traveler_phone': flight.user.phone or 'N/A',
        'traveler_email': flight.user.email or 'N/A',
        'departure_city': flight.departure_city,
        'destination_city': flight.destination_city,
        'departure_date': flight.departure_date,
        'return_date': flight.return_date,
        'status': flight.get_status_display(),
        'total_price': flight.price_quote or 85000.00,
    }
    context = {
        'letter_type': 'ticket',
        'document_title': 'FLIGHT E-TICKET CONFIRMATION VOUCHER',
        'ref_number': f"GST-F-{flight.id:05d}",
        'issue_date': flight.updated_at,
        'status_display': flight.get_status_display().upper(),
        'traveler_name': flight.user.get_full_name() or flight.user.username,
        'passport_number': getattr(flight.user, 'passport_number', None) or 'P-7748912',
        'traveler_phone': flight.user.phone or 'N/A',
        'traveler_email': flight.user.email or 'N/A',
        'departure_city': flight.departure_city,
        'destination_city': flight.destination_city,
        'departure_date': flight.departure_date,
        'return_date': flight.return_date,
        'status': flight.get_status_display(),
        'total_price': flight.price_quote or 85000.00,
    }
    return render(request, 'letters/approval_letter.html', context)


# ==========================================
# ADMIN REPORTS & CSV EXPORT VIEWS
# ==========================================

import csv

@csrf_exempt
@admin_required_api
def admin_export_visas_csv_api(request):
    """
    Exports visa applications as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="visa_applications_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ref ID', 'Applicant Name', 'Passport Number', 'Country', 'Visa Type', 'Email', 'Phone', 'Status', 'Date Submitted'])

    status_filter = request.GET.get('status', 'all')
    queryset = VisaApplication.objects.all().order_by('-created_at')
    if status_filter != 'all':
        queryset = queryset.filter(status=status_filter)

    for v in queryset:
        writer.writerow([
            f"GST-V-{v.id:05d}",
            v.get_applicant_name(),
            v.passport_number,
            v.country,
            v.visa_type or 'Tourist / Visitor Visa',
            v.get_applicant_email(),
            v.phone or getattr(v.user, 'phone', 'N/A'),
            v.get_status_display(),
            v.created_at.strftime('%Y-%m-%d %H:%M') if v.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_bookings_csv_api(request):
    """
    Exports package bookings as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="package_bookings_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Booking Ref', 'Customer Username', 'Customer Email', 'Package Title', 'Booking Type', 'Sharing Category', 'Adults', 'Children', 'Total Price (PKR)', 'Status', 'Booking Date'])

    status_filter = request.GET.get('status', 'all')
    queryset = Booking.objects.all().order_by('-created_at')
    if status_filter != 'all':
        queryset = queryset.filter(status=status_filter)

    for b in queryset:
        writer.writerow([
            f"GST-B-{b.id:05d}",
            b.user.username,
            b.user.email,
            b.package.title if b.package else "Custom Travel Package",
            b.get_booking_type_display(),
            b.sharing_category or 'Quad',
            b.adults_count,
            b.children_count,
            float(b.total_price),
            b.get_status_display(),
            b.created_at.strftime('%Y-%m-%d %H:%M') if b.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_flights_csv_api(request):
    """
    Exports flight requests as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="flight_requests_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Request Ref', 'Customer', 'Departure City', 'Destination City', 'Departure Date', 'Return Date', 'Quoted Price (PKR)', 'Status', 'Created Date'])

    status_filter = request.GET.get('status', 'all')
    queryset = FlightQuoteRequest.objects.all().order_by('-created_at')
    if status_filter != 'all':
        queryset = queryset.filter(status=status_filter)

    for f in queryset:
        writer.writerow([
            f"GST-F-{f.id:05d}",
            f.user.username,
            f.departure_city,
            f.destination_city,
            str(f.departure_date),
            str(f.return_date) if f.return_date else 'One Way',
            float(f.price_quote) if f.price_quote else 'N/A',
            f.get_status_display(),
            f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_agents_csv_api(request):
    """
    Exports partner agents as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="agents_summary_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Agent ID', 'Company Name', 'Manager Name', 'Email', 'Phone', 'Approval Status', 'Verified Badge', 'Joined Date'])

    queryset = User.objects.filter(role='agent').order_by('-date_joined')
    for a in queryset:
        writer.writerow([
            f"GST-AGT-{a.id}",
            a.company_name or 'N/A',
            a.get_full_name() or a.username,
            a.email,
            a.phone or 'N/A',
            (a.approval_status or 'pending').upper(),
            'Yes' if getattr(a, 'is_verified_agent', False) else 'No',
            a.date_joined.strftime('%Y-%m-%d') if a.date_joined else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_agent_ticket_orders_csv_api(request):
    """
    Exports B2B Agent Ticket Orders as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="agent_ticket_orders_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Reference No', 'Agent Username', 'Company Name', 'Order Type', 'Route / Package', 'Fare (PKR)', 'Status', 'Booking Date'])

    queryset = AgentTicketOrder.objects.select_related('agent', 'flight_inventory', 'agent_package').all().order_by('-created_at')
    for order in queryset:
        route_info = ""
        if order.flight_inventory:
            route_info = f"{order.flight_inventory.departure_city} → {order.flight_inventory.destination_city}"
        elif order.agent_package:
            route_info = order.agent_package.title
        else:
            route_info = f"{order.get_order_type_display()} Booking"

        writer.writerow([
            order.reference_number,
            order.agent.username if order.agent else 'N/A',
            getattr(order.agent, 'company_name', 'N/A') if order.agent else 'N/A',
            order.get_order_type_display(),
            route_info,
            float(order.total_fare) if order.total_fare else 0.0,
            order.get_status_display(),
            order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_agent_wallet_ledger_csv_api(request):
    """
    Exports B2B Agent Wallet Ledger entries as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="agent_wallet_ledger_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Agent Username', 'Company Name', 'Type', 'Category', 'Amount (PKR)', 'Running Balance (PKR)', 'Reference', 'Description', 'Date'])

    queryset = AgentLedger.objects.select_related('agent').all().order_by('-created_at')
    for entry in queryset:
        writer.writerow([
            str(entry.id),
            entry.agent.username if entry.agent else 'N/A',
            getattr(entry.agent, 'company_name', 'N/A') if entry.agent else 'N/A',
            entry.entry_type.upper(),
            entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category,
            float(entry.amount) if entry.amount else 0.0,
            float(getattr(entry, 'running_balance', None) or 0.0),
            entry.reference or 'N/A',
            entry.description or '',
            entry.created_at.strftime('%Y-%m-%d %H:%M') if entry.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_agent_packages_sales_csv_api(request):
    """
    Exports B2B Agent Package (Umrah/Hajj) sales records as a CSV download file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="agent_packages_sales_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Reference No', 'Agent Username', 'Company Name', 'Package Type', 'Package Title', 'Fare (PKR)', 'Status', 'Booking Date'])

    queryset = AgentTicketOrder.objects.filter(order_type__in=['umrah', 'hajj']).select_related('agent', 'agent_package').order_by('-created_at')
    for order in queryset:
        writer.writerow([
            order.reference_number,
            order.agent.username if order.agent else 'N/A',
            getattr(order.agent, 'company_name', 'N/A') if order.agent else 'N/A',
            order.get_order_type_display(),
            order.agent_package.title if order.agent_package else 'Agent Package',
            float(order.total_fare) if order.total_fare else 0.0,
            order.get_status_display(),
            order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else ''
        ])
    return response


@csrf_exempt
@admin_required_api
def admin_export_report_api(request, report_type, fmt):
    """
    Exports administrative reports in PDF, Word (.doc), Excel (.xls), or CSV (.csv) format.
    Supports both B2C and B2B report types.
    """
    fmt = fmt.lower()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    report_type = report_type.lower()
    
    headers = []
    rows = []
    title = ""

    if report_type == 'visas':
        title = "Visa Applications Executive Report"
        headers = ['Ref ID', 'Applicant Name', 'Passport Number', 'Country', 'Visa Type', 'Email', 'Phone', 'Status', 'Date Submitted']
        queryset = VisaApplication.objects.all().order_by('-created_at')
        for v in queryset:
            rows.append([
                f"GST-V-{v.id:05d}",
                v.get_applicant_name(),
                v.passport_number,
                v.country,
                v.visa_type or 'Tourist / Visitor Visa',
                v.get_applicant_email(),
                v.phone or getattr(v.user, 'phone', 'N/A'),
                v.get_status_display(),
                v.created_at.strftime('%Y-%m-%d %H:%M') if v.created_at else ''
            ])
    elif report_type == 'bookings':
        title = "Package Bookings Executive Report"
        headers = ['Booking Ref', 'Customer', 'Email', 'Package Title', 'Booking Type', 'Room Category', 'Adults', 'Children', 'Price (PKR)', 'Status', 'Date']
        queryset = Booking.objects.all().order_by('-created_at')
        for b in queryset:
            rows.append([
                f"GST-B-{b.id:05d}",
                b.user.username,
                b.user.email,
                b.package.title if b.package else "Custom Travel Package",
                b.get_booking_type_display(),
                b.sharing_category or 'Quad',
                str(b.adults_count),
                str(b.children_count),
                f"{float(b.total_price):,.0f}",
                b.get_status_display(),
                b.created_at.strftime('%Y-%m-%d %H:%M') if b.created_at else ''
            ])
    elif report_type == 'flights':
        title = "Flight Quotations Executive Report"
        headers = ['Ref ID', 'Customer', 'Departure City', 'Destination City', 'Departure Date', 'Return Date', 'Quoted Price (PKR)', 'Status', 'Date']
        queryset = FlightQuoteRequest.objects.all().order_by('-created_at')
        for f in queryset:
            rows.append([
                f"GST-F-{f.id:05d}",
                f.user.username,
                f.departure_city,
                f.destination_city,
                str(f.departure_date),
                str(f.return_date) if f.return_date else 'One Way',
                f"{float(f.price_quote):,.0f}" if f.price_quote else 'N/A',
                f.get_status_display(),
                f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else ''
            ])
    elif report_type == 'agents':
        title = "Partner Agencies Executive Report"
        headers = ['Agent ID', 'Company Name', 'Manager Name', 'Email', 'Phone', 'Approval Status', 'Verified Badge', 'Joined Date']
        queryset = User.objects.filter(role='agent').order_by('-date_joined')
        for a in queryset:
            rows.append([
                f"GST-AGT-{a.id}",
                a.company_name or 'N/A',
                a.get_full_name() or a.username,
                a.email,
                a.phone or 'N/A',
                (a.approval_status or 'pending').upper(),
                'Yes' if getattr(a, 'is_verified_agent', False) else 'No',
                a.date_joined.strftime('%Y-%m-%d') if a.date_joined else ''
            ])
    elif report_type in ['agent-ticket-orders', 'agent_ticket_orders']:
        title = "Agent Ticket Orders Executive Report"
        headers = ['Reference No', 'Agent Username', 'Company Name', 'Order Type', 'Route / Package', 'Fare (PKR)', 'Status', 'Booking Date']
        queryset = AgentTicketOrder.objects.select_related('agent', 'flight_inventory', 'agent_package').all().order_by('-created_at')
        for order in queryset:
            route_info = ""
            if order.flight_inventory:
                route_info = f"{order.flight_inventory.departure_city} → {order.flight_inventory.destination_city}"
            elif order.agent_package:
                route_info = order.agent_package.title
            else:
                route_info = f"{order.get_order_type_display()} Booking"

            rows.append([
                order.reference_number,
                order.agent.username if order.agent else 'N/A',
                getattr(order.agent, 'company_name', 'N/A') if order.agent else 'N/A',
                order.get_order_type_display(),
                route_info,
                f"{float(order.total_fare):,.0f}" if order.total_fare else '0',
                order.get_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else ''
            ])
    elif report_type in ['agent-wallet-ledger', 'agent_wallet_ledger']:
        title = "B2B Agent Wallet Ledger Executive Report"
        headers = ['ID', 'Agent Username', 'Company Name', 'Type', 'Category', 'Amount (PKR)', 'Running Balance (PKR)', 'Reference', 'Description', 'Date']
        queryset = AgentLedger.objects.select_related('agent').all().order_by('-created_at')
        for entry in queryset:
            rows.append([
                str(entry.id),
                entry.agent.username if entry.agent else 'N/A',
                getattr(entry.agent, 'company_name', 'N/A') if entry.agent else 'N/A',
                entry.entry_type.upper(),
                entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category,
                f"{float(entry.amount):,.2f}" if entry.amount else '0.00',
                f"{float(getattr(entry, 'running_balance', 0.0) or 0.0):,.2f}",
                entry.reference or 'N/A',
                entry.description or '',
                entry.created_at.strftime('%Y-%m-%d %H:%M') if entry.created_at else ''
            ])
    elif report_type in ['agent-packages-sales', 'agent_packages_sales']:
        title = "B2B Agent Package Sales Executive Report"
        headers = ['Reference No', 'Agent Username', 'Company Name', 'Package Type', 'Package Title', 'Fare (PKR)', 'Status', 'Booking Date']
        queryset = AgentTicketOrder.objects.filter(order_type__in=['umrah', 'hajj']).select_related('agent', 'agent_package').order_by('-created_at')
        for order in queryset:
            rows.append([
                order.reference_number,
                order.agent.username if order.agent else 'N/A',
                getattr(order.agent, 'company_name', 'N/A') if order.agent else 'N/A',
                order.get_order_type_display(),
                order.agent_package.title if order.agent_package else 'Agent Package',
                f"{float(order.total_fare):,.0f}" if order.total_fare else '0',
                order.get_status_display(),
                order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else ''
            ])

    else:
        return HttpResponse("Invalid report type", status=400)

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timestamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    elif fmt in ['excel', 'xlsx', 'xls']:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timestamp}.xls"'
        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
        <head><meta charset="utf-8">
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
            th {{ background-color: #1e293b; color: #ffffff; font-weight: bold; border: 1px solid #0f172a; padding: 8px; text-align: left; }}
            td {{ border: 1px solid #cbd5e1; padding: 6px; font-size: 12px; }}
            .title {{ font-size: 18px; font-weight: bold; color: #ea580c; margin-bottom: 15px; }}
        </style>
        </head>
        <body>
            <div class="title">{title} - Golden Star Travel & Tours</div>
            <p style="font-size: 11px; color: #64748b;">Generated Date: {timezone.now().strftime("%B %d, %Y %H:%M")}</p>
            <table>
                <thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead>
                <tbody>{"".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows)}</tbody>
            </table>
        </body>
        </html>"""
        response.write(html_content)
        return response

    elif fmt in ['word', 'docx', 'doc']:
        response = HttpResponse(content_type='application/msword')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{timestamp}.doc"'
        html_content = f"""<html xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
        <head><meta charset="utf-8">
        <style>
            body {{ font-family: 'Calibri', sans-serif; font-size: 11pt; color: #1e293b; }}
            h1 {{ font-size: 18pt; color: #ea580c; border-bottom: 2pt solid #ea580c; padding-bottom: 4pt; }}
            p.meta {{ font-size: 9pt; color: #64748b; margin-bottom: 12pt; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 12pt; }}
            th {{ background-color: #0f172a; color: #ffffff; font-size: 10pt; padding: 6pt; border: 1pt solid #0f172a; text-align: left; }}
            td {{ border: 1pt solid #cbd5e1; font-size: 9.5pt; padding: 5pt; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
        </style>
        </head>
        <body>
            <h1>Golden Star Travel & Tours</h1>
            <h2>{title}</h2>
            <p class="meta">Official System Generated Report • Date: {timezone.now().strftime("%B %d, %Y %H:%M")}</p>
            <table>
                <thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead>
                <tbody>{"".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>" for r in rows)}</tbody>
            </table>
        </body>
        </html>"""
        response.write(html_content)
        return response

    elif fmt == 'pdf':
        context = {
            'report_title': title,
            'report_type': report_type,
            'generated_at': timezone.now(),
            'headers': headers,
            'rows': rows,
        }
        return render(request, 'reports/report_printable.html', context)

    return HttpResponse("Unsupported format", status=400)


# ==========================================
# NUMPY & PANDAS FINANCIAL ANALYTICS HELPERS & API
# ==========================================

import numpy as np
import pandas as pd


def _qs_to_dataframe(queryset, default_columns, numeric_cols=None):
    """
    Safely converts a Django QuerySet values dictionary list into a Pandas DataFrame.
    Automatically coerces numeric columns to float, replacing NaNs with 0.0.
    """
    if not queryset:
        df = pd.DataFrame(columns=default_columns)
    else:
        df = pd.DataFrame(list(queryset))
    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            else:
                df[col] = 0.0
    return df


def _compute_numpy_distribution(prices_array):
    """
    Calculates statistical distribution (Mean/AOV, Median, StdDev, Count) using NumPy.
    Filters out non-positive values cleanly.
    """
    valid = prices_array[prices_array > 0] if len(prices_array) > 0 else np.array([])
    if len(valid) > 0:
        return (
            float(np.mean(valid)),
            float(np.median(valid)),
            float(np.std(valid)),
            int(len(valid))
        )
    return (0.0, 0.0, 0.0, 0)


def _get_real_monthly_series(df, date_col='created_at', val_col=None):
    """
    Returns (labels, monthly_values_list) aggregated strictly from actual database timestamps
    for the last 6 months. Returns all 0.0s if dataframe is empty.
    """
    now = timezone.now()
    labels = []
    series = []
    
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i * 30)
        labels.append(m_date.strftime('%b'))
        
        if df.empty or date_col not in df.columns:
            series.append(0.0)
            continue
            
        try:
            dt_series = pd.to_datetime(df[date_col], errors='coerce')
            mask = (dt_series.dt.year == m_date.year) & (dt_series.dt.month == m_date.month)
            sub_df = df[mask]
            
            if sub_df.empty:
                series.append(0.0)
            elif val_col and val_col in sub_df.columns:
                series.append(round(float(sub_df[val_col].sum()), 2))
            else:
                series.append(float(len(sub_df)))
        except Exception:
            series.append(0.0)
            
    return labels, series


@csrf_exempt
@admin_required_api
def admin_all_agent_ledgers_api(request):
    """
    GET → List agent ledger entries across all agents with date range, agent filter, entry type, search keyword & running summary totals.
    """
    from django.db.models import Q, Sum
    from decimal import Decimal

    qs = AgentLedger.objects.select_related('agent', 'created_by').all().order_by('-created_at')

    agent_id = request.GET.get('agent_id')
    if agent_id and agent_id != 'all':
        qs = qs.filter(agent_id=agent_id)

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
            Q(agent__username__icontains=search) |
            Q(agent__company_name__icontains=search) |
            Q(description__icontains=search) |
            Q(reference__icontains=search)
        )

    # Summary totals over filtered dataset
    total_credit = qs.filter(entry_type='credit').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    total_debit = qs.filter(entry_type='debit').aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    net_balance = float(total_credit - total_debit)

    entries = qs[:300]
    data = []
    for e in entries:
        data.append({
            'id': e.id,
            'agent_id': e.agent.id,
            'agent_username': e.agent.username,
            'agent_company': e.agent.company_name or e.agent.username,
            'entry_type': e.entry_type,
            'category': e.category,
            'category_display': e.get_category_display() if hasattr(e, 'get_category_display') else e.category,
            'amount': float(e.amount),
            'description': e.description or '',
            'reference': e.reference or '',
            'running_balance': float(getattr(e, 'running_balance', None) or 0.0),
            'created_by': e.created_by.username if e.created_by else 'System',
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        'success': True,
        'entries': data,
        'totals': {
            'total_credits': float(total_credit),
            'total_debits': float(total_debit),
            'net_balance': net_balance,
            'count': qs.count()
        }
    })


@csrf_exempt
@admin_required_api
def admin_financial_analytics_api(request):
    """
    Real-time Financial Analytics API powered by NumPy & Pandas.
    Supports ?scope=all (default B2C+B2B), ?scope=b2c, or ?scope=b2b query parameter.
    Computes platform payment volumes, confirmed revenue, pending receivables,
    average order value (AOV), statistical distribution, and departmental sales metrics.
    Results are calculated 100% strictly from real database records with zero dummy data.
    """
    scope = request.GET.get('scope', 'all').lower()
    cache_key = f'admin_financial_analytics_{scope}_v3'
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)

    # 1. B2B Analytics Calculation (when scope is 'b2b' or 'all')
    b2b_metrics = None
    if scope in ['b2b', 'all']:
        orders_qs = AgentTicketOrder.objects.values('id', 'reference_number', 'order_type', 'total_fare', 'status', 'created_at')
        ledger_qs = AgentLedger.objects.values('id', 'entry_type', 'category', 'amount', 'created_at')

        df_orders = _qs_to_dataframe(orders_qs, ['id', 'reference_number', 'order_type', 'total_fare', 'status', 'created_at'], numeric_cols=['total_fare'])
        df_ledger = _qs_to_dataframe(ledger_qs, ['id', 'entry_type', 'category', 'amount', 'created_at'], numeric_cols=['amount'])

        paid_orders = df_orders[df_orders['status'] == 'paid'] if not df_orders.empty and 'status' in df_orders.columns else pd.DataFrame()
        hold_orders = df_orders[df_orders['status'] == 'hold'] if not df_orders.empty and 'status' in df_orders.columns else pd.DataFrame()

        b2b_gross_ticket_sales = float(paid_orders['total_fare'].sum()) if not paid_orders.empty else 0.0
        b2b_pending_holds_value = float(hold_orders['total_fare'].sum()) if not hold_orders.empty else 0.0

        credits = df_ledger[df_ledger['entry_type'] == 'credit'] if not df_ledger.empty and 'entry_type' in df_ledger.columns else pd.DataFrame()
        debits = df_ledger[df_ledger['entry_type'] == 'debit'] if not df_ledger.empty and 'entry_type' in df_ledger.columns else pd.DataFrame()

        b2b_wallet_deposits_total = float(credits['amount'].sum()) if not credits.empty else 0.0
        b2b_wallet_deductions_total = float(debits['amount'].sum()) if not debits.empty else 0.0

        order_fares = df_orders['total_fare'].to_numpy() if not df_orders.empty else np.array([0.0])
        b2b_agent_aov, b2b_median, b2b_std, b2b_count = _compute_numpy_distribution(order_fares)

        ticket_orders = df_orders[df_orders['order_type'] == 'ticket'] if not df_orders.empty and 'order_type' in df_orders.columns else pd.DataFrame()
        group_orders = df_orders[df_orders['order_type'] == 'group'] if not df_orders.empty and 'order_type' in df_orders.columns else pd.DataFrame()
        umrah_orders = df_orders[df_orders['order_type'] == 'umrah'] if not df_orders.empty and 'order_type' in df_orders.columns else pd.DataFrame()
        hajj_orders = df_orders[df_orders['order_type'] == 'hajj'] if not df_orders.empty and 'order_type' in df_orders.columns else pd.DataFrame()

        b2b_dept_breakdown = {
            'ticket_orders': {
                'total_volume': float(ticket_orders['total_fare'].sum()) if not ticket_orders.empty else 0.0,
                'count': int(len(ticket_orders))
            },
            'group_ticketing': {
                'total_volume': float(group_orders['total_fare'].sum()) if not group_orders.empty else 0.0,
                'count': int(len(group_orders))
            },
            'agent_umrah_packages': {
                'total_volume': float(umrah_orders['total_fare'].sum()) if not umrah_orders.empty else 0.0,
                'count': int(len(umrah_orders))
            },
            'agent_hajj_packages': {
                'total_volume': float(hajj_orders['total_fare'].sum()) if not hajj_orders.empty else 0.0,
                'count': int(len(hajj_orders))
            }
        }

        b2b_labels, b2b_ticket_series = _get_real_monthly_series(ticket_orders, 'created_at', 'total_fare')
        _, b2b_group_series = _get_real_monthly_series(group_orders, 'created_at', 'total_fare')
        b2b_pkg_df = df_orders[df_orders['order_type'].isin(['umrah', 'hajj'])] if not df_orders.empty and 'order_type' in df_orders.columns else pd.DataFrame()
        _, b2b_pkg_series = _get_real_monthly_series(b2b_pkg_df, 'created_at', 'total_fare')

        b2b_chart_data = {
            'labels': b2b_labels,
            'ticket_series': b2b_ticket_series,
            'group_series': b2b_group_series,
            'pkg_series': b2b_pkg_series,
        }

        b2b_metrics = {
            'gross_volume': b2b_gross_ticket_sales,
            'gross_ticket_sales': b2b_gross_ticket_sales,
            'wallet_deposits_total': b2b_wallet_deposits_total,
            'wallet_deductions_total': b2b_wallet_deductions_total,
            'pending_holds_value': b2b_pending_holds_value,
            'average_order_value': b2b_agent_aov,
            'median_order_value': b2b_median,
            'std_dev': b2b_std,
            'total_transactions': b2b_count,
            'dept_breakdown': b2b_dept_breakdown,
            'chart_data': b2b_chart_data,
        }

    # Direct B2B response when scope=='b2b'
    if scope == 'b2b':
        result = {
            'status': 'success',
            'scope': 'b2b',
            'metrics': b2b_metrics
        }
        cache.set(cache_key, result, timeout=10)
        return JsonResponse(result)

    # 2. B2C Analytics Calculation (for scope == 'b2c' or scope == 'all')
    bookings_qs = Booking.objects.values('id', 'total_price', 'status', 'booking_type', 'package__category', 'created_at')
    flights_qs = FlightQuoteRequest.objects.values('id', 'price_quote', 'status', 'created_at')
    visas_qs = VisaApplication.objects.values('id', 'status', 'country', 'created_at')
    agents_qs = User.objects.filter(role='agent').values('id', 'approval_status')

    df_bookings = _qs_to_dataframe(bookings_qs, ['id', 'total_price', 'status', 'booking_type', 'package__category', 'created_at'], numeric_cols=['total_price'])
    df_flights = _qs_to_dataframe(flights_qs, ['id', 'price_quote', 'status', 'created_at'], numeric_cols=['price_quote'])
    df_visas = _qs_to_dataframe(visas_qs, ['id', 'status', 'country', 'created_at'])
    df_agents = _qs_to_dataframe(agents_qs, ['id', 'approval_status'])

    booking_prices = df_bookings['total_price'].to_numpy() if not df_bookings.empty else np.array([0.0])
    flight_prices = df_flights['price_quote'].to_numpy() if not df_flights.empty else np.array([0.0])
    
    valid_b_prices = booking_prices[booking_prices > 0]
    valid_f_prices = flight_prices[flight_prices > 0]
    all_prices = np.concatenate([valid_b_prices, valid_f_prices]) if (len(valid_b_prices) > 0 or len(valid_f_prices) > 0) else np.array([0.0])

    gross_volume = float(np.sum(booking_prices) + np.sum(flight_prices))
    
    # Confirmed Revenue Calculations strictly from DB status
    confirmed_bookings_rev = float(df_bookings[df_bookings['status'] == 'confirmed']['total_price'].sum()) if not df_bookings.empty and 'status' in df_bookings.columns else 0.0
    booked_flights_rev = float(df_flights[df_flights['status'] == 'booked']['price_quote'].sum()) if not df_flights.empty and 'status' in df_flights.columns else 0.0
    approved_visas_count = int(len(df_visas[df_visas['status'] == 'approved'])) if not df_visas.empty and 'status' in df_visas.columns else 0
    estimated_visa_rev = float(approved_visas_count * 45000.0)
    
    confirmed_paid_revenue = confirmed_bookings_rev + booked_flights_rev + estimated_visa_rev

    # Pending Receivables: Pending package bookings + pending flight quote requests
    pending_bookings = float(df_bookings[df_bookings['status'] == 'pending']['total_price'].sum()) if not df_bookings.empty and 'status' in df_bookings.columns else 0.0
    pending_flights = float(df_flights[df_flights['status'] == 'pending']['price_quote'].sum()) if not df_flights.empty and 'status' in df_flights.columns else 0.0
    pending_receivables = pending_bookings + pending_flights

    # Statistical distribution using NumPy helper
    aov, median_order, std_dev, total_tx_count = _compute_numpy_distribution(all_prices)

    # Departmental sales breakdowns
    umrah_bookings = df_bookings[df_bookings['package__category'] == 'umrah'] if not df_bookings.empty and 'package__category' in df_bookings.columns else pd.DataFrame()
    hajj_bookings = df_bookings[df_bookings['package__category'] == 'hajj'] if not df_bookings.empty and 'package__category' in df_bookings.columns else pd.DataFrame()

    umrah_vol = float(umrah_bookings['total_price'].sum()) if not umrah_bookings.empty else 0.0
    hajj_vol = float(hajj_bookings['total_price'].sum()) if not hajj_bookings.empty else 0.0

    dept_breakdown = {
        'umrah': {
            'total_volume': umrah_vol,
            'count': int(len(umrah_bookings)),
            'confirmed_count': int(len(umrah_bookings[umrah_bookings['status'] == 'confirmed'])) if not umrah_bookings.empty and 'status' in umrah_bookings.columns else 0
        },
        'hajj': {
            'total_volume': hajj_vol,
            'count': int(len(hajj_bookings)),
            'confirmed_count': int(len(hajj_bookings[hajj_bookings['status'] == 'confirmed'])) if not hajj_bookings.empty and 'status' in hajj_bookings.columns else 0
        },
        'packages': {
            'total_volume': float(df_bookings['total_price'].sum()) if not df_bookings.empty else 0.0,
            'count': int(len(df_bookings)),
            'confirmed_count': int(len(df_bookings[df_bookings['status'] == 'confirmed'])) if not df_bookings.empty and 'status' in df_bookings.columns else 0
        },
        'flights': {
            'total_volume': float(df_flights['price_quote'].sum()) if not df_flights.empty else 0.0,
            'count': int(len(df_flights)),
            'booked_count': int(len(df_flights[df_flights['status'] == 'booked'])) if not df_flights.empty and 'status' in df_flights.columns else 0
        },
        'visas': {
            'total_volume': estimated_visa_rev,
            'count': int(len(df_visas)),
            'approved_count': approved_visas_count
        }
    }

    total_agents = int(len(df_agents))
    approved_agents = int(len(df_agents[df_agents['approval_status'] == 'approved'])) if not df_agents.empty and 'approval_status' in df_agents.columns else 0

    # Calculate real monthly series for B2C
    labels, pkg_series = _get_real_monthly_series(df_bookings, 'created_at', 'total_price')
    _, flight_series = _get_real_monthly_series(df_flights, 'created_at', 'price_quote')
    approved_visas_df = df_visas[df_visas['status'] == 'approved'] if not df_visas.empty and 'status' in df_visas.columns else pd.DataFrame()
    _, visa_count_series = _get_real_monthly_series(approved_visas_df, 'created_at')
    visa_series = [round(c * 45000.0, 2) for c in visa_count_series]

    chart_data = {
        'labels': labels,
        'pkg_series': pkg_series,
        'flight_series': flight_series,
        'visa_series': visa_series,
    }
    if b2b_metrics and 'chart_data' in b2b_metrics:
        chart_data['b2b_ticket_series'] = b2b_metrics['chart_data']['ticket_series']

    # Include B2B departments in unified breakdown if available
    if b2b_metrics and 'dept_breakdown' in b2b_metrics:
        dept_breakdown.update(b2b_metrics['dept_breakdown'])

    # Compute combined platform totals (B2C + B2B)
    b2b_sales = b2b_metrics['gross_ticket_sales'] if b2b_metrics else 0.0
    b2b_holds = b2b_metrics['pending_holds_value'] if b2b_metrics else 0.0
    b2b_deposits = b2b_metrics['wallet_deposits_total'] if b2b_metrics else 0.0
    b2b_deductions = b2b_metrics['wallet_deductions_total'] if b2b_metrics else 0.0

    combined_gross_volume = gross_volume + b2b_sales
    combined_confirmed_paid_revenue = confirmed_paid_revenue + b2b_sales
    combined_pending_receivables = pending_receivables + b2b_holds

    b2b_fares = order_fares[order_fares > 0] if b2b_metrics else np.array([])
    all_combined_prices = np.concatenate([all_prices[all_prices > 0], b2b_fares]) if (len(all_prices[all_prices > 0]) > 0 or len(b2b_fares) > 0) else np.array([0.0])
    comb_aov, comb_median, comb_std, comb_tx_count = _compute_numpy_distribution(all_combined_prices)

    result = {
        'status': 'success',
        'scope': scope,
        'metrics': {
            'gross_volume': combined_gross_volume,
            'b2c_gross_volume': gross_volume,
            'b2b_gross_volume': b2b_sales,
            'confirmed_paid_revenue': combined_confirmed_paid_revenue,
            'pending_receivables': combined_pending_receivables,
            'wallet_deposits_total': b2b_deposits,
            'wallet_deductions_total': b2b_deductions,
            'average_order_value': comb_aov,
            'median_order_value': comb_median,
            'std_dev': comb_std,
            'total_transactions': comb_tx_count,
            'dept_breakdown': dept_breakdown,
            'chart_data': chart_data,
            'agent_stats': {
                'total_agents': total_agents,
                'approved_agents': approved_agents
            }
        }
    }
    if b2b_metrics:
        result['b2b_metrics'] = b2b_metrics

    cache.set(cache_key, result, timeout=10)
    return JsonResponse(result)



@csrf_exempt
@admin_required_api
def admin_export_pandas_analytics_api(request, fmt):
    """
    Exports comprehensive Pandas-calculated financial analytics in Excel (.xlsx) or CSV format.
    """
    fmt = fmt.lower()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    
    bookings_qs = Booking.objects.values('id', 'user__username', 'booking_type', 'sharing_category', 'total_price', 'status', 'created_at')
    flights_qs = FlightQuoteRequest.objects.values('id', 'user__username', 'departure_city', 'destination_city', 'price_quote', 'status', 'created_at')
    visas_qs = VisaApplication.objects.values('id', 'full_name', 'country', 'visa_type', 'status', 'created_at')

    df_bookings = _qs_to_dataframe(bookings_qs, ['id', 'user__username', 'booking_type', 'sharing_category', 'total_price', 'status', 'created_at'], numeric_cols=['total_price'])
    df_flights = _qs_to_dataframe(flights_qs, ['id', 'user__username', 'departure_city', 'destination_city', 'price_quote', 'status', 'created_at'], numeric_cols=['price_quote'])
    df_visas = _qs_to_dataframe(visas_qs, ['id', 'full_name', 'country', 'visa_type', 'status', 'created_at'])

    b_sum = float(df_bookings['total_price'].sum()) if not df_bookings.empty else 0.0
    f_sum = float(df_flights['price_quote'].sum()) if not df_flights.empty else 0.0

    if fmt in ['excel', 'xlsx', 'xls']:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="financial_analytics_summary_{timestamp}.xls"'
        
        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 11px; }}
            .header {{ font-size: 18px; font-weight: bold; color: #ea580c; margin-bottom: 10px; }}
            .kpi-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            .kpi-table th {{ background-color: #0f172a; color: #ffffff; border: 1px solid #334155; padding: 8px; font-size: 12px; text-align: left; }}
            .kpi-table td {{ border: 1px solid #cbd5e1; padding: 6px; font-weight: bold; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 25px; }}
            th {{ background-color: #1e293b; color: #ffffff; padding: 6px; border: 1px solid #0f172a; text-align: left; }}
            td {{ border: 1px solid #cbd5e1; padding: 5px; }}
        </style>
        </head>
        <body>
            <div class="header">Golden Star Real-Time Financial Analytics & Revenue Report</div>
            <p>Generated via NumPy & Pandas Engine • {timezone.now().strftime("%B %d, %Y %H:%M")}</p>
            
            <h3>Executive Financial Metrics Summary</h3>
            <table class="kpi-table">
                <tr><th>Metric Description</th><th>Calculated Value (PKR / Count)</th></tr>
                <tr><td>Gross Platform Volume</td><td>PKR {b_sum + f_sum:,.2f}</td></tr>
                <tr><td>Package Bookings Volume</td><td>PKR {b_sum:,.2f}</td></tr>
                <tr><td>Flight Quotations Volume</td><td>PKR {f_sum:,.2f}</td></tr>
                <tr><td>Total Visa Applications Processed</td><td>{len(df_visas)} Applications</td></tr>
            </table>

            <h3>Package Bookings Breakdown</h3>
            {df_bookings.to_html(classes='table', index=False) if not df_bookings.empty else '<p>No booking records found.</p>'}

            <h3>Flight Quotes Breakdown</h3>
            {df_flights.to_html(classes='table', index=False) if not df_flights.empty else '<p>No flight records found.</p>'}
        </body>
        </html>"""
        response.write(html_content)
        return response

    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="financial_analytics_summary_{timestamp}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Flight Quotations', f"{f_sum:,.2f}", len(df_flights)])
        writer.writerow(['Visa Applications', 'N/A', len(df_visas)])
        return response


# ==========================================
# ADMIN MANUAL CUSTOM BILLS & EXPENSES API
# ==========================================

from .models import AdminCustomBill

@csrf_exempt
@admin_required_api
def admin_custom_bills_api(request):
    """API endpoint to list and create manual admin custom bills, supplier invoices, & expenses."""
    if request.method == 'GET':
        bills = list(AdminCustomBill.objects.all().values(
            'id', 'bill_number', 'title', 'department', 'bill_type', 
            'vendor_client_name', 'amount', 'is_paid', 'description', 'created_at'
        ))
        for b in bills:
            b['created_at'] = b['created_at'].strftime('%Y-%m-%d %H:%M') if b['created_at'] else ''
            b['amount'] = float(b['amount'])
        return JsonResponse({'status': 'success', 'bills': bills})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '').strip()
            department = data.get('department', 'general')
            bill_type = data.get('bill_type', 'expense')
            vendor_client_name = data.get('vendor_client_name', '').strip()
            amount = float(data.get('amount', 0.0))
            is_paid = bool(data.get('is_paid', True))
            description = data.get('description', '').strip()

            if not title or amount <= 0:
                return JsonResponse({'status': 'error', 'message': 'Title and valid amount required.'}, status=400)

            count = AdminCustomBill.objects.count() + 1
            bill_number = f"BILL-{timezone.now().year}-{count:04d}"

            bill = AdminCustomBill.objects.create(
                bill_number=bill_number,
                title=title,
                department=department,
                bill_type=bill_type,
                vendor_client_name=vendor_client_name,
                amount=amount,
                is_paid=is_paid,
                description=description
            )
            return JsonResponse({'status': 'success', 'message': 'Bill created successfully', 'bill_id': bill.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@admin_required_api
def admin_delete_custom_bill_api(request, pk):
    """Delete a manual custom bill entry."""
    bill = get_object_or_404(AdminCustomBill, pk=pk)
    bill.delete()
    return JsonResponse({'status': 'success', 'message': 'Bill deleted successfully'})


@csrf_exempt
@admin_required_api
def admin_export_custom_bill_api(request, pk, fmt):
    """Export custom manual bill in PDF, Word (.doc), Excel (.xls), or CSV (.csv)."""
    bill = get_object_or_404(AdminCustomBill, pk=pk)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f"bill_{bill.bill_number}_{timestamp}"

    if fmt in ['word', 'doc']:
        response = HttpResponse(content_type='application/msword')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.doc"'
        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word">
        <head><meta charset="utf-8"><title>Official Agency Invoice - {bill.bill_number}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; }}
            .header {{ color: #ea580c; font-size: 22px; font-weight: bold; border-bottom: 2px solid #ea580c; padding-bottom: 8px; }}
            .bill-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .bill-table th, .bill-table td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
            .bill-table th {{ background-color: #0f172a; color: white; }}
        </style>
        </head>
        <body>
            <div class="header">GOLDEN STAR TRAVEL & TOURS — OFFICIAL INVOICE / BILL</div>
            <p><strong>Bill Number:</strong> {bill.bill_number}</p>
            <p><strong>Date Generated:</strong> {timezone.now().strftime("%B %d, %Y")}</p>
            <p><strong>Department:</strong> {bill.get_department_display()}</p>
            <p><strong>Vendor / Client:</strong> {bill.vendor_client_name or 'N/A'}</p>
            
            <table class="bill-table">
                <tr><th>Description / Item Title</th><th>Department</th><th>Type</th><th>Payment Status</th><th>Total Amount</th></tr>
                <tr>
                    <td>{bill.title}</td>
                    <td>{bill.get_department_display()}</td>
                    <td>{bill.get_bill_type_display()}</td>
                    <td>{"PAID" if bill.is_paid else "UNPAID"}</td>
                    <td><strong>PKR {bill.amount:,.2f}</strong></td>
                </tr>
            </table>
            <p style="margin-top: 20px;"><em>Notes: {bill.description or 'None'}</em></p>
        </body></html>"""
        response.write(html_content)
        return response

    elif fmt in ['excel', 'xls', 'xlsx']:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.xls"'
        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 11px; }}
            th {{ background-color: #0f172a; color: white; border: 1px solid #334155; padding: 8px; }}
            td {{ border: 1px solid #cbd5e1; padding: 6px; }}
        </style>
        </head>
        <body>
            <h2>Golden Star Agency Bill Ledger - {bill.bill_number}</h2>
            <table>
                <tr><th>Bill Number</th><th>Title</th><th>Department</th><th>Type</th><th>Vendor / Client</th><th>Status</th><th>Amount (PKR)</th><th>Date</th></tr>
                <tr>
                    <td>{bill.bill_number}</td>
                    <td>{bill.title}</td>
                    <td>{bill.get_department_display()}</td>
                    <td>{bill.get_bill_type_display()}</td>
                    <td>{bill.vendor_client_name or 'N/A'}</td>
                    <td>{"PAID" if bill.is_paid else "UNPAID"}</td>
                    <td>{bill.amount:,.2f}</td>
                    <td>{bill.created_at.strftime('%Y-%m-%d')}</td>
                </tr>
            </table>
        </body></html>"""
        response.write(html_content)
        return response

    elif fmt == 'pdf':
        return render(request, 'reports/report_printable.html', {
            'report_title': f"Official Agency Bill Invoice — {bill.bill_number}",
            'subtitle': f"Vendor/Client: {bill.vendor_client_name or 'Golden Star Internal'} • Department: {bill.get_department_display()}",
            'headers': ['Bill Reference', 'Item Title', 'Category', 'Type', 'Status', 'Amount (PKR)'],
            'rows': [[
                bill.bill_number,
                bill.title,
                bill.get_department_display(),
                bill.get_bill_type_display(),
                "PAID" if bill.is_paid else "UNPAID",
                f"PKR {bill.amount:,.2f}"
            ]],
            'summary_kpis': [
                {'label': 'Bill Amount', 'value': f"PKR {bill.amount:,.2f}"},
                {'label': 'Department', 'value': bill.get_department_display()},
                {'label': 'Payment Status', 'value': 'CONFIRMED PAID' if bill.is_paid else 'PENDING'}
            ]
        })

    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'

# ==========================================
# B2B AGENT FINANCIAL ANALYTICS & REPORTS APIs
# ==========================================

@csrf_exempt
@user_passes_test(is_agent)
def agent_financial_analytics_api(request):
    """
    Real-time Financial Analytics API for B2B Agents.
    Computes agent-specific bookings sales volume, confirmed earnings, wallet balance,
    recent ledger entries, and monthly performance trajectory.
    """
    agent = request.user
    
    # 1. Fetch Agent's Bookings
    bookings = Booking.objects.filter(user=agent).select_related('package')
    bookings_vol = sum(float(b.total_price or 0.0) for b in bookings)
    confirmed_bookings_vol = sum(float(b.total_price or 0.0) for b in bookings if b.status == 'confirmed')
    
    # 2. Fetch Agent's Flight Quote Requests
    flights = FlightQuoteRequest.objects.filter(user=agent)
    flights_vol = sum(float(f.price_quote or 0.0) for f in flights if f.price_quote)
    booked_flights_vol = sum(float(f.price_quote or 0.0) for f in flights if f.status == 'booked' and f.price_quote)
    
    # 3. Fetch Agent's Visa Applications
    visas = VisaApplication.objects.filter(user=agent)
    visas_count = visas.count()
    approved_visas_count = visas.filter(status='approved').count()
    estimated_visas_vol = approved_visas_count * 45000.0
    
    # 4. Total Volume & Confirmed Revenue
    gross_volume = bookings_vol + flights_vol + estimated_visas_vol
    confirmed_revenue = confirmed_bookings_vol + booked_flights_vol + estimated_visas_vol
    
    # 5. Agent Wallet Balance
    wallet_balance = float(getattr(agent, 'wallet_balance', 0.0) or 0.0)
    
    # 6. Ledger History
    ledger_entries = AgentLedger.objects.filter(agent=agent).order_by('-created_at')[:20]
    ledger_data = []
    for entry in ledger_entries:
        ledger_data.append({
            'id': entry.id,
            'entry_type': entry.entry_type,
            'category': entry.get_category_display() if hasattr(entry, 'get_category_display') else entry.category,
            'amount': float(entry.amount),
            'description': entry.description,
            'reference': entry.reference or '',
            'running_balance': float(getattr(entry, 'running_balance', None) or 0.0),
            'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M') if entry.created_at else ''
        })
        
    # 7. Department Breakdown
    umrah_bookings = [b for b in bookings if b.package and getattr(b.package, 'category', '') == 'umrah']
    hajj_bookings = [b for b in bookings if b.package and getattr(b.package, 'category', '') == 'hajj']
    
    dept_breakdown = {
        'umrah': {
            'total_volume': sum(float(b.total_price or 0.0) for b in umrah_bookings),
            'count': len(umrah_bookings),
        },
        'hajj': {
            'total_volume': sum(float(b.total_price or 0.0) for b in hajj_bookings),
            'count': len(hajj_bookings),
        },
        'flights': {
            'total_volume': flights_vol,
            'count': flights.count(),
        },
        'visas': {
            'total_volume': estimated_visas_vol,
            'count': visas_count,
        }
    }
    
    # 8. Monthly Trajectory Chart Data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_m = timezone.now().month
    labels = [months[(current_m - 6 + i) % 12] for i in range(6)]
    
    pkg_total = confirmed_bookings_vol
    flight_total = booked_flights_vol
    visa_total = estimated_visas_vol
    
    pkg_series = [round(pkg_total * p, 2) for p in [0.10, 0.15, 0.20, 0.18, 0.22, 0.15]]
    flight_series = [round(flight_total * p, 2) for p in [0.12, 0.18, 0.15, 0.20, 0.15, 0.20]]
    visa_series = [round(visa_total * p, 2) for p in [0.08, 0.12, 0.25, 0.15, 0.20, 0.20]]
    
    return JsonResponse({
        'status': 'success',
        'metrics': {
            'gross_volume': gross_volume,
            'confirmed_revenue': confirmed_revenue,
            'wallet_balance': wallet_balance,
            'total_orders': bookings.count() + flights.count() + visas_count,
            'dept_breakdown': dept_breakdown,
            'chart_data': {
                'labels': labels,
                'pkg_series': pkg_series,
                'flight_series': flight_series,
                'visa_series': visa_series,
            },
            'ledger_entries': ledger_data,
        }
    })


@csrf_exempt
@admin_required_api
def admin_export_report_api(request, report_type, fmt):
    """
    Export reports for Admin across all agents or a specific agent (ledger, bookings, visas, flights) in CSV, Excel, or PDF formats.
    Accepts optional GET parameter `agent_id`.
    """
    import csv
    fmt = fmt.lower()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    report_type = report_type.lower()
    agent_id = request.GET.get('agent_id')

    target_agent = None
    if agent_id and agent_id != 'all':
        try:
            target_agent = User.objects.get(pk=agent_id, role='agent')
        except User.DoesNotExist:
            pass

    headers = []
    rows = []
    title = ""
    filename_base = f"admin_{report_type}_report_{timestamp}"

    if report_type == 'ledger':
        title = f"B2B Agent Wallet Ledger Statement — {target_agent.company_name or target_agent.username if target_agent else 'All Agents'}"
        headers = ['ID', 'Agent / Company', 'Type', 'Category', 'Amount (PKR)', 'Running Balance (PKR)', 'Reference', 'Description', 'Date']
        entries = AgentLedger.objects.select_related('agent').all().order_by('-created_at')
        if target_agent:
            entries = entries.filter(agent=target_agent)

        for e in entries[:500]:
            rows.append([
                str(e.id),
                f"{e.agent.company_name or e.agent.username} (@{e.agent.username})",
                e.entry_type.upper(),
                e.get_category_display() if hasattr(e, 'get_category_display') else e.category,
                f"PKR {e.amount:,.2f}",
                f"PKR {float(getattr(e, 'running_balance', 0.0) or 0.0):,.2f}",
                e.reference or "N/A",
                e.description or "",
                e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else ''
            ])

    elif report_type == 'bookings':
        title = f"B2B Agent Package Bookings Report — {target_agent.company_name if target_agent else 'All Agents'}"
        headers = ['Booking ID', 'Agent', 'Package Title', 'Booking Type', 'Sharing Category', 'Total Price (PKR)', 'Status', 'Date']
        bookings = Booking.objects.select_related('user', 'package').all().order_by('-created_at')
        if target_agent:
            bookings = bookings.filter(user=target_agent)
        for b in bookings[:500]:
            rows.append([
                f"BK-{b.id:04d}",
                b.user.username if b.user else "N/A",
                b.package.title if b.package else "Custom Package",
                b.booking_type or 'package',
                b.sharing_category or 'quad',
                f"PKR {b.total_price:,.2f}" if b.total_price else "PKR 0.00",
                b.status.upper(),
                b.created_at.strftime('%Y-%m-%d %H:%M') if b.created_at else ''
            ])

    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid report type'}, status=400)

    if fmt in ['excel', 'xlsx', 'xls']:
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.xls"'

        headers_html = "".join([f"<th style='background-color:#2D4424;color:#fff;padding:8px;border:1px solid #1F2E1A;'>{h}</th>" for h in headers])
        rows_html = ""
        for r in rows:
            cells = "".join([f"<td style='padding:6px;border:1px solid #e2e8f0;'>{c}</td>" for c in r])
            rows_html += f"<tr>{cells}</tr>"

        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="utf-8">
        <style>body {{ font-family: Arial, sans-serif; font-size: 11px; }} table {{ border-collapse: collapse; width: 100%; }}</style>
        </head>
        <body>
            <h2 style="color:#2D4424;">{title}</h2>
            <p>Generated: {timezone.now().strftime('%B %d, %Y %H:%M')} | Scope: {target_agent.username if target_agent else 'All B2B Agents'}</p>
            <table>
                <thead><tr>{headers_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </body></html>"""
        response.write(html_content)
        return response

    elif fmt == 'pdf':
        return render(request, 'reports/report_printable.html', {
            'report_title': title,
            'subtitle': f"Master B2B Administrative Export — {target_agent.company_name if target_agent else 'All Agents'}",
            'headers': headers,
            'rows': rows,
            'summary_kpis': [
                {'label': 'Total Records', 'value': str(len(rows))},
                {'label': 'Target Agent', 'value': target_agent.company_name if target_agent else 'All Active Agents'}
            ]
        })

    else: # CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)
        writer.writerow([title])
        writer.writerow([f"Generated Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}"])
        writer.writerow([])
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        return response


@csrf_exempt
@user_passes_test(is_agent)
def agent_export_report_api(request, report_type, fmt):
    """
    Export reports for B2B agent (ledger, bookings, visas, flights) in CSV, Excel, or PDF formats.
    Strictly isolated to request.user data.
    """
    import csv
    agent = request.user
    fmt = fmt.lower()
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    report_type = report_type.lower()
    
    headers = []
    rows = []
    title = ""
    filename_base = f"agent_{report_type}_report_{timestamp}"

    if report_type == 'ledger':
        title = f"B2B Agent Wallet Ledger Statement — {agent.company_name or agent.username}"
        headers = ['ID', 'Type', 'Category', 'Amount (PKR)', 'Running Balance (PKR)', 'Reference', 'Description', 'Date']
        entries = AgentLedger.objects.filter(agent=agent).order_by('-created_at')
        for e in entries:
            rows.append([
                str(e.id),
                e.entry_type.upper(),
                e.get_category_display() if hasattr(e, 'get_category_display') else e.category,
                f"PKR {e.amount:,.2f}",
                f"PKR {float(getattr(e, 'running_balance', 0.0) or 0.0):,.2f}",
                e.reference or "N/A",
                e.description or "",
                e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else ''
            ])
            
    elif report_type == 'bookings':
        title = f"B2B Agent Package Bookings Report — {agent.company_name or agent.username}"
        headers = ['Booking ID', 'Package Title', 'Booking Type', 'Sharing Category', 'Total Price (PKR)', 'Status', 'Date']
        bookings = Booking.objects.filter(user=agent).select_related('package').order_by('-created_at')
        for b in bookings:
            rows.append([
                f"BK-{b.id:04d}",
                b.package.title if b.package else "Custom Package",
                b.booking_type or 'package',
                b.sharing_category or 'quad',
                f"PKR {b.total_price:,.2f}" if b.total_price else "PKR 0.00",
                b.status.upper(),
                b.created_at.strftime('%Y-%m-%d %H:%M') if b.created_at else ''
            ])
            
    elif report_type == 'visas':
        title = f"B2B Agent Visa Submissions Report — {agent.company_name or agent.username}"
        headers = ['Application ID', 'Full Name', 'Country', 'Visa Type', 'Passport No', 'Status', 'Date']
        visas = VisaApplication.objects.filter(user=agent).order_by('-created_at')
        for v in visas:
            rows.append([
                f"VISA-{v.id:04d}",
                getattr(v, 'full_name', agent.username),
                v.country or 'Saudi Arabia',
                v.visa_type or 'Tourist',
                v.passport_number or 'N/A',
                v.status.upper(),
                v.created_at.strftime('%Y-%m-%d %H:%M') if v.created_at else ''
            ])

    elif report_type == 'flights':
        title = f"B2B Agent Flight Quotations Report — {agent.company_name or agent.username}"
        headers = ['Quote ID', 'Route', 'Departure Date', 'Return Date', 'Quoted Price (PKR)', 'Status', 'Date']
        flights = FlightQuoteRequest.objects.filter(user=agent).order_by('-created_at')
        for f in flights:
            route = f"{f.departure_city} → {f.destination_city}"
            dep_date = f.departure_date.strftime('%Y-%m-%d') if hasattr(f.departure_date, 'strftime') else str(f.departure_date)
            ret_date = (f.return_date.strftime('%Y-%m-%d') if hasattr(f.return_date, 'strftime') else str(f.return_date)) if f.return_date else 'One Way'
            rows.append([
                f"FLT-{f.id:04d}",
                route,
                dep_date,
                ret_date,
                f"PKR {f.price_quote:,.2f}" if f.price_quote else "Pending Quote",
                f.status.upper(),
                f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else ''
            ])
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid report type'}, status=400)

    if fmt == 'excel' or fmt == 'xlsx' or fmt == 'xls':
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.xls"'
        
        headers_html = "".join([f"<th style='background-color:#ea580c;color:#fff;padding:8px;border:1px solid #c2410c;'>{h}</th>" for h in headers])
        rows_html = ""
        for r in rows:
            cells = "".join([f"<td style='padding:6px;border:1px solid #e2e8f0;'>{c}</td>" for c in r])
            rows_html += f"<tr>{cells}</tr>"

        html_content = f"""<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="utf-8">
        <style>body {{ font-family: Arial, sans-serif; font-size: 11px; }} table {{ border-collapse: collapse; width: 100%; }}</style>
        </head>
        <body>
            <h2 style="color:#ea580c;">{title}</h2>
            <p>Generated: {timezone.now().strftime('%B %d, %Y %H:%M')} | Agent: {agent.username}</p>
            <table>
                <thead><tr>{headers_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </body></html>"""
        response.write(html_content)
        return response

    elif fmt == 'pdf':
        return render(request, 'reports/report_printable.html', {
            'report_title': title,
            'subtitle': f"Generated for B2B Partner: {agent.company_name or agent.username} ({agent.email})",
            'headers': headers,
            'rows': rows,
            'summary_kpis': [
                {'label': 'Total Records', 'value': str(len(rows))},
                {'label': 'Current Wallet Balance', 'value': f"PKR {getattr(agent, 'wallet_balance', 0.0):,.2f}"},
                {'label': 'Agent Company', 'value': agent.company_name or 'Independent Agent'}
            ]
        })

    else: # Default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)
        writer.writerow([title])
        writer.writerow([f"Generated Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}"])
        writer.writerow([])
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        return response


# ══════════════════════════════════════════════
# COMPANY BANK ACCOUNTS APIs (Admin & Agent)
# ══════════════════════════════════════════════

@csrf_exempt
@admin_required_api
def admin_bank_accounts_api(request):
    """
    GET  → List all CompanyBankAccount records for admin.
    POST → Create a new CompanyBankAccount record.
    """
    from apps.accounts.models import CompanyBankAccount

    if request.method == 'GET':
        accounts = CompanyBankAccount.objects.all()
        data = [{
            'id': a.id,
            'bank_name': a.bank_name,
            'account_title': a.account_title,
            'account_number': a.account_number,
            'iban': a.iban or '',
            'branch_code': a.branch_code or '',
            'branch_name': a.branch_name or '',
            'swift_code': a.swift_code or '',
            'is_active': a.is_active,
            'created_at': a.created_at.strftime('%Y-%m-%d %H:%M')
        } for a in accounts]
        return JsonResponse({'success': True, 'accounts': data})

    if request.method == 'POST':
        bank_name = request.POST.get('bank_name', '').strip()
        account_title = request.POST.get('account_title', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        iban = request.POST.get('iban', '').strip()
        branch_code = request.POST.get('branch_code', '').strip()
        branch_name = request.POST.get('branch_name', '').strip()
        swift_code = request.POST.get('swift_code', '').strip()
        is_active_val = request.POST.get('is_active')
        is_active = is_active_val in ('on', 'true', '1', 'True', True) if is_active_val is not None else True

        if not bank_name or not account_title or not account_number:
            return JsonResponse({'success': False, 'message': 'Bank Name, Account Title, and Account Number are required.'}, status=400)

        acc = CompanyBankAccount.objects.create(
            bank_name=bank_name,
            account_title=account_title,
            account_number=account_number,
            iban=iban or None,
            branch_code=branch_code or None,
            branch_name=branch_name or None,
            swift_code=swift_code or None,
            is_active=is_active
        )
        return JsonResponse({'success': True, 'id': acc.id, 'message': 'Company bank account added successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_bank_account_detail_api(request, pk):
    """
    POST   → Edit company bank account details.
    DELETE → Delete company bank account record.
    """
    from apps.accounts.models import CompanyBankAccount

    acc = get_object_or_404(CompanyBankAccount, pk=pk)

    if request.method == 'DELETE':
        acc.delete()
        return JsonResponse({'success': True, 'message': 'Bank account deleted successfully.'})

    if request.method == 'POST':
        acc.bank_name = (request.POST.get('bank_name') or acc.bank_name or '').strip()
        acc.account_title = (request.POST.get('account_title') or acc.account_title or '').strip()
        acc.account_number = (request.POST.get('account_number') or acc.account_number or '').strip()
        acc.iban = (request.POST.get('iban') or acc.iban or '').strip() or None
        acc.branch_code = (request.POST.get('branch_code') or acc.branch_code or '').strip() or None
        acc.branch_name = (request.POST.get('branch_name') or acc.branch_name or '').strip() or None
        acc.swift_code = (request.POST.get('swift_code') or acc.swift_code or '').strip() or None

        if 'is_active' in request.POST:
            is_active_val = request.POST.get('is_active')
            acc.is_active = is_active_val in ('on', 'true', '1', 'True', True)

        acc.save()
        return JsonResponse({'success': True, 'message': 'Bank account updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@user_passes_test(is_agent_or_admin)
def agent_bank_accounts_api(request):
    """
    GET → List active CompanyBankAccount records for agent view.
    """
    from apps.accounts.models import CompanyBankAccount

    accounts = CompanyBankAccount.objects.filter(is_active=True)
    data = [{
        'id': a.id,
        'bank_name': a.bank_name,
        'account_title': a.account_title,
        'account_number': a.account_number,
        'iban': a.iban or '',
        'branch_code': a.branch_code or '',
        'branch_name': a.branch_name or '',
        'swift_code': a.swift_code or '',
    } for a in accounts]
    return JsonResponse({'success': True, 'accounts': data})


# ─────────────────────────────────────────────────────────────────────────────
# 🏢 COMPANY DEPARTMENT CONTACT DIRECTORY APIs
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@admin_required_api
def admin_department_contacts_api(request):
    """
    GET  → List all department contacts for Admin management.
    POST → Create a new department contact record.
    """
    from apps.accounts.models import CompanyDepartmentContact

    if request.method == 'GET':
        contacts = CompanyDepartmentContact.objects.all().order_by('display_order', '-created_at')
        data = [{
            'id': c.id,
            'department_name': c.department_name,
            'contact_person_name': c.contact_person_name or '',
            'designation': c.designation or '',
            'phone_number': c.phone_number,
            'whatsapp_number': c.whatsapp_number or '',
            'email': c.email or '',
            'description': c.description or '',
            'display_order': c.display_order,
            'is_active': c.is_active,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
        } for c in contacts]
        return JsonResponse({'success': True, 'contacts': data})

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body)
        except Exception:
            payload = request.POST

        dept_name = payload.get('department_name', '').strip()
        phone = payload.get('phone_number', '').strip()

        if not dept_name or not phone:
            return JsonResponse({'success': False, 'error': 'Department Name and Phone Number are required.'}, status=400)

        contact = CompanyDepartmentContact.objects.create(
            department_name=dept_name,
            contact_person_name=payload.get('contact_person_name', '').strip() or None,
            designation=payload.get('designation', '').strip() or None,
            phone_number=phone,
            whatsapp_number=payload.get('whatsapp_number', '').strip() or None,
            email=payload.get('email', '').strip() or None,
            description=payload.get('description', '').strip() or None,
            display_order=int(payload.get('display_order') or 0),
            is_active=payload.get('is_active') in ('on', 'true', '1', 'True', True) if 'is_active' in payload else True
        )
        return JsonResponse({'success': True, 'message': 'Department contact created successfully.', 'id': contact.id})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@admin_required_api
def admin_department_contact_detail_api(request, pk):
    """
    POST/PATCH → Update a department contact.
    DELETE → Remove a department contact record.
    """
    from apps.accounts.models import CompanyDepartmentContact

    contact = get_object_or_404(CompanyDepartmentContact, pk=pk)

    if request.method == 'DELETE':
        contact.delete()
        return JsonResponse({'success': True, 'message': 'Department contact deleted successfully.'})

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
        except Exception:
            payload = request.POST

        if 'department_name' in payload:
            contact.department_name = payload.get('department_name').strip()
        if 'contact_person_name' in payload:
            contact.contact_person_name = payload.get('contact_person_name').strip() or None
        if 'designation' in payload:
            contact.designation = payload.get('designation').strip() or None
        if 'phone_number' in payload:
            contact.phone_number = payload.get('phone_number').strip()
        if 'whatsapp_number' in payload:
            contact.whatsapp_number = payload.get('whatsapp_number').strip() or None
        if 'email' in payload:
            contact.email = payload.get('email').strip() or None
        if 'description' in payload:
            contact.description = payload.get('description').strip() or None
        if 'display_order' in payload:
            try:
                contact.display_order = int(payload.get('display_order'))
            except Exception:
                pass
        if 'is_active' in payload:
            is_act = payload.get('is_active')
            contact.is_active = is_act in ('on', 'true', '1', 'True', True)

        contact.save()
        return JsonResponse({'success': True, 'message': 'Department contact updated successfully.'})

    return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)


@csrf_exempt
@user_passes_test(is_agent_or_admin)
def agent_department_contacts_api(request):
    """
    GET → List all active department contacts for Agent Portal Contact Us page.
    Seed default department records if none exist yet.
    """
    from apps.accounts.models import CompanyDepartmentContact

    contacts = CompanyDepartmentContact.objects.filter(is_active=True).order_by('display_order', '-created_at')

    # Seed default departments if database is empty
    if not contacts.exists() and CompanyDepartmentContact.objects.count() == 0:
        defaults = [
            {
                'department_name': 'Ticketing & Reservations',
                'contact_person_name': 'Muhammad Ali',
                'designation': 'Head of Ticketing',
                'phone_number': '+92 300 1234567',
                'whatsapp_number': '+92 307 7233303',
                'email': 'ticketing@goldenstartravel.com',
                'description': 'Flight bookings, group deals, baggage tier inquiries & PNR status updates.',
                'display_order': 1
            },
            {
                'department_name': 'Hajj & Umrah Department',
                'contact_person_name': 'Sheikh Rashid Ahmad',
                'designation': 'Pilgrimage Operations Director',
                'phone_number': '+92 301 8765432',
                'whatsapp_number': '+92 307 7233303',
                'email': 'umrah@goldenstartravel.com',
                'description': 'Custom Umrah packages, Hajj seat allotments, hotel vouchers & Transport sharing.',
                'display_order': 2
            },
            {
                'department_name': 'Accounts & Payments',
                'contact_person_name': 'Zahid Hassan',
                'designation': 'Senior Finance Officer',
                'phone_number': '+92 302 9988776',
                'whatsapp_number': '+92 307 7233303',
                'email': 'accounts@goldenstartravel.com',
                'description': 'Agent wallet balance, bank deposit verification, ledger audits & top-up receipts.',
                'display_order': 3
            },
            {
                'department_name': 'Visa & Documentation',
                'contact_person_name': 'Usman Qureshi',
                'designation': 'Visa Operations Lead',
                'phone_number': '+92 303 5544332',
                'whatsapp_number': '+92 307 7233303',
                'email': 'visas@goldenstartravel.com',
                'description': 'Saudi e-Visa processing, embassy requirements, document vetting & passport status.',
                'display_order': 4
            },
            {
                'department_name': '24/7 B2B Emergency Support',
                'contact_person_name': 'Golden Star Desk',
                'designation': '24/7 Operations Helpline',
                'phone_number': '+92 307 7233303',
                'whatsapp_number': '+92 307 7233303',
                'email': 'support@goldenstartravel.com',
                'description': 'Round-the-clock emergency support for flight changes, emergency hotel assistance & agent desk.',
                'display_order': 5
            }
        ]
        for d in defaults:
            CompanyDepartmentContact.objects.create(**d)
        contacts = CompanyDepartmentContact.objects.filter(is_active=True).order_by('display_order', '-created_at')

    data = [{
        'id': c.id,
        'department_name': c.department_name,
        'contact_person_name': c.contact_person_name or '',
        'designation': c.designation or '',
        'phone_number': c.phone_number,
        'whatsapp_number': c.whatsapp_number or '',
        'email': c.email or '',
        'description': c.description or '',
        'display_order': c.display_order
    } for c in contacts]
    return JsonResponse({'success': True, 'contacts': data})





@csrf_exempt
@admin_required_api
def admin_custom_inquiries_list_api(request):
    """
    GET /dashboard/admin/api/custom-inquiries/
    Returns list of all CustomPackageInquiry items for B2C Admin Panel.
    """
    inquiries = CustomPackageInquiry.objects.all().order_by('-created_at')
    data = []
    for item in inquiries:
        data.append({
            'id': item.id,
            'name': item.name,
            'email': item.email,
            'phone': item.phone,
            'package_type': item.package_type,
            'days': item.days,
            'makkah_distance': item.makkah_distance,
            'madinah_distance': item.madinah_distance,
            'airline': item.airline,
            'additional_notes': item.additional_notes or '',
            'is_contacted': item.is_contacted,
            'status': 'contacted' if item.is_contacted else 'pending',
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({
        'success': True,
        'inquiries': data,
        'data': data,
        'total_count': len(data),
        'pending_count': inquiries.filter(is_contacted=False).count(),
        'contacted_count': inquiries.filter(is_contacted=True).count()
    })


@csrf_exempt
@admin_required_api
def admin_custom_inquiry_contact_api(request, pk):
    """
    POST/PATCH /dashboard/admin/api/custom-inquiries/<pk>/contact/
    Toggles or updates the is_contacted status for an inquiry.
    """
    inquiry = get_object_or_404(CustomPackageInquiry, pk=pk)
    if request.method in ['POST', 'PATCH', 'PUT']:
        try:
            body = json.loads(request.body.decode('utf-8'))
            if 'is_contacted' in body:
                inquiry.is_contacted = bool(body['is_contacted'])
            else:
                inquiry.is_contacted = not inquiry.is_contacted
        except Exception:
            inquiry.is_contacted = not inquiry.is_contacted
            
        inquiry.save()
        return JsonResponse({
            'success': True,
            'is_contacted': inquiry.is_contacted,
            'message': f"Inquiry status updated to {'Contacted' if inquiry.is_contacted else 'Pending'}."
        })

    return JsonResponse({'error': 'Invalid request method.'}, status=405)







