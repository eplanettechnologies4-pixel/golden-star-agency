import re
import os

filepath = r"c:\Users\Administrator\Desktop\travel-agecny-main\core_admin\templates\dashboard\admin\overview.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace renderB2CFlightTickets JS in overview.html
old_render_tickets = """        function renderB2CFlightTickets() {
            const grid = document.getElementById('grid-b2c-flight-tickets');
            if (!grid) return;
            const el = (id,v) => { const e=document.getElementById(id); if(e) e.textContent=v; };

            const totalSeats = _b2cFlightTicketsData.reduce((s,t)=>s+(t.available_seats||0),0);
            const popular = _b2cFlightTicketsData.filter(t=>t.is_popular).length;
            const prices = _b2cFlightTicketsData.map(t=>Number(t.price)).filter(p=>p>0);
            const minPrice = prices.length ? Math.min(...prices) : null;

            el('stat-tickets-total', _b2cFlightTicketsData.length);
            el('stat-tickets-seats', totalSeats);
            el('stat-tickets-popular', popular);
            el('stat-tickets-minprice', minPrice ? 'PKR ' + minPrice.toLocaleString('en-PK') : '---');

            if (!_b2cFlightTicketsData.length) {
                grid.innerHTML = `<div class="p-12 text-center bg-white rounded-3xl border border-[#E7DCB9]">
                    <i class="fa-solid fa-plane-slash text-5xl text-[#D9CBAC] block mb-4"></i>
                    <div class="font-black text-[#2D4424] text-base">No Ticket Offers Yet</div>
                    <p class="text-xs text-[#567946] mt-1">Click "+ Add Flight Offer" to publish the first ticket.</p>
                </div>`;
                return;
            }

            const typeColor = t => t==='direct'?'bg-emerald-100 text-emerald-700 border-emerald-200':'bg-amber-100 text-amber-700 border-amber-200';
            const classColor = c => c==='business'?'bg-blue-100 text-blue-800 border-blue-200':c==='first'?'bg-[#FDF2EA] text-[#E06A26] border-[#FCE2D2]':'bg-[#F0F6EC] text-[#567946] border-[#C6DCB4]';
            const seatColor = s => s<=5?'text-rose-600':s<=20?'text-amber-600':'text-emerald-700';

            grid.innerHTML = _b2cFlightTicketsData.map(ft => `
                <div class="bg-white border border-[#E7DCB9] rounded-3xl shadow-sm hover:shadow-xl hover:border-[#E06A26]/50 transition-all duration-300 overflow-hidden flex flex-col lg:flex-row">
                    <!-- Airline Brand Strip -->
                    <div class="bg-[#2D4424] lg:w-48 p-5 flex flex-row lg:flex-col items-center lg:items-start justify-between lg:justify-start gap-4 shrink-0">
                        <div class="flex items-center gap-3 lg:flex-col lg:items-start">
                            <div class="w-12 h-12 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-white font-black text-lg shadow-md">
                                ${ft.airline_code ? ft.airline_code.slice(0,2).toUpperCase() : ft.airline_name.slice(0,2).toUpperCase()}
                            </div>
                            <div>
                                <div class="text-white font-extrabold text-sm leading-tight">${ft.airline_name}</div>
                                <div class="text-[#90B576] text-[10px] font-mono mt-0.5">${ft.flight_number}</div>
                            </div>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${typeColor(ft.flight_type)}">${ft.flight_type === 'direct' ? 'Non-Stop' : '1 Stop'}</span>
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${classColor(ft.ticket_class)}">${ft.ticket_class}</span>
                            ${ft.is_popular ? '<span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-[#E06A26] text-white border border-[#C45517]">&#9733; Popular</span>' : ''}
                        </div>
                    </div>

                    <!-- Route Boarding Pass Block -->
                    <div class="flex-1 p-5 flex flex-col gap-4">
                        <!-- Route Visual -->
                        <div class="bg-[#F7F3E9] rounded-2xl p-4 border border-[#E7DCB9] flex items-center justify-between gap-4">
                            <!-- Departure -->
                            <div class="text-left">
                                <div class="text-3xl font-black text-[#2D4424] tracking-tight">${ft.departure_airport_code || ft.departure_city.slice(0,3).toUpperCase()}</div>
                                <div class="text-[11px] text-[#567946] font-semibold mt-0.5">${ft.departure_city}</div>
                                <div class="text-[11px] text-[#E06A26] font-bold mt-1">&#9200; ${ft.departure_time_str}</div>
                            </div>
                            <!-- Flight Path -->
                            <div class="flex-1 text-center px-2">
                                <div class="text-[9px] text-[#567946] font-bold uppercase tracking-wider">${ft.duration_str || ''}</div>
                                <div class="relative my-2">
                                    <div class="h-0.5 bg-gradient-to-r from-[#E06A26]/40 via-[#567946]/60 to-emerald-400/40 rounded-full"></div>
                                    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white border-2 border-[#E06A26] rounded-full flex items-center justify-center shadow">
                                        <i class="fa-solid fa-plane text-[#E06A26] text-[9px]"></i>
                                    </div>
                                </div>
                                <div class="text-[9px] text-emerald-600 font-bold uppercase tracking-widest">${ft.flight_type==='direct'?'NON-STOP':'1 STOP'}</div>
                            </div>
                            <!-- Arrival -->
                            <div class="text-right">
                                <div class="text-3xl font-black text-[#2D4424] tracking-tight">${ft.destination_airport_code || ft.destination_city.slice(0,3).toUpperCase()}</div>
                                <div class="text-[11px] text-[#567946] font-semibold mt-0.5">${ft.destination_city}</div>
                                <div class="text-[11px] text-[#E06A26] font-bold mt-1">&#9200; ${ft.arrival_time_str}</div>
                            </div>
                        </div>

                        <!-- Details Grid -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Check-in Baggage</div>
                                <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-suitcase-rolling text-blue-500 text-[10px]"></i>${ft.baggage_checkin || '30 kg'}
                                </div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Hand Carry</div>
                                <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-briefcase text-purple-500 text-[10px]"></i>${ft.baggage_hand || '7 kg'}
                                </div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Seats Available</div>
                                <div class="font-extrabold text-xs ${seatColor(ft.available_seats)}">${ft.available_seats} <span class="text-[#567946] font-semibold">/ ${ft.total_seats}</span></div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Refundable</div>
                                <div class="font-extrabold text-xs ${ft.is_refundable ? 'text-emerald-700' : 'text-rose-600'}">${ft.is_refundable ? 'Yes' : 'No'}</div>
                            </div>
                        </div>

                        <!-- Baggage Tier Pricing -->
                        <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                            <div class="text-[9px] text-[#567946] uppercase font-bold mb-2 flex items-center gap-1">
                                <i class="fa-solid fa-weight-hanging text-[#E06A26]"></i> Baggage Tier Prices
                            </div>
                            <div class="flex flex-wrap gap-2 text-[10px]">
                                <span class="bg-[#E06A26] text-white px-3 py-1 rounded-lg font-black">20 KG — PKR ${Number(ft.price_20kg||ft.price).toLocaleString('en-PK')}</span>
                                <span class="bg-white border border-[#D9CBAC] text-[#2D4424] px-3 py-1 rounded-lg font-bold">30 KG — PKR ${Number(ft.price_30kg||(Number(ft.price)+15000)).toLocaleString('en-PK')}</span>
                                <span class="bg-white border border-[#D9CBAC] text-[#2D4424] px-3 py-1 rounded-lg font-bold">40 KG — PKR ${Number(ft.price_40kg||(Number(ft.price)+30000)).toLocaleString('en-PK')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Price & Actions -->
                    <div class="border-t lg:border-t-0 lg:border-l border-[#E7DCB9] p-5 flex flex-row lg:flex-col items-center lg:items-end justify-between lg:justify-center gap-3 shrink-0 lg:w-48">
                        <div class="text-right">
                            <div class="text-[10px] text-[#567946] uppercase font-bold">Base Fare</div>
                            <div class="text-2xl font-black text-[#E06A26]">PKR ${Number(ft.price).toLocaleString('en-PK')}</div>
                            ${ft.original_price ? '<div class="text-xs text-[#D9CBAC] line-through font-semibold">PKR '+Number(ft.original_price).toLocaleString('en-PK')+'</div>' : ''}
                            <div class="text-[9px] text-[#567946] mt-0.5">ID: #${ft.id}</div>
                        </div>
                        <div class="flex flex-col gap-2">
                            <button onclick="deleteB2CFlightTicket(${ft.id})" class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-600 text-[10px] font-bold rounded-xl border border-rose-200 flex items-center gap-1.5 transition-all">
                                <i class="fa-solid fa-trash-alt"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }"""

