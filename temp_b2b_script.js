
        // ─────────────────────────────────────────────────────────────
        // ⚡ B2B AGENT FEEDBACK MANAGEMENT JS
        // ─────────────────────────────────────────────────────────────
        let allAdminFeedbacksData = [];
        let currentAdminFeedbackFilter = '';

        async function fetchAdminAgentFeedbacks() {
            try {
                const res = await fetch('/dashboard/admin/api/feedbacks/');
                const data = await res.json();
                if (data.success && data.feedbacks) {
                    allAdminFeedbacksData = data.feedbacks;
                    
                    const badge = document.getElementById("badge-admin-feedbacks-pending");
                    if (badge) {
                        badge.textContent = data.pending_count || 0;
                        if (data.pending_count > 0) badge.classList.remove("hidden");
                        else badge.classList.add("hidden");
                    }

                    renderAdminAgentFeedbacks();
                }
            } catch (err) {
                console.error("Error fetching agent feedbacks for admin:", err);
            }
        }

        function filterAdminFeedbacks(status) {
            currentAdminFeedbackFilter = status;
            document.querySelectorAll('.fb-filter-btn').forEach(btn => {
                btn.classList.remove('bg-[#E06A26]', 'text-white');
                btn.classList.add('bg-[#F7F3E9]', 'text-[#2D4424]', 'border', 'border-[#D9CBAC]');
            });
            const activeBtn = document.getElementById(`btn-fb-filter-${status || 'all'}`);
            if (activeBtn) {
                activeBtn.classList.remove('bg-[#F7F3E9]', 'text-[#2D4424]', 'border', 'border-[#D9CBAC]');
                activeBtn.classList.add('bg-[#E06A26]', 'text-white');
            }
            renderAdminAgentFeedbacks();
        }

        let adminFbDebounceTimer = null;
        function debounceAdminAgentFeedbacksSearch() {
            clearTimeout(adminFbDebounceTimer);
            adminFbDebounceTimer = setTimeout(renderAdminAgentFeedbacks, 250);
        }

        function renderAdminAgentFeedbacks() {
            const tbody = document.getElementById("tbody-admin-agent-feedbacks");
            if (!tbody) return;

            let items = allAdminFeedbacksData;
            if (currentAdminFeedbackFilter) {
                items = items.filter(f => f.status === currentAdminFeedbackFilter);
            }

            const search = (document.getElementById("admin-fb-search-input")?.value || "").toLowerCase().trim();
            if (search) {
                items = items.filter(f =>
                    f.agent_company.toLowerCase().includes(search) ||
                    f.agent_name.toLowerCase().includes(search) ||
                    f.subject.toLowerCase().includes(search) ||
                    f.message.toLowerCase().includes(search)
                );
            }

            if (items.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-[#567946] font-semibold">No agent feedbacks match criteria.</td></tr>`;
                return;
            }

            tbody.innerHTML = items.map(f => {
                let badgeClass = "bg-[#FBF5E8] text-[#7A5C28] border-[#EADBB8]";
                if (f.status === 'reviewed') badgeClass = "bg-sky-50 text-sky-800 border-sky-200";
                else if (f.status === 'resolved') badgeClass = "bg-[#F0F6EC] text-[#38522D] border-[#C6DCB4]";
                else if (f.status === 'closed') badgeClass = "bg-gray-100 text-gray-700 border-gray-200";

                let starsHtml = '';
                for (let i = 1; i <= 5; i++) {
                    starsHtml += `<i class="fa-solid fa-star text-xs ${i <= f.rating ? 'text-amber-400' : 'text-gray-300'}"></i>`;
                }

                return `
                    <tr class="hover:bg-[#F8FAF6] transition-colors border-b border-[#E7DCB9]">
                        <td class="px-6 py-4 font-mono text-[10px] text-[#567946]">${f.created_at}</td>
                        <td class="px-6 py-4 font-bold text-[#2D4424]">
                            <div>${escapeHTML(f.agent_company)}</div>
                            <div class="text-[10px] text-[#567946] font-normal">${escapeHTML(f.agent_name)}</div>
                        </td>
                        <td class="px-6 py-4">
                            <span class="px-2 py-0.5 bg-[#F7F3E9] text-[#2D4424] text-[10px] font-extrabold uppercase rounded-lg border border-[#D9CBAC] block w-max mb-1">${escapeHTML(f.category_display)}</span>
                            <div class="flex items-center space-x-1">${starsHtml}</div>
                        </td>
                        <td class="px-6 py-4 max-w-xs">
                            <div class="font-bold text-[#2D4424] truncate">${escapeHTML(f.subject)}</div>
                            <div class="text-[11px] text-[#567946] line-clamp-2">${escapeHTML(f.message)}</div>
                        </td>
                        <td class="px-6 py-4">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase border ${badgeClass}">${escapeHTML(f.status_display)}</span>
                        </td>
                        <td class="px-6 py-4 text-right">
                            <div class="flex items-center justify-end gap-1.5">
                                <button onclick="openAdminReplyFeedbackModal(${f.id})" class="px-3 py-1.5 bg-[#2D4424] hover:bg-[#1F2E1A] text-white text-[11px] font-bold rounded-xl shadow-sm transition-all flex items-center gap-1">
                                    <i class="fa-solid fa-reply"></i> Reply / Status
                                </button>
                                <button onclick="deleteAdminFeedback(${f.id})" class="p-1.5 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-xl border border-rose-200 transition-all" title="Delete Feedback">
                                    <i class="fa-solid fa-trash text-xs"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function openAdminReplyFeedbackModal(id) {
            const item = allAdminFeedbacksData.find(f => f.id === id);
            if (!item) return;

            document.getElementById("admin-fb-modal-id").value = item.id;
            document.getElementById("admin-fb-modal-agent").textContent = item.agent_company;
            document.getElementById("admin-fb-modal-date").textContent = item.created_at;
            document.getElementById("admin-fb-modal-subject").textContent = item.subject;
            document.getElementById("admin-fb-modal-message").textContent = item.message;
            document.getElementById("admin-fb-modal-status").value = item.status;
            document.getElementById("admin-fb-modal-reply").value = item.admin_reply || "";

            const modal = document.getElementById("modal-admin-reply-feedback");
            if (modal) {
                modal.classList.remove("hidden");
                modal.classList.add("flex");
            }
        }

        function closeAdminReplyFeedbackModal() {
            const modal = document.getElementById("modal-admin-reply-feedback");
            if (modal) {
                modal.classList.remove("flex");
                modal.classList.add("hidden");
            }
        }

        async function submitAdminFeedbackReply() {
            const id = document.getElementById("admin-fb-modal-id").value;
            const status = document.getElementById("admin-fb-modal-status").value;
            const adminReply = document.getElementById("admin-fb-modal-reply").value.trim();

            try {
                const res = await fetch(`/dashboard/admin/api/feedbacks/${id}/status/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: status, admin_reply: adminReply })
                });

                const data = await res.json();
                if (data.success) {
                    alert("Feedback status & response saved!");
                    closeAdminReplyFeedbackModal();
                    fetchAdminAgentFeedbacks();
                } else {
                    alert(data.error || "Failed to update feedback.");
                }
            } catch (err) {
                console.error("Error updating feedback:", err);
                alert("Server error updating feedback.");
            }
        }

        async function deleteAdminFeedback(id) {
            if (!confirm("Are you sure you want to delete this agent feedback entry?")) return;
            try {
                const res = await fetch(`/dashboard/admin/api/feedbacks/${id}/delete/`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    fetchAdminAgentFeedbacks();
                } else {
                    alert(data.error || "Failed to delete feedback.");
                }
            } catch (err) {
                console.error("Error deleting feedback:", err);
                alert("Server error deleting feedback.");
            }
        }

        // ══════════════ COMPANY OFFICIAL BANK ACCOUNTS LOGIC ══════════════
        async function fetchAdminBankAccounts() {
            try {
                const res = await fetch("/dashboard/admin/api/bank-accounts/");
                const data = await res.json();
                const tbody = document.getElementById("tbody-admin-bank-accounts");
                if (!tbody) return;

                const accounts = data.bank_accounts || data.accounts || [];

                if (accounts.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" class="px-6 py-8 text-center text-[#567946]">No company bank accounts registered. Click "+ Add New Bank Account" to create one.</td></tr>`;
                    return;
                }

                tbody.innerHTML = accounts.map(b => `
                    <tr class="hover:bg-[#F6FAF3] transition-colors border-b border-[#E7DCB9]">
                        <td class="px-6 py-4 font-black text-[#2D4424] text-xs">
                            <i class="fa-solid fa-building-columns text-[#E06A26] mr-1.5"></i> ${escapeHTML(b.bank_name)}
                        </td>
                        <td class="px-6 py-4 text-xs font-bold text-[#1F2E1A]">${escapeHTML(b.account_title)}</td>
                        <td class="px-6 py-4 font-mono font-bold text-xs text-[#2D4424]">${escapeHTML(b.account_number)}</td>
                        <td class="px-6 py-4 font-mono text-xs text-[#E06A26]">${escapeHTML(b.iban || 'N/A')}</td>
                        <td class="px-6 py-4 text-xs text-[#567946]">${escapeHTML(b.branch_code || 'N/A')}</td>
                        <td class="px-6 py-4">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${b.is_active ? 'bg-[#F0F6EC] text-[#38522D] border border-[#C6DCB4]' : 'bg-slate-100 text-slate-500 border border-slate-300'}">
                                ${b.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-right space-x-2">
                            <button onclick='openEditBankAccountModal(${JSON.stringify(b).replace(/'/g, "&apos;")})'  class="px-3 py-1 bg-white hover:bg-[#F7F3E9] text-[#2D4424] text-xs font-bold rounded-lg border border-[#D9CBAC] transition-all">Edit</button>
                            <button onclick="deleteAdminBankAccount(${b.id})" class="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-bold rounded-lg border border-rose-200 transition-all">Delete</button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Error fetching bank accounts:", err);
            }
        }

        function openAddBankAccountModal() {
            const modal = document.getElementById('modal-bank-account');
            const title = document.getElementById('modal-bank-account-title');
            const bankAccId = document.getElementById('bank-acc-id');
            const bankAccName = document.getElementById('bank-acc-name');
            const bankAccTitle = document.getElementById('bank-acc-title');
            const bankAccNumber = document.getElementById('bank-acc-number');
            const bankAccIban = document.getElementById('bank-acc-iban');
            const bankAccBranchCode = document.getElementById('bank-acc-branch-code');
            const bankAccBranchName = document.getElementById('bank-acc-branch-name');
            const bankAccSwift = document.getElementById('bank-acc-swift');
            const bankAccActive = document.getElementById('bank-acc-active');

            if (!modal || !title || !bankAccId || !bankAccName || !bankAccTitle || !bankAccNumber || !bankAccIban || !bankAccBranchCode || !bankAccBranchName || !bankAccSwift || !bankAccActive) {
                console.error('openAddBankAccountModal: missing bank account modal elements', {
                    modal, title, bankAccId, bankAccName, bankAccTitle, bankAccNumber, bankAccIban, bankAccBranchCode, bankAccBranchName, bankAccSwift, bankAccActive
                });
                return;
            }

            title.innerHTML = '<i class="fa-solid fa-building-columns text-[#E06A26]"></i> Add Company Bank Account';
            bankAccId.value = '';
            bankAccName.value = '';
            bankAccTitle.value = '';
            bankAccNumber.value = '';
            bankAccIban.value = '';
            bankAccBranchCode.value = '';
            bankAccBranchName.value = '';
            bankAccSwift.value = '';
            bankAccActive.checked = true;
            openModal('modal-bank-account');
        }

        function closeBankAccountModal() {
            closeModal('modal-bank-account');
        }

        function openEditBankAccountModal(acc) {
            document.getElementById('modal-bank-account-title').innerHTML = '<i class="fa-solid fa-pen-to-square text-[#E06A26]"></i> Edit Bank Account';
            document.getElementById('bank-acc-id').value = acc.id;
            document.getElementById('bank-acc-name').value = acc.bank_name || '';
            document.getElementById('bank-acc-title').value = acc.account_title || '';
            document.getElementById('bank-acc-number').value = acc.account_number || '';
            document.getElementById('bank-acc-iban').value = acc.iban || '';
            document.getElementById('bank-acc-branch-code').value = acc.branch_code || '';
            document.getElementById('bank-acc-branch-name').value = acc.branch_name || '';
            document.getElementById('bank-acc-swift').value = acc.swift_code || '';
            document.getElementById('bank-acc-active').checked = acc.is_active !== false;
            openModal('modal-bank-account');
        }

        async function submitAdminBankAccountForm(e) {
            e.preventDefault();
            const form = document.getElementById('form-admin-bank-account');
            const accId = document.getElementById('bank-acc-id').value;
            const formData = new FormData(form);
            const url = accId ? `/dashboard/admin/api/bank-accounts/${accId}/` : `/dashboard/admin/api/bank-accounts/`;
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData
                });
                const data = await res.json();
                if (data.success) {
                    alert(accId ? 'Bank account updated successfully!' : 'Bank account added successfully!');
                    closeBankAccountModal();
                    fetchAdminBankAccounts();
                } else {
                    alert(data.message || data.error || 'Failed to save bank account.');
                }
            } catch (err) {
                alert('Error connecting to server to save bank account.');
            }
        }

        async function deleteAdminBankAccount(accId) {
            if (!confirm('Are you sure you want to delete this bank account?')) return;
            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
                const res = await fetch(`/dashboard/admin/api/bank-accounts/${accId}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                const data = await res.json();
                if (data.success) {
                    alert('Bank account deleted successfully!');
                    fetchAdminBankAccounts();
                } else {
                    alert(data.message || 'Failed to delete bank account.');
                }
            } catch (err) {
                alert('Error connecting to server to delete bank account.');
            }
        }

        // ══════════════ COMPANY DEPARTMENT CONTACTS DIRECTORY LOGIC ══════════════
        async function fetchAdminDepartmentContacts() {
            try {
                const res = await fetch("/dashboard/admin/api/department-contacts/");
                const data = await res.json();
                const tbody = document.getElementById("tbody-admin-dept-contacts");
                if (!tbody) return;

                const contacts = data.contacts || [];

                if (contacts.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" class="px-6 py-8 text-center text-[#567946]">No department contacts added yet. Click "+ Add New Department Contact" to create one.</td></tr>`;
                    return;
                }

                tbody.innerHTML = contacts.map(c => `
                    <tr class="hover:bg-[#F6FAF3] transition-colors border-b border-[#E7DCB9]">
                        <td class="px-6 py-4 font-black text-[#2D4424] text-xs">
                            <i class="fa-solid fa-sitemap text-[#E06A26] mr-1.5"></i> ${escapeHTML(c.department_name)}
                        </td>
                        <td class="px-6 py-4 text-xs">
                            <strong class="text-[#1F2E1A] font-bold block">${escapeHTML(c.contact_person_name || 'N/A')}</strong>
                            <span class="text-[10px] text-[#567946]">${escapeHTML(c.designation || '')}</span>
                        </td>
                        <td class="px-6 py-4 font-mono font-bold text-xs text-[#2D4424]">
                            <div>${escapeHTML(c.phone_number)}</div>
                            ${c.whatsapp_number ? `<div class="text-[#25D366] text-[10px]"><i class="fa-brands fa-whatsapp mr-1"></i>${escapeHTML(c.whatsapp_number)}</div>` : ''}
                        </td>
                        <td class="px-6 py-4 text-xs font-mono text-[#E06A26]">${escapeHTML(c.email || 'N/A')}</td>
                        <td class="px-6 py-4 text-xs text-[#567946] max-w-xs truncate">${escapeHTML(c.description || 'N/A')}</td>
                        <td class="px-6 py-4">
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${c.is_active ? 'bg-[#F0F6EC] text-[#38522D] border border-[#C6DCB4]' : 'bg-slate-100 text-slate-500 border border-slate-300'}">
                                ${c.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-right space-x-2">
                            <button onclick="editDepartmentContact(${c.id})" class="px-3 py-1 bg-white hover:bg-[#F7F3E9] text-[#2D4424] text-xs font-bold rounded-lg border border-[#D9CBAC] transition-all">Edit</button>
                            <button onclick="deleteDepartmentContact(${c.id})" class="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-bold rounded-lg border border-rose-200 transition-all">Delete</button>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                console.error("Error fetching department contacts:", err);
            }
        }

        function openAddDepartmentContactModal() {
            const form = document.getElementById("dept-contact-form");
            const deptId = document.getElementById("dept-contact-id");
            const modalTitle = document.getElementById("modal-dept-contact-title");
            const modal = document.getElementById('modal-admin-dept-contact');

            if (!form || !deptId || !modalTitle || !modal) {
                console.error('openAddDepartmentContactModal: missing department contact modal elements', { form, deptId, modalTitle, modal });
                return;
            }

            form.reset();
            deptId.value = "";
            modalTitle.textContent = "Add New Department Contact";
            openModal('modal-admin-dept-contact');
        }

        async function editDepartmentContact(id) {
            try {
                const res = await fetch("/dashboard/admin/api/department-contacts/");
                const data = await res.json();
                const contact = (data.contacts || []).find(c => c.id === id);
                if (!contact) return;

                document.getElementById("dept-contact-id").value = contact.id;
                document.getElementById("dept-contact-name").value = contact.department_name;
                document.getElementById("dept-contact-person").value = contact.contact_person_name || '';
                document.getElementById("dept-contact-designation").value = contact.designation || '';
                document.getElementById("dept-contact-phone").value = contact.phone_number;
                document.getElementById("dept-contact-whatsapp").value = contact.whatsapp_number || '';
                document.getElementById("dept-contact-email").value = contact.email || '';
                document.getElementById("dept-contact-description").value = contact.description || '';
                document.getElementById("dept-contact-order").value = contact.display_order || 0;
                document.getElementById("dept-contact-active").checked = contact.is_active;

                document.getElementById("modal-dept-contact-title").textContent = "Edit Department Contact";
                openModal('modal-admin-dept-contact');
            } catch (e) {
                console.error("Error fetching detail for edit:", e);
            }
        }

        function closeDepartmentContactModal() {
            closeModal('modal-admin-dept-contact');
        }

        async function saveDepartmentContact(e) {
            e.preventDefault();
            const id = document.getElementById("dept-contact-id").value;
            const payload = {
                department_name: document.getElementById("dept-contact-name").value,
                contact_person_name: document.getElementById("dept-contact-person").value,
                designation: document.getElementById("dept-contact-designation").value,
                phone_number: document.getElementById("dept-contact-phone").value,
                whatsapp_number: document.getElementById("dept-contact-whatsapp").value,
                email: document.getElementById("dept-contact-email").value,
                description: document.getElementById("dept-contact-description").value,
                display_order: document.getElementById("dept-contact-order").value,
                is_active: document.getElementById("dept-contact-active").checked
            };

            const url = id ? `/dashboard/admin/api/department-contacts/${id}/` : `/dashboard/admin/api/department-contacts/`;
            const res = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie('csrftoken') || ''
                },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok && data.success) {
                closeDepartmentContactModal();
                fetchAdminDepartmentContacts();
            } else {
                alert(data.error || data.message || "Failed to save department contact.");
            }
        }

        async function deleteDepartmentContact(id) {
            if (!confirm("Are you sure you want to delete this department contact?")) return;
            const res = await fetch(`/dashboard/admin/api/department-contacts/${id}/`, {
                method: "DELETE",
                headers: { "X-CSRFToken": getCookie('csrftoken') || '' }
            });
            if (res.ok) {
                fetchAdminDepartmentContacts();
            } else {
                alert("Failed to delete contact.");
            }
        }

        // Fetch feedback count on load
        document.addEventListener('DOMContentLoaded', () => {
            fetchAdminAgentFeedbacks();
            document.getElementById('btn-add-bank-account')?.addEventListener('click', openAddBankAccountModal);
            document.getElementById('btn-add-department-contact')?.addEventListener('click', openAddDepartmentContactModal);
        });
    