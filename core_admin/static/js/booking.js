// Core Travel booking helper script
document.addEventListener('DOMContentLoaded', () => {
    console.log("Golden Star Booking System initialized.");
    
    // Quick search search form logic
    const searchForm = document.getElementById('quick-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const serviceType = document.getElementById('search-service-type').value;
            const packageMonth = document.getElementById('search-month').value;
            console.log(`Searching for service: ${serviceType} in month: ${packageMonth}`);
            
            // Redirect based on selected category
            if (serviceType === 'hajj') {
                window.location.href = '/packages/hajj/';
            } else if (serviceType === 'umrah') {
                window.location.href = '/packages/umrah/';
            } else {
                window.location.href = '/visa/';
            }
        });
    }
});

/* ══════════════════════════════════════════════════════════════════════
   GLOBAL QUICK BOOKING MODAL FOR CLIENTS / VISITORS (B2C WEBSITE)
   ══════════════════════════════════════════════════════════════════════ */

function openQuickBookModal(pkgId, pkgTitle, pkgPrice) {
    let modal = document.getElementById('modal-quick-book-global');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-quick-book-global';
        document.body.appendChild(modal);
    }

    const priceNum = parseFloat(pkgPrice) || 200000;
    
    modal.className = 'fixed inset-0 z-[99999] flex items-center justify-center p-4 overflow-y-auto';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.right = '0';
    modal.style.bottom = '0';
    modal.style.width = '100vw';
    modal.style.height = '100vh';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.zIndex = '99999';
    modal.style.backgroundColor = 'rgba(15, 23, 42, 0.8)';
    modal.style.backdropFilter = 'blur(6px)';
    modal.style.webkitBackdropFilter = 'blur(6px)';

    modal.classList.remove('hidden');
    modal.innerHTML = `
        <div class="bg-white border border-[#E7DCB9] rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-5 relative animate-fade-in text-left my-auto" style="margin: auto; max-height: 90vh; overflow-y: auto;">
            <button onclick="document.getElementById('modal-quick-book-global').style.display='none'" class="absolute top-5 right-5 w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-rose-500 hover:text-white flex items-center justify-center font-bold text-lg transition-all">&times;</button>
            
            <div>
                <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-black uppercase tracking-wider mb-2">
                    <i class="fa-solid fa-file-pen text-brand-orange"></i> Package Booking Form
                </span>
                <h3 class="text-xl font-extrabold text-[#2D4424] leading-snug">${pkgTitle || 'Pilgrimage Package'}</h3>
                <p class="text-xs text-[#567946] mt-0.5">Fill out your passenger contact details below to reserve your seat:</p>
            </div>

            <form id="form-quick-book-global" onsubmit="submitQuickBookModal(event, ${pkgId}, ${priceNum})" class="space-y-4 text-xs">
                <div class="p-3.5 bg-[#F7F3E9] rounded-2xl border border-[#D9CBAC] space-y-3">
                    <span class="font-extrabold text-[#2D4424] block flex items-center gap-1.5"><i class="fa-solid fa-id-card text-[#E06A26]"></i> Passenger / Client Contact Info</span>
                    <div>
                        <label class="block font-bold text-[#2D4424] mb-1">Full Name *</label>
                        <input type="text" id="qb-full-name" required placeholder="e.g. Muhammad Danish" class="w-full px-3 py-2.5 bg-white border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div class="grid grid-cols-2 gap-2.5">
                        <div>
                            <label class="block font-bold text-[#2D4424] mb-1">WhatsApp / Phone *</label>
                            <input type="tel" id="qb-phone" required placeholder="03001234567" class="w-full px-3 py-2.5 bg-white border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                        </div>
                        <div>
                            <label class="block font-bold text-[#2D4424] mb-1">Email Address *</label>
                            <input type="email" id="qb-email" required placeholder="name@example.com" class="w-full px-3 py-2.5 bg-white border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block font-bold text-[#2D4424] mb-1">Room Sharing Category</label>
                        <select id="qb-sharing" class="w-full px-3 py-2.5 bg-slate-50 border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                            <option value="Sharing" selected>Sharing Room</option>
                            <option value="Quad">Quad Sharing</option>
                            <option value="Triple">Triple Sharing</option>
                            <option value="Double">Double Sharing</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="block font-bold text-[#2D4424] mb-1">Adults (12+)</label>
                            <input type="number" id="qb-adults" value="1" min="1" max="20" class="w-full px-2 py-2.5 bg-slate-50 border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                        </div>
                        <div>
                            <label class="block font-bold text-[#2D4424] mb-1">Child (2-11)</label>
                            <input type="number" id="qb-children" value="0" min="0" max="10" class="w-full px-2 py-2.5 bg-slate-50 border border-[#D9CBAC] rounded-xl font-bold text-[#2D4424] focus:outline-none focus:border-[#E06A26]">
                        </div>
                    </div>
                </div>

                <div>
                    <label class="block font-bold text-[#2D4424] mb-1">Special Instructions / Requests (Optional)</label>
                    <textarea id="qb-notes" rows="2" placeholder="e.g. Ground floor room, wheelchair assistance required..." class="w-full px-3 py-2 bg-slate-50 border border-[#D9CBAC] rounded-xl font-semibold text-[#2D4424] focus:outline-none focus:border-[#E06A26]"></textarea>
                </div>

                <div class="pt-3 border-t border-[#E7DCB9] flex justify-end gap-2">
                    <button type="button" onclick="document.getElementById('modal-quick-book-global').style.display='none'" class="px-4 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200">Cancel</button>
                    <button type="submit" id="btn-qb-submit" class="px-6 py-2.5 bg-[#E06A26] hover:bg-[#C45517] text-white font-extrabold rounded-xl shadow-lg transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-paper-plane"></i> Submit Booking to Admin
                    </button>
                </div>
            </form>
        </div>
    `;
}

