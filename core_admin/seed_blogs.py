"""
Seed script — creates sample Blog categories and posts.
Run: python core_admin/manage.py shell < core_admin/seed_blogs.py
"""
import django, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.blog.models import BlogCategory, BlogPost
from django.utils import timezone

# ── Categories ───────────────────────────────────────────────────────────────
cats = [
    {'name': 'Hajj & Umrah', 'slug': 'hajj-umrah', 'color': 'brand-orange'},
    {'name': 'Visa Guides', 'slug': 'visa-guides', 'color': 'blue'},
    {'name': 'Destination Spotlight', 'slug': 'destination-spotlight', 'color': 'emerald'},
    {'name': 'Travel Tips', 'slug': 'travel-tips', 'color': 'purple'},
    {'name': 'News & Updates', 'slug': 'news-updates', 'color': 'rose'},
]
cat_objs = {}
for c in cats:
    obj, _ = BlogCategory.objects.get_or_create(slug=c['slug'], defaults={'name': c['name'], 'color': c['color']})
    cat_objs[c['slug']] = obj
    print(f"  Category: {obj.name}")

# ── Posts ─────────────────────────────────────────────────────────────────────
posts = [
    {
        'title': 'Complete Hajj 2026 Preparation Guide: What Every Pilgrim Must Know',
        'slug': 'hajj-2026-preparation-guide',
        'category': 'hajj-umrah',
        'excerpt': 'From obtaining your Hajj visa to selecting the right Maktab and packing essentials — this comprehensive guide walks you through every step of your blessed pilgrimage.',
        'body': '''<h2>Why Preparation is Key</h2>
<p>Hajj is the fifth pillar of Islam and performing it well-prepared ensures a spiritually fulfilling and physically comfortable journey. This guide covers everything from visa requirements to on-ground logistics.</p>
<h2>Step 1: Securing Your Hajj Visa</h2>
<p>Pakistan allocates a fixed quota for Hajj pilgrims each year. Apply through the <strong>Ministry of Religious Affairs portal</strong> or via a registered private operator. Required documents include a valid CNIC, passport (minimum 6 months validity), and recent photographs.</p>
<h2>Step 2: Choosing the Right Package</h2>
<p>There are three main Hajj categories:</p>
<ul>
<li><strong>Government Hajj Scheme</strong> — subsidised and strictly regulated</li>
<li><strong>Private Economy</strong> — affordable with standard hotels</li>
<li><strong>Private VIP</strong> — 5-star hotels within 50–200 meters of Haram</li>
</ul>
<h2>Step 3: Health Preparation</h2>
<p>Meningitis and COVID-19 vaccinations are mandatory. Consult your physician at least 8 weeks before departure for a full check-up and necessary travel vaccinations.</p>
<h2>Essential Packing List</h2>
<p>Ihram clothing, comfortable sandals, a small medical kit, sunscreen SPF 50+, a portable power bank, and a waterproof document holder are must-haves.</p>
<blockquote>Tip: Download the Nusuk app for digital Hajj permit management and prayer time notifications directly from the Saudi authorities.</blockquote>''',
        'static_cover': 'hajj_card.png',
        'author_name': 'Hajj Advisory Team',
        'read_time': 8,
        'is_featured': True,
        'status': 'published',
        'published_at': timezone.now(),
    },
    {
        'title': 'UAE Tourist Visa 2026: Complete Application Process for Pakistanis',
        'slug': 'uae-tourist-visa-2026-pakistan',
        'category': 'visa-guides',
        'excerpt': 'Everything you need to know about applying for a UAE tourist visa from Pakistan, including fees, processing times, document checklist, and e-visa portal instructions.',
        'body': '''<h2>UAE Visa at a Glance</h2>
<p>Pakistan passport holders require a visa to enter the UAE. The good news: the process is now mostly digital and can be completed in 2–5 business days.</p>
<h2>Types of UAE Visas Available</h2>
<ul>
<li><strong>30-Day Tourist Visa</strong> — PKR 18,000–22,000 approx</li>
<li><strong>60-Day Tourist Visa</strong> — PKR 28,000–35,000 approx</li>
<li><strong>96-Hour Transit Visa</strong> — For short layovers</li>
</ul>
<h2>Required Documents</h2>
<p>Valid passport (6+ months), recent passport-size photo, confirmed return flight ticket, hotel booking confirmation, bank statement (last 3 months), and travel insurance.</p>
<h2>Application Channels</h2>
<p>You can apply via Emirates Airlines official site, Air Arabia, ICP Smart Services, or through an authorised travel agent like Golden Star Agency for fastest processing.</p>
<blockquote>Pro Tip: Having AED 5,000 or equivalent in your bank statement significantly improves approval chances.</blockquote>''',
        'static_cover': 'turkey_card.png',
        'author_name': 'Visa Services Team',
        'read_time': 6,
        'is_featured': False,
        'status': 'published',
        'published_at': timezone.now(),
    },
    {
        'title': 'Top 7 Reasons to Visit Istanbul in 2026',
        'slug': 'top-7-reasons-visit-istanbul-2026',
        'category': 'destination-spotlight',
        'excerpt': 'Istanbul straddles two continents and thousands of years of history. Here are 7 compelling reasons why Pakistani travellers are choosing Turkey as their top destination this year.',
        'body': '''<h2>1. No Visa Required for Pakistanis</h2>
<p>One of the biggest draws — Pakistani passport holders can enter Turkey visa-free for up to 90 days (180-day period). No embassy visit, no waiting.</p>
<h2>2. Affordable Luxury</h2>
<p>The Turkish Lira exchange rate makes Istanbul incredibly affordable. A 5-star hotel costs a fraction of what it would in Dubai or London.</p>
<h2>3. Halal Food Heaven</h2>
<p>Istanbul is a food paradise for Muslim travellers. From simit and kebabs to incredible baklava and Turkish tea — every meal is an experience.</p>
<h2>4. Historic Mosques & Sacred Sites</h2>
<p>The Blue Mosque (Sultan Ahmed), Hagia Sophia, and Süleymaniye Mosque offer breathtaking architecture and spiritual atmosphere.</p>
<h2>5. Cappadocia Hot Air Balloons</h2>
<p>Just 5 hours from Istanbul, Cappadocia's fairy chimneys and sunrise balloon rides are bucket-list experiences at very reasonable prices.</p>
<h2>6. Direct Flights from Pakistan</h2>
<p>Multiple airlines operate direct Karachi/Lahore to Istanbul routes. Flight time is approximately 6–7 hours.</p>
<h2>7. Family-Friendly Culture</h2>
<p>Turkey is deeply conservative and family-oriented, making it perfect for Pakistani families seeking a culturally comfortable vacation abroad.</p>''',
        'static_cover': 'turkey_card.png',
        'author_name': 'Destinations Editorial',
        'read_time': 5,
        'is_featured': False,
        'status': 'published',
        'published_at': timezone.now(),
    },
    {
        'title': '10 Smart Tips to Save Money on Your Umrah Trip',
        'slug': '10-smart-tips-save-money-umrah',
        'category': 'travel-tips',
        'excerpt': 'Performing Umrah does not have to break the bank. Discover 10 proven strategies to cut costs without compromising the quality of your spiritual journey.',
        'body': '''<h2>1. Book Off-Peak Dates</h2>
<p>Avoid Ramadan and school holidays. Prices for flights and hotels can be 40–60% lower during off-peak months like August–October.</p>
<h2>2. Choose Economy Class Hotels</h2>
<p>3-star hotels near Haram still offer walkable proximity. The saved budget can be spent on local food and souvenirs.</p>
<h2>3. Book a Group Package</h2>
<p>Group bookings of 10+ pilgrims unlock significant discounts on flights, transfers, and hotels.</p>
<h2>4. Compare Airlines</h2>
<p>Saudia, PIA, and Air Arabia all operate Umrah routes. Prices vary significantly — book 3–4 months in advance for best deals.</p>
<h2>5. Use a Trusted Agent</h2>
<p>Registered travel agents like Golden Star Agency have bulk contracts with hotels and airlines, passing savings directly to pilgrims.</p>
<h2>6. Pack Light</h2>
<p>Extra baggage fees add up quickly. One bag + carry-on is sufficient for a 15-day Umrah trip.</p>
<h2>7. Cook Simple Meals</h2>
<p>Many hotels provide small kitchens or microwaves. Simple meals save hundreds of thousands of rupees over a 2-week trip.</p>
<h2>8. Use Public Transport</h2>
<p>The Makkah Metro and Haramain High Speed Rail between Makkah and Madinah are excellent value alternatives to private taxis.</p>
<h2>9. Exchange Currency in Pakistan</h2>
<p>SAR exchange rates in Pakistan are often better than at Saudi airports or money changers in Makkah.</p>
<h2>10. Early Return Permits</h2>
<p>If your schedule is flexible, opt for open-return tickets — they sometimes cost less and give you flexibility if your plans change.</p>''',
        'static_cover': 'umrah_card.png',
        'author_name': 'Travel Tips Desk',
        'read_time': 7,
        'is_featured': False,
        'status': 'published',
        'published_at': timezone.now(),
    },
    {
        'title': 'Saudi Arabia Introduces New e-Visa Portal for 2026 — What You Need to Know',
        'slug': 'saudi-e-visa-portal-2026',
        'category': 'news-updates',
        'excerpt': 'Saudi Arabia has launched an upgraded e-Visa system for tourist and Umrah visas. We break down the changes, new processing times, and how Pakistani travellers can benefit.',
        'body': '''<h2>What Changed?</h2>
<p>The Saudi Ministry of Tourism launched the new Nusuk e-Visa portal in early 2026. The updated system now offers faster processing (24–72 hours vs. 7–14 days previously) and a single unified platform for Umrah and tourist visas.</p>
<h2>Key Improvements</h2>
<ul>
<li>Biometric data collection integrated</li>
<li>Digital Mahram verification for female pilgrims</li>
<li>Real-time application tracking</li>
<li>Multi-entry tourist visa option now available</li>
</ul>
<h2>How to Apply</h2>
<p>Visit visa.visitsaudi.com or the official Nusuk app. Upload your documents, pay the visa fee, and receive your e-Visa via email.</p>
<h2>Fees for Pakistani Applicants</h2>
<p>Tourist visa: SAR 300 (~PKR 23,000). Umrah visa: Currently free as part of the pilgrimage facilitation initiative.</p>''',
        'static_cover': 'hajj_card.png',
        'author_name': 'News Desk',
        'read_time': 4,
        'is_featured': False,
        'status': 'published',
        'published_at': timezone.now(),
    },
]

for p in posts:
    cat = cat_objs.get(p.pop('category'))
    p['category'] = cat
    if not BlogPost.objects.filter(slug=p['slug']).exists():
        post = BlogPost.objects.create(**p)
        print(f"  Created post: {post.title}")
    else:
        print(f"  Already exists: {p['slug']}")

print("\n✅ Blog seed complete!")
