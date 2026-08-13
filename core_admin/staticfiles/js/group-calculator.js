// Group size pricing adjustments calculation logic
function calculateGroupPrice(basePrice, groupSize) {
    let discountRate = 0.0;
    
    if (groupSize >= 15) {
        discountRate = 0.12; // 12% group discount
    } else if (groupSize >= 10) {
        discountRate = 0.08; // 8% group discount
    } else if (groupSize >= 5) {
        discountRate = 0.05; // 5% group discount
    }
    
    const discountedPrice = basePrice * (1 - discountRate);
    const totalPrice = discountedPrice * groupSize;
    
    return {
        originalBase: basePrice,
        size: groupSize,
        rate: discountRate * 100,
        discountedBase: discountedPrice,
        total: totalPrice
    };
}

console.log("Group calculator service online.");