async function submitQuickBookModal(e, pkgId, basePrice) {
    e.preventDefault();
    const btn = document.getElementById('btn-qb-submit');
    const fullName = document.getElementById('qb-full-name').value.trim();
    const phone = document.getElementById('qb-phone').value.trim();
    const email = document.getElementById('qb-email').value.trim();
    const sharing = document.getElementById('qb-sharing').value;
    const adults = parseInt(document.getElementById('qb-adults').value) || 1;
    const children = parseInt(document.getElementById('qb-children').value) || 0;
    const notes = document.getElementById('qb-notes').value.trim();

    if (!fullName || !phone || !email) {
        alert('Please fill in your Full Name, Phone / WhatsApp, and Email.');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Submitting...';

    if (typeof showBookingLoadingOverlay === 'function') {
        showBookingLoadingOverlay(
            'Submitting Package Booking...',
            'Registering your pilgrimage request & reference tracking ID. Please wait.'
        );
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    try {
        const res = await fetch('/api/packages/book/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({
                package_id: pkgId,
                full_name: fullName,
                phone_number: phone,
                email: email,
                sharing_category: sharing,
                adults_count: adults,
                children_count: children,
                notes: notes
            })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById('modal-quick-book-global').style.display = 'none';
            if (typeof showSubmissionSuccessModal === 'function') {
                showSubmissionSuccessModal({
                    userName: fullName,
                    title: 'Package Booking Submitted!',
                    message: `JazakAllah Khair! Your booking for ${data.package_title} has been logged and sent to Admin B2C panel. Tracking ID: ${data.tracking_id}`,
                    trackingId: data.tracking_id,
                    details: [
                        { label: 'Package Title', value: data.package_title },
                        { label: 'Sharing Option', value: `${data.sharing_category} Sharing` },
                        { label: 'Passengers', value: `${data.adults_count} Adult(s)${data.children_count > 0 ? ', ' + data.children_count + ' Child(ren)' : ''}` },
                        { label: 'Total Fare', value: `PKR ${parseFloat(data.total_price).toLocaleString()}` }
                    ]
                });
            } else {
                alert(`🎉 Booking Successful!\n\nReference Tracking ID: ${data.tracking_id}\nPackage: ${data.package_title}\nTotal Fare: PKR ${parseFloat(data.total_price).toLocaleString()}\n\nOur pilgrimage consultant will contact you shortly on ${phone}!`);
            }
        } else {
            alert(data.message || 'Failed to submit booking. Please try again.');
        }
    } catch(err) {
        console.error('Quick book error:', err);
        alert('Network error submitting booking. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Booking to Admin';
    }
}