new_render_tickets = """        function renderB2CFlightTickets() {
            const grid = document.getElementById('grid-b2c-flight-tickets');
            if (!grid) return;
            const el = (id,v) => { const e=document.getElementById(id); if(e) e.textContent=v; };

            const totalSeats = _b2cFlightTicketsData.reduce((s,t)=>s+(t.available_seats||0),0);
            const popular = _b2cFlightTicketsData.filter(t=>t.is_popular).length;
            const prices = _b2cFlightTicketsData.map(t=>Number(t.price)).filter(p=>p>0);
            const minPrice = prices.length ? Math.min(...prices) : null;

            el('stat-tickets-total', _b2cFlightTicketsData.length);
            el('stat-tickets-seats', totalSeats);
            el('stat-tickets-popular', popular);
            el('stat-tickets-minprice', minPrice ? 'PKR ' + minPrice.toLocaleString('en-PK') : '---');

            if (!_b2cFlightTicketsData.length) {
                grid.innerHTML = `<div class="p-12 text-center bg-white rounded-3xl border border-[#E7DCB9]">
                    <i class="fa-solid fa-plane-slash text-5xl text-[#D9CBAC] block mb-4"></i>
                    <div class="font-black text-[#2D4424] text-base">No Ticket Offers Yet</div>
                    <p class="text-xs text-[#567946] mt-1">Click "+ Add Flight Offer" to publish the first ticket.</p>
                </div>`;
                return;
            }

            const typeColor = t => t==='direct'?'bg-emerald-100 text-emerald-700 border-emerald-200':'bg-amber-100 text-amber-700 border-amber-200';
            const classColor = c => c==='business'?'bg-blue-100 text-blue-800 border-blue-200':c==='first'?'bg-[#FDF2EA] text-[#E06A26] border-[#FCE2D2]':'bg-[#F0F6EC] text-[#567946] border-[#C6DCB4]';
            const seatColor = s => s<=5?'text-rose-600':s<=20?'text-amber-600':'text-emerald-700';

            grid.innerHTML = _b2cFlightTicketsData.map(ft => `
                <div class="bg-white border border-[#E7DCB9] rounded-3xl shadow-sm hover:shadow-xl hover:border-[#E06A26]/50 transition-all duration-300 overflow-hidden flex flex-col lg:flex-row">
                    <!-- Airline Brand Strip -->
                    <div class="bg-[#2D4424] lg:w-48 p-5 flex flex-row lg:flex-col items-center lg:items-start justify-between lg:justify-start gap-4 shrink-0">
                        <div class="flex items-center gap-3 lg:flex-col lg:items-start">
                            ${ft.airline_logo ? `<img src="${ft.airline_logo}" alt="${ft.airline_name}" class="w-12 h-12 object-contain rounded-2xl bg-white p-1">` : `
                                <div class="w-12 h-12 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-white font-black text-lg shadow-md">
                                    ${ft.airline_code ? ft.airline_code.slice(0,2).toUpperCase() : ft.airline_name.slice(0,2).toUpperCase()}
                                </div>
                            `}
                            <div>
                                <div class="text-white font-extrabold text-sm leading-tight">${ft.airline_name}</div>
                                <div class="text-[#90B576] text-[10px] font-mono mt-0.5">${ft.flight_number}</div>
                            </div>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${typeColor(ft.flight_type)}">${ft.flight_type === 'direct' ? 'Non-Stop' : 'Via / Transit'}</span>
                            <span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${classColor(ft.ticket_class)}">${ft.ticket_class}</span>
                            ${ft.has_meal ? '<span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-emerald-700 text-white border border-emerald-800">🍲 Meal Included</span>' : '<span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-slate-700 text-white border border-slate-800">🚫 No Meal</span>'}
                            ${ft.is_popular ? '<span class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-[#E06A26] text-white border border-[#C45517]">&#9733; Popular</span>' : ''}
                        </div>
                    </div>

                    <!-- Route Boarding Pass Block -->
                    <div class="flex-1 p-5 flex flex-col gap-4">
                        <!-- Route Visual -->
                        <div class="bg-[#F7F3E9] rounded-2xl p-4 border border-[#E7DCB9] flex flex-col gap-3">
                            <div class="flex items-center justify-between gap-4">
                                <!-- Departure -->
                                <div class="text-left">
                                    <div class="text-3xl font-black text-[#2D4424] tracking-tight">${ft.departure_airport_code || ft.departure_city.slice(0,3).toUpperCase()}</div>
                                    <div class="text-[11px] text-[#567946] font-semibold mt-0.5">${ft.departure_city}</div>
                                    <div class="text-[11px] text-[#E06A26] font-bold mt-1">&#9200; ${ft.departure_time_str}</div>
                                </div>
                                <!-- Flight Path -->
                                <div class="flex-1 text-center px-2">
                                    <div class="text-[9px] text-[#567946] font-bold uppercase tracking-wider">${ft.duration_str || ''}</div>
                                    <div class="relative my-2">
                                        <div class="h-0.5 bg-gradient-to-r from-[#E06A26]/40 via-[#567946]/60 to-emerald-400/40 rounded-full"></div>
                                        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white border-2 border-[#E06A26] rounded-full flex items-center justify-center shadow">
                                            <i class="fa-solid fa-plane text-[#E06A26] text-[9px]"></i>
                                        </div>
                                    </div>
                                    <div class="text-[9px] text-emerald-600 font-bold uppercase tracking-widest">${ft.flight_type==='direct'?'NON-STOP':'TRANSIT VIA ROUTE'}</div>
                                </div>
                                <!-- Arrival -->
                                <div class="text-right">
                                    <div class="text-3xl font-black text-[#2D4424] tracking-tight">${ft.destination_airport_code || ft.destination_city.slice(0,3).toUpperCase()}</div>
                                    <div class="text-[11px] text-[#567946] font-semibold mt-0.5">${ft.destination_city}</div>
                                    <div class="text-[11px] text-[#E06A26] font-bold mt-1">&#9200; ${ft.arrival_time_str}</div>
                                </div>
                            </div>
                            ${ft.via_routes ? `
                                <div class="bg-white/80 border border-[#E7DCB9] p-2 rounded-xl text-[10px] text-[#2D4424] font-bold flex items-center gap-1.5">
                                    <i class="fa-solid fa-route text-[#E06A26]"></i> <span class="text-[#567946] uppercase font-extrabold">Via Route Segments:</span> ${ft.via_routes}
                                </div>
                            ` : ''}
                        </div>

                        <!-- Details Grid -->
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Check-in Baggage</div>
                                <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-suitcase-rolling text-blue-500 text-[10px]"></i>${ft.baggage_checkin || '30 kg'}
                                </div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Hand Carry</div>
                                <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                                    <i class="fa-solid fa-briefcase text-purple-500 text-[10px]"></i>${ft.baggage_hand || '7 kg'}
                                </div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">In-Flight Meals</div>
                                <div class="font-extrabold text-xs ${ft.has_meal ? 'text-emerald-700' : 'text-slate-600'} flex items-center gap-1">
                                    <i class="fa-solid fa-utensils text-[10px]"></i>${ft.meal_service || (ft.has_meal ? 'Meal Included' : 'No Meal')}
                                </div>
                            </div>
                            <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                                <div class="text-[9px] text-[#567946] uppercase font-bold mb-1">Seats Available</div>
                                <div class="font-extrabold text-xs ${seatColor(ft.available_seats)}">${ft.available_seats} <span class="text-[#567946] font-semibold">/ ${ft.total_seats}</span></div>
                            </div>
                        </div>

                        <!-- Baggage & Fare Tier Options Allotment -->
                        <div class="bg-[#F7F3E9] p-3 rounded-xl border border-[#E7DCB9]">
                            <div class="text-[9px] text-[#567946] uppercase font-bold mb-2 flex items-center gap-1">
                                <i class="fa-solid fa-tags text-[#E06A26]"></i> Allotted Baggage Fares Listing
                            </div>
                            <div class="flex flex-wrap gap-2 text-[10px]">
                                ${ft.price_handcarry ? `<span class="bg-slate-800 text-white px-3 py-1 rounded-lg font-black">Hand Carry Only — PKR ${Number(ft.price_handcarry).toLocaleString('en-PK')}</span>` : ''}
                                <span class="bg-[#E06A26] text-white px-3 py-1 rounded-lg font-black">20 KG — PKR ${Number(ft.price_20kg||ft.price).toLocaleString('en-PK')}</span>
                                <span class="bg-white border border-[#D9CBAC] text-[#2D4424] px-3 py-1 rounded-lg font-bold">30 KG — PKR ${Number(ft.price_30kg||(Number(ft.price)+15000)).toLocaleString('en-PK')}</span>
                                <span class="bg-white border border-[#D9CBAC] text-[#2D4424] px-3 py-1 rounded-lg font-bold">40 KG — PKR ${Number(ft.price_40kg||(Number(ft.price)+30000)).toLocaleString('en-PK')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Price & Actions -->
                    <div class="border-t lg:border-t-0 lg:border-l border-[#E7DCB9] p-5 flex flex-row lg:flex-col items-center lg:items-end justify-between lg:justify-center gap-3 shrink-0 lg:w-48">
                        <div class="text-right">
                            <div class="text-[10px] text-[#567946] uppercase font-bold">Starting Fare</div>
                            <div class="text-2xl font-black text-[#E06A26]">PKR ${Number(ft.price).toLocaleString('en-PK')}</div>
                            ${ft.original_price ? '<div class="text-xs text-[#D9CBAC] line-through font-semibold">PKR '+Number(ft.original_price).toLocaleString('en-PK')+'</div>' : ''}
                            <div class="text-[9px] text-[#567946] mt-0.5">ID: #${ft.id}</div>
                        </div>
                        <div class="flex flex-col gap-2">
                            <button onclick="deleteB2CFlightTicket(${ft.id})" class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-600 text-[10px] font-bold rounded-xl border border-rose-200 flex items-center gap-1.5 transition-all">
                                <i class="fa-solid fa-trash-alt"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }"""

