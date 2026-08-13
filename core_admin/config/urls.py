"""
URL configuration for core_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.accounts import views as accounts_views
from apps.content import views as content_views
from apps.flights import views as flights_views
from apps.packages import views as packages_views
from apps.visa import views as visa_views
from apps.blog import views as blog_views
from apps.blog import admin_views as blog_admin_views
from apps.airline_ticketing import views as airline_ticketing_views

from django.contrib.sitemaps.views import sitemap
from sitemaps import StaticViewSitemap, PackageSitemap, BlogPostSitemap

from django.views.generic.base import RedirectView

sitemaps = {
    'static': StaticViewSitemap,
    'packages': PackageSitemap,
    'blog': BlogPostSitemap,
}

from django.views.decorators.csrf import ensure_csrf_cookie
admin.site.login = ensure_csrf_cookie(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
    
    # SEO Technical URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', content_views.robots_txt_view, name='robots_txt'),
    
    # Static pages (Templates)
    path('', accounts_views.home_view, name='home'),
    path('achievements/', content_views.achievements_list_view, name='achievements_list'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='contact.html'), name='contact'),
    path('careers/', TemplateView.as_view(template_name='careers.html'), name='careers'),
    path('privacy-policy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    
    # Packages (Dynamic routing from database)
    path('packages/hajj/', packages_views.hajj_list_view, name='hajj_list'),
    path('packages/hajj/<int:pk>/', packages_views.hajj_detail_view, name='hajj_detail'),
    path('packages/umrah/', packages_views.umrah_list_view, name='umrah_list'),
    path('packages/<int:pk>/', packages_views.package_detail_view, name='package_detail'),
    path('api/packages/book/', packages_views.book_package_api, name='book_package_api'),
    
    # Visa (Dynamic catalog & application form)
    path('visa/', visa_views.visa_countries_view, name='visa_countries'),
    path('visa/apply/', TemplateView.as_view(template_name='visa/apply.html'), name='visa_apply'),
    
    # Flights
    path('flights/', flights_views.flight_list_view, name='flights_list'),
    path('flights/<int:pk>/', flights_views.flight_detail_view, name='flight_detail'),
    path('flights/quote/', TemplateView.as_view(template_name='flights/quote_request.html'), name='flight_quote'),
    
    # Public Blogs
    path('blogs/', blog_views.blog_list_view, name='blog_list'),
    path('blogs/<slug:slug>/', blog_views.blog_detail_view, name='blog_detail'),
    
    # Auth
    path('auth/login/', accounts_views.login_view, name='login'),
    path('auth/signup/', accounts_views.signup_view, name='signup'),
    path('auth/logout/', accounts_views.logout_view, name='logout'),
    path('auth/verify-email/<int:user_id>/', accounts_views.verify_email_view, name='verify_email'),
    path('auth/resend-otp/<int:user_id>/', accounts_views.resend_otp_view, name='resend_otp'),
    path('auth/pending-approval/', accounts_views.pending_approval_view, name='pending_approval'),
    path('auth/signup/agent/verify/<int:user_id>/', accounts_views.agent_signup_verify_view, name='agent_signup_verify'),
    path('auth/signup/agent/documents/<int:user_id>/', accounts_views.agent_signup_documents_view, name='agent_signup_documents'),
    path('auth/forgot-password/', accounts_views.forgot_password_view, name='forgot_password'),
    path('auth/forgot-password/verify/', accounts_views.forgot_password_verify_view, name='forgot_password_verify'),
    path('auth/forgot-password/reset/<int:user_id>/', accounts_views.forgot_password_reset_view, name='forgot_password_reset'),
    
    # Dashboards
    path('dashboard/customer/', accounts_views.customer_dashboard_view, name='customer_dashboard'),
    path('dashboard/user/', accounts_views.customer_dashboard_view, name='user_dashboard'),
    path('dashboard/agent/', accounts_views.agent_dashboard_view, name='agent_dashboard'),
    path('dashboard/admin/', accounts_views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/admin/api/agents/', accounts_views.admin_dashboard_api, name='admin_dashboard_api'),
    path('dashboard/admin/api/agents/<str:agent_id>/approve/', accounts_views.admin_approve_agent, name='admin_approve_agent'),
    path('dashboard/admin/api/agents/<str:agent_id>/reject/', accounts_views.admin_reject_agent, name='admin_reject_agent'),
    path('dashboard/admin/api/agents/<str:agent_id>/suspend/', accounts_views.admin_suspend_agent, name='admin_suspend_agent'),
    path('dashboard/admin/api/agents/<str:agent_id>/delete/', accounts_views.admin_delete_agent, name='admin_delete_agent'),
    path('dashboard/admin/api/agents/<str:agent_id>/toggle-badge/', accounts_views.admin_toggle_agent_verification_badge, name='admin_toggle_agent_verification_badge'),
    path('dashboard/admin/api/agents/<str:agent_id>/details/', accounts_views.admin_agent_detail_data_api, name='admin_agent_detail_data_api'),
    path('dashboard/admin/api/agents/<str:agent_id>/ledger/', accounts_views.admin_agent_ledger_api, name='admin_agent_ledger_api'),
    path('dashboard/admin/api/agents/<str:agent_id>/ledger/add/', accounts_views.admin_agent_ledger_create_api, name='admin_agent_ledger_create_api'),
    path('dashboard/admin/api/ledger/entries/<int:entry_id>/delete/', accounts_views.admin_agent_ledger_delete_api, name='admin_agent_ledger_delete_api'),
    path('dashboard/admin/agents/<str:agent_id>/view/', accounts_views.admin_agent_detail_view, name='admin_agent_detail_view'),
    path('agents/<str:agent_id>/profile/', accounts_views.public_agent_profile_view, name='public_agent_profile'),
    path('api/track/<str:tracking_id>/', accounts_views.track_status_api, name='track_status_api'),
    path('api/visa/submit/', accounts_views.submit_visa_application_api, name='submit_visa_application_api'),
    path('api/flights/quote/submit/', accounts_views.submit_flight_quote_api, name='submit_flight_quote_api'),
    path('api/flights/book/', accounts_views.submit_flight_ticket_booking_api, name='submit_flight_ticket_booking_api'),
    path('api/search/live/', accounts_views.live_search_api, name='live_search_api'),
    
    # Agent API endpoints
    path('dashboard/agent/api/overview-stats/', accounts_views.agent_dashboard_overview_api, name='agent_dashboard_overview_api'),
    path('dashboard/agent/api/bookings/', accounts_views.agent_bookings_api, name='agent_bookings_api'),
    path('dashboard/agent/api/visas/', accounts_views.agent_visas_api, name='agent_visas_api'),
    path('dashboard/agent/api/flights/', accounts_views.agent_flights_api, name='agent_flights_api'),
    path('dashboard/agent/chart/', accounts_views.agent_dashboard_chart_view, name='agent_dashboard_chart'),
    path('dashboard/agent/chart/pie/', accounts_views.agent_dashboard_pie_chart_view, name='agent_dashboard_pie_chart'),
    path('dashboard/agent/chart/bar/', accounts_views.agent_dashboard_bar_chart_view, name='agent_dashboard_bar_chart'),
    path('dashboard/agent/chart/data/', accounts_views.agent_chart_data_api, name='agent_chart_data_api'),
    path('dashboard/agent/profile-settings/', accounts_views.agent_profile_settings_view, name='agent_profile_settings'),
    path('dashboard/agent/api/analytics/financial/', accounts_views.agent_financial_analytics_api, name='agent_financial_analytics_api'),
    path('dashboard/agent/api/reports/export/<str:report_type>/<str:fmt>/', accounts_views.agent_export_report_api, name='agent_export_report_api'),
    path('dashboard/agent/api/feedback/submit/', accounts_views.agent_submit_feedback_api, name='agent_submit_feedback_api'),
    path('dashboard/agent/api/feedback/my/', accounts_views.agent_feedbacks_api, name='agent_feedbacks_api'),
    path('dashboard/agent/api/my-id-card/', accounts_views.agent_my_id_card_api, name='agent_my_id_card_api'),
    path('dashboard/agent/id-card-qr/<str:agent_id_number>/', accounts_views.agent_id_card_qr_api, name='agent_id_card_qr_api'),
    path('verify-agent/<str:agent_id_number>/', accounts_views.verify_agent_public_view, name='verify_agent_public'),
    
    # Admin API endpoints
    path('dashboard/admin/api/feedbacks/', accounts_views.admin_agent_feedbacks_api, name='admin_agent_feedbacks_api'),
    path('dashboard/admin/api/feedbacks/<int:pk>/status/', accounts_views.admin_feedback_status_api, name='admin_feedback_status_api'),
    path('dashboard/admin/api/feedbacks/<int:pk>/delete/', accounts_views.admin_feedback_delete_api, name='admin_feedback_delete_api'),

    path('dashboard/admin/api/overview-stats/', accounts_views.admin_dashboard_overview_api, name='admin_dashboard_overview_api'),
    path('dashboard/admin/api/b2b-overview/', accounts_views.admin_b2b_overview_api, name='admin_b2b_overview_api'),
    path('dashboard/admin/api/packages/', packages_views.admin_packages_list_api, name='admin_packages_api'),
    path('dashboard/admin/api/packages/create/', packages_views.admin_package_create_api, name='admin_package_create_api'),
    path('dashboard/admin/api/packages/<int:pk>/', packages_views.admin_package_detail_api, name='admin_package_detail_api'),
    path('dashboard/admin/api/packages/<int:pk>/delete/', packages_views.admin_package_delete_api, name='admin_package_delete_api'),
    path('dashboard/admin/api/packages/<int:pk>/toggle-featured/', packages_views.admin_package_toggle_featured_api, name='admin_package_toggle_featured_api'),
    path('dashboard/admin/api/hajj-packages/', packages_views.admin_hajj_packages_api, name='admin_hajj_packages_api'),
    path('dashboard/admin/api/hajj-packages/<int:pk>/', packages_views.admin_hajj_package_detail_api, name='admin_hajj_package_detail_api'),
    path('dashboard/admin/api/visas/', accounts_views.admin_visas_api, name='admin_visas_api'),
    path('dashboard/admin/api/visas/<int:pk>/', accounts_views.admin_visa_status_api, name='admin_visa_status_api'),
    path('dashboard/admin/api/visa-packages/', accounts_views.admin_visa_packages_api, name='admin_visa_packages_api'),
    path('dashboard/admin/api/visa-packages/<int:pk>/', accounts_views.admin_visa_package_detail_api, name='admin_visa_package_detail_api'),
    path('dashboard/admin/api/flights/', accounts_views.admin_flights_api, name='admin_flights_api'),
    path('dashboard/admin/api/flights/<int:pk>/', accounts_views.admin_flight_status_api, name='admin_flight_status_api'),
    path('dashboard/admin/api/flight-tickets/', accounts_views.admin_flight_tickets_api, name='admin_flight_tickets_api'),
    path('dashboard/admin/api/flight-tickets/<int:pk>/', accounts_views.admin_flight_ticket_detail_api, name='admin_flight_ticket_detail_api'),
    path('dashboard/admin/api/bookings/', accounts_views.admin_bookings_api, name='admin_bookings_api'),
    path('dashboard/admin/api/bookings/<int:pk>/', accounts_views.admin_booking_status_api, name='admin_booking_status_api'),

    # Complete Admin Blog Management Panel Routes & REST APIs
    path('dashboard/admin/blogs/', blog_admin_views.admin_blogs_page_view, name='admin_blogs_page'),
    path('dashboard/admin/api/blogs/', blog_admin_views.admin_blogs_list_api, name='admin_blogs_list_api'),
    path('dashboard/admin/api/blogs/create/', blog_admin_views.admin_blog_create_api, name='admin_blog_create_api'),
    path('dashboard/admin/api/blogs/<slug:slug>/', blog_admin_views.admin_blog_detail_api, name='admin_blog_detail_api'),
    path('dashboard/admin/api/blogs/<slug:slug>/delete/', blog_admin_views.admin_blog_delete_api, name='admin_blog_delete_api'),
    path('dashboard/admin/api/blogs/<slug:slug>/toggle-publish/', blog_admin_views.admin_blog_toggle_publish_api, name='admin_blog_toggle_publish_api'),
    path('dashboard/admin/api/blog-categories/', blog_admin_views.admin_blog_categories_api, name='admin_blog_categories_api'),
    path('dashboard/admin/api/blog-categories/create/', blog_admin_views.admin_blog_category_create_api, name='admin_blog_category_create_api'),

    # Admin charts
    path('dashboard/admin/chart/trend/', accounts_views.admin_chart_revenue_view, name='admin_chart_trend'),
    path('dashboard/admin/chart/pie/',   accounts_views.admin_chart_pie_view,     name='admin_chart_pie'),
    path('dashboard/admin/chart/agents/', accounts_views.admin_chart_agents_view,  name='admin_chart_agents'),
    path('dashboard/admin/chart/data/',  accounts_views.admin_chart_data_api,     name='admin_chart_data_api'),

    # Platform Reviews APIs
    path('api/reviews/', content_views.get_approved_reviews_api, name='get_approved_reviews_api'),
    path('api/reviews/submit/', content_views.submit_review_api, name='submit_review_api'),
    path('dashboard/admin/api/reviews/', content_views.admin_reviews_list_api, name='admin_reviews_list_api'),
    path('dashboard/admin/api/reviews/<int:review_id>/toggle/', content_views.admin_review_toggle_api, name='admin_review_toggle_api'),
    path('dashboard/admin/api/reviews/<int:review_id>/delete/', content_views.admin_review_delete_api, name='admin_review_delete_api'),

    # Achievements Admin APIs
    path('dashboard/admin/api/achievements/', content_views.admin_achievements_list_api, name='admin_achievements_list_api'),
    path('dashboard/admin/api/achievements/create/', content_views.admin_achievement_create_api, name='admin_achievement_create_api'),
    path('dashboard/admin/api/achievements/<int:pk>/', content_views.admin_achievement_detail_api, name='admin_achievement_detail_api'),

    # Client Accounts APIs
    path('dashboard/admin/api/clients/', accounts_views.admin_clients_list_api, name='admin_clients_list_api'),
    path('dashboard/admin/api/clients/<int:client_id>/toggle/', accounts_views.admin_client_toggle_api, name='admin_client_toggle_api'),

    # Agent Ledger APIs
    path('dashboard/admin/api/agents/<int:agent_id>/ledger/', accounts_views.admin_agent_ledger_api, name='admin_agent_ledger_api'),
    path('dashboard/admin/api/agents/<int:agent_id>/ledger/add/', accounts_views.admin_agent_ledger_create_api, name='admin_agent_ledger_create_api'),
    path('dashboard/admin/api/ledger/<int:entry_id>/delete/', accounts_views.admin_agent_ledger_delete_api, name='admin_agent_ledger_delete_api'),

    # Public Website Client Submission APIs (Bookings, Visas, Flight Quotes)
    path('api/packages/book/', packages_views.book_package_api, name='book_package_api'),
    path('api/visa/submit/', accounts_views.submit_visa_application_api, name='submit_visa_application_api'),
    path('api/flights/quote/', accounts_views.submit_flight_quote_api, name='submit_flight_quote_api'),

    # Custom Inquiries APIs
    path('api/packages/custom-inquiry/', accounts_views.submit_custom_inquiry_api, name='submit_custom_inquiry_api'),
    path('dashboard/admin/api/custom-inquiries/', accounts_views.admin_custom_inquiries_list_api, name='admin_custom_inquiries_list_api'),
    path('dashboard/admin/api/custom-inquiries/<int:pk>/contact/', accounts_views.admin_custom_inquiry_contact_api, name='admin_custom_inquiry_contact_api'),

    # Official Approval Letter Print Routes (Packages, Visas, Tickets)
    path('approval-letter/package/<int:pk>/', accounts_views.package_approval_letter_view, name='package_approval_letter'),
    path('approval-letter/visa/<int:pk>/', accounts_views.visa_approval_letter_view, name='visa_approval_letter'),
    path('approval-letter/ticket/<int:pk>/', accounts_views.ticket_approval_letter_view, name='ticket_approval_letter'),

    # Multi-Format Report Exports APIs (PDF, Word, Excel, CSV)
    path('dashboard/admin/api/reports/export/visas/', accounts_views.admin_export_visas_csv_api, name='admin_export_visas_csv_api'),
    path('dashboard/admin/api/reports/export/bookings/', accounts_views.admin_export_bookings_csv_api, name='admin_export_bookings_csv_api'),
    path('dashboard/admin/api/reports/export/flights/', accounts_views.admin_export_flights_csv_api, name='admin_export_flights_csv_api'),
    path('dashboard/admin/api/reports/export/agents/', accounts_views.admin_export_agents_csv_api, name='admin_export_agents_csv_api'),
    path('dashboard/admin/api/reports/export/agent-ticket-orders/', accounts_views.admin_export_agent_ticket_orders_csv_api, name='admin_export_agent_ticket_orders_csv_api'),
    path('dashboard/admin/api/reports/export/agent-wallet-ledger/', accounts_views.admin_export_agent_wallet_ledger_csv_api, name='admin_export_agent_wallet_ledger_csv_api'),
    path('dashboard/admin/api/reports/export/agent-packages-sales/', accounts_views.admin_export_agent_packages_sales_csv_api, name='admin_export_agent_packages_sales_csv_api'),
    path('dashboard/admin/api/reports/export/<str:report_type>/<str:fmt>/', accounts_views.admin_export_report_api, name='admin_export_report_api'),

    # NumPy & Pandas Financial Analytics APIs
    path('dashboard/admin/api/analytics/financial/', accounts_views.admin_financial_analytics_api, name='admin_financial_analytics_api'),
    path('dashboard/admin/api/analytics/export/<str:fmt>/', accounts_views.admin_export_pandas_analytics_api, name='admin_export_pandas_analytics_api'),
    path('dashboard/admin/api/all-agent-ledgers/', accounts_views.admin_all_agent_ledgers_api, name='admin_all_agent_ledgers_api'),
    path('dashboard/admin/api/bank-accounts/', accounts_views.admin_bank_accounts_api, name='admin_bank_accounts_api'),
    path('dashboard/admin/api/bank-accounts/<int:pk>/', accounts_views.admin_bank_account_detail_api, name='admin_bank_account_detail_api'),
    path('dashboard/agent/api/bank-accounts/', accounts_views.agent_bank_accounts_api, name='agent_bank_accounts_api'),
    path('dashboard/admin/api/department-contacts/', accounts_views.admin_department_contacts_api, name='admin_department_contacts_api'),
    path('dashboard/admin/api/department-contacts/<int:pk>/', accounts_views.admin_department_contact_detail_api, name='admin_department_contact_detail_api'),
    path('dashboard/agent/api/department-contacts/', accounts_views.agent_department_contacts_api, name='agent_department_contacts_api'),

    # Manual Custom Bills & Supplier Expenses APIs (PDF, Word, Excel, CSV)
    path('dashboard/admin/api/custom-bills/', accounts_views.admin_custom_bills_api, name='admin_custom_bills_api'),
    path('dashboard/admin/api/custom-bills/<int:pk>/delete/', accounts_views.admin_delete_custom_bill_api, name='admin_delete_custom_bill_api'),
    path('dashboard/admin/api/custom-bills/<int:pk>/export/<str:fmt>/', accounts_views.admin_export_custom_bill_api, name='admin_export_custom_bill_api'),

    # Airline Ticketing (B2B) — Admin APIs
    path('dashboard/admin/api/sectors/', airline_ticketing_views.admin_sectors_api, name='admin_sectors_api'),
    path('dashboard/admin/api/sectors/<int:pk>/', airline_ticketing_views.admin_sector_detail_api, name='admin_sector_detail_api'),
    path('dashboard/admin/api/adjust-seats/<int:pk>/', airline_ticketing_views.admin_adjust_seats_api, name='admin_adjust_seats_api'),
    path('dashboard/admin/api/airlines/', airline_ticketing_views.admin_airlines_api, name='admin_airlines_api'),
    path('dashboard/admin/api/airlines/<int:pk>/', airline_ticketing_views.admin_airline_detail_api, name='admin_airline_detail_api'),
    path('dashboard/admin/api/flight-inventory/', airline_ticketing_views.admin_flight_inventory_api, name='admin_flight_inventory_api'),
    path('dashboard/admin/api/flight-inventory/<int:pk>/', airline_ticketing_views.admin_flight_inventory_detail_api, name='admin_flight_inventory_detail_api'),

    # Group Ticketing (B2B) — Admin APIs
    path('dashboard/admin/api/group-fare-policies/', airline_ticketing_views.admin_group_fare_policies_api, name='admin_group_fare_policies_api'),
    path('dashboard/admin/api/group-fare-policies/<int:pk>/', airline_ticketing_views.admin_group_fare_policy_detail_api, name='admin_group_fare_policy_detail_api'),
    path('dashboard/admin/api/group-fare-policies/<int:pk>/adjust-seats/', airline_ticketing_views.admin_adjust_group_seats_api, name='admin_adjust_group_seats_api'),

    # Agent Packages (B2B) — Admin APIs
    path('dashboard/admin/api/agent-packages/', airline_ticketing_views.admin_agent_packages_api, name='admin_agent_packages_api'),
    path('dashboard/admin/api/agent-packages/<int:pk>/', airline_ticketing_views.admin_agent_package_detail_api, name='admin_agent_package_detail_api'),

    # Standalone Agent Hajj Packages (B2B) — Admin & Agent APIs
    path('dashboard/admin/api/agent-hajj-packages/', airline_ticketing_views.admin_agent_hajj_packages_api, name='admin_agent_hajj_packages_api'),
    path('dashboard/admin/api/agent-hajj-packages/<int:pk>/', airline_ticketing_views.admin_agent_hajj_package_detail_api, name='admin_agent_hajj_package_detail_api'),
    path('dashboard/agent/api/agent-hajj-packages/', airline_ticketing_views.agent_hajj_packages_api, name='agent_hajj_packages_api'),

    # Hotel Master (B2B) — Admin APIs
    path('dashboard/admin/api/hotels/', airline_ticketing_views.admin_hotels_api, name='admin_hotels_api'),
    path('dashboard/admin/api/hotels/<int:pk>/', airline_ticketing_views.admin_hotel_detail_api, name='admin_hotel_detail_api'),


    # B2B Inventory & Booking — Read-Only Agent APIs
    path('dashboard/agent/api/sectors/', airline_ticketing_views.agent_sectors_api, name='agent_sectors_api'),
    path('dashboard/agent/api/airlines/', airline_ticketing_views.agent_airlines_api, name='agent_airlines_api'),
    path('dashboard/agent/api/flight-inventory/', airline_ticketing_views.agent_flight_inventory_api, name='agent_flight_inventory_api'),
    path('dashboard/agent/api/group-policies/', airline_ticketing_views.agent_group_fare_policies_api, name='agent_group_fare_policies_api'),
    path('dashboard/agent/api/packages/', airline_ticketing_views.agent_packages_api, name='agent_packages_api'),

    # B2B Order Creation & Booking API
    path('dashboard/agent/api/orders/create/', airline_ticketing_views.agent_create_ticket_order_api, name='agent_create_ticket_order_api'),
    path('dashboard/agent/api/orders/<int:pk>/passengers/', airline_ticketing_views.agent_update_passengers_api, name='agent_update_passengers_api'),

    # B2B Ticket Orders — Admin APIs
    path('dashboard/admin/api/ticket-orders/', airline_ticketing_views.admin_ticket_orders_api, name='admin_ticket_orders_api'),
    path('dashboard/admin/api/ticket-orders/<str:pk>/confirm-payment/', airline_ticketing_views.admin_confirm_ticket_payment_api, name='admin_confirm_ticket_payment_api'),
    path('dashboard/admin/api/ticket-orders/<str:pk>/cancel/', airline_ticketing_views.admin_cancel_ticket_order_api, name='admin_cancel_ticket_order_api'),
    path('dashboard/admin/api/ticket-orders/<str:pk>/allot-tickets/', airline_ticketing_views.admin_allot_tickets_api, name='admin_allot_tickets_api'),

    # B2B Ticket Orders — Agent APIs & Printable Ticket
    path('dashboard/agent/api/my-orders/', airline_ticketing_views.agent_my_orders_api, name='agent_my_orders_api'),
    path('dashboard/agent/api/my-orders/<str:pk>/cancel/', airline_ticketing_views.agent_cancel_ticket_order_api, name='agent_cancel_ticket_order_api'),
    path('dashboard/agent/api/my-orders/<str:pk>/delete/', airline_ticketing_views.agent_delete_ticket_order_api, name='agent_delete_ticket_order_api'),
    path('dashboard/agent/api/my-activity/', airline_ticketing_views.agent_my_activity_api, name='agent_my_activity_api'),
    path('dashboard/agent/api/ledger/', airline_ticketing_views.agent_wallet_ledger_api, name='agent_wallet_ledger_api'),
    path('dashboard/agent/api/reports/export/<str:report_type>/<str:fmt>/', accounts_views.agent_export_report_api, name='agent_export_report_api'),
    path('dashboard/agent/ticket-orders/<str:reference_number>/print/', airline_ticketing_views.agent_ticket_order_print_view, name='agent_ticket_order_print_view'),
]

from django.views.static import serve
from django.urls import re_path

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
