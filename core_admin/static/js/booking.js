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