if old_render_tickets in content:
    content = content.replace(old_render_tickets, new_render_tickets)
    print("Replaced renderB2CFlightTickets successfully!")
else:
    print("old_render_tickets not found")

# Replace modal-add-b2c-flight form in overview.html
modal_start = '<form id="form-add-b2c-flight" onsubmit="submitAddB2CFlight(event)" class="space-y-4 text-xs">'
modal_end = '</form>'

m_idx1 = content.find(modal_start)
m_idx2 = content.find(modal_end, m_idx1)

if m_idx1 != -1 and m_idx2 != -1:
    new_modal_content = """<form id="form-add-b2c-flight" onsubmit="submitAddB2CFlight(event)" class="space-y-4 text-xs">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Airline Name *</label>
                        <input type="text" name="airline_name" required placeholder="e.g. Saudi Arabian Airlines" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Flight Number *</label>
                        <input type="text" name="flight_number" required placeholder="e.g. SV-705" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Departure City *</label>
                        <input type="text" name="departure_city" required placeholder="Karachi (KHI)" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Departure Airport Code</label>
                        <input type="text" name="departure_airport_code" placeholder="e.g. KHI" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26] uppercase">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Destination City *</label>
                        <input type="text" name="destination_city" required placeholder="Jeddah (JED)" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Destination Airport Code</label>
                        <input type="text" name="destination_airport_code" placeholder="e.g. JED" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26] uppercase">
                    </div>

                    <!-- Flight Type: Direct vs Via -->
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Flight Type *</label>
                        <select name="flight_type" id="add-flight-type-select" onchange="toggleViaRouteFields(this.value)" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26] bg-white font-bold">
                            <option value="direct">Direct (Non-Stop)</option>
                            <option value="one_stop">Via / Connecting (Transit)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Ticket Class</label>
                        <select name="ticket_class" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26] bg-white font-bold">
                            <option value="economy">Economy Class</option>
                            <option value="business">Business Class</option>
                            <option value="first">First Class</option>
                        </select>
                    </div>

                    <!-- In-Flight Meal Option -->
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">In-Flight Meal Option *</label>
                        <select name="has_meal" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26] bg-white font-bold">
                            <option value="true">🍲 Meal Included</option>
                            <option value="false">🚫 No Meal (Paid/None)</option>
                        </select>
                    </div>

                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Meal Service Description</label>
                        <input type="text" name="meal_service" value="Hot Meal & Drinks Included" placeholder="e.g. Hot Meal Included" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                </div>

                <!-- Via Route Segments (Up to 4 Routes) -->
                <div id="via-routes-container" class="space-y-2 bg-[#F8FAF6] p-4 rounded-2xl border border-[#E7DCB9] hidden">
                    <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-route text-[#E06A26]"></i> Via / Transit Route Segments (Up to 4 Routes)
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <input type="text" name="via_route1" placeholder="Segment 1: e.g. KHI → MCT" class="px-3 py-1.5 border border-[#D9CBAC] rounded-lg">
                        <input type="text" name="via_route2" placeholder="Segment 2: e.g. MCT → DXB" class="px-3 py-1.5 border border-[#D9CBAC] rounded-lg">
                        <input type="text" name="via_route3" placeholder="Segment 3: e.g. DXB → MED" class="px-3 py-1.5 border border-[#D9CBAC] rounded-lg">
                        <input type="text" name="via_route4" placeholder="Segment 4: e.g. MED → JED" class="px-3 py-1.5 border border-[#D9CBAC] rounded-lg">
                    </div>
                </div>

                <!-- Allotted Baggage Fares Listing -->
                <div class="bg-[#FDF2EA] p-4 rounded-2xl border border-[#FCE2D2] space-y-3">
                    <div class="font-extrabold text-[#2D4424] text-xs flex items-center gap-1.5">
                        <i class="fa-solid fa-tags text-[#E06A26]"></i> Allotted Fares by Baggage Allowance
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                        <div>
                            <label class="block font-bold text-[#567946] text-[10px] uppercase mb-1">Hand Carry Fare (PKR)</label>
                            <input type="number" step="0.01" name="price_handcarry" placeholder="110000" class="w-full px-3 py-1.5 border border-[#D9CBAC] rounded-xl bg-white">
                        </div>
                        <div>
                            <label class="block font-bold text-[#567946] text-[10px] uppercase mb-1">20 KG Fare (PKR) *</label>
                            <input type="number" step="0.01" name="price" required placeholder="145000" class="w-full px-3 py-1.5 border border-[#D9CBAC] rounded-xl bg-white font-bold text-[#E06A26]">
                        </div>
                        <div>
                            <label class="block font-bold text-[#567946] text-[10px] uppercase mb-1">30 KG Fare (PKR)</label>
                            <input type="number" step="0.01" name="price_30kg" placeholder="160000" class="w-full px-3 py-1.5 border border-[#D9CBAC] rounded-xl bg-white">
                        </div>
                        <div>
                            <label class="block font-bold text-[#567946] text-[10px] uppercase mb-1">40 KG Fare (PKR)</label>
                            <input type="number" step="0.01" name="price_40kg" placeholder="175000" class="w-full px-3 py-1.5 border border-[#D9CBAC] rounded-xl bg-white">
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Departure Time</label>
                        <input type="text" name="departure_time_str" value="03:30 AM" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Arrival Time</label>
                        <input type="text" name="arrival_time_str" value="06:45 AM" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                    <div>
                        <label class="block font-extrabold text-[#2D4424] mb-1">Total Seats Available</label>
                        <input type="number" name="total_seats" value="50" class="w-full px-3 py-2 border border-[#D9CBAC] rounded-xl focus:outline-none focus:border-[#E06A26]">
                    </div>
                </div>

                <div class="flex justify-end gap-3 pt-4 border-t border-[#E7DCB9]">
                    <button type="button" onclick="closeAddB2CFlightModal()" class="px-4 py-2 bg-[#F7F3E9] hover:bg-[#EBD8B3] border border-[#D9CBAC] text-[#2D4424] font-bold rounded-xl">Cancel</button>
                    <button type="submit" class="px-5 py-2 bg-[#E06A26] hover:bg-[#C45517] text-white font-bold rounded-xl shadow-md">+ Publish Flight Ticket Offer</button>
                </div>"""
    content = content[:m_idx1] + new_modal_content + content[m_idx2:]
    print("Replaced modal-add-b2c-flight form successfully!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Modal & Cards updated!")
