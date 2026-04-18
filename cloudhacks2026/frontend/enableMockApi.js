/**
 * Mock API Helper
 * Paste this in browser console to enable mock API responses
 * 
 * Usage:
 * 1. Open DevTools (F12)
 * 2. Go to Console tab
 * 3. Copy & paste this entire file
 * 4. Press Enter
 * 5. Upload an image - you'll get mock data!
 */

const mockApiEnabled = () => {
  const originalFetch = window.fetch;
  
  window.fetch = function(...args) {
    const url = args[0];
    
    // Intercept analyze-ingredients requests
    if (url.includes('analyze-ingredients')) {
      console.log('[Mock API] Intercepted request to:', url);
      
      return new Promise((resolve) => {
        // Simulate network delay
        setTimeout(() => {
          const mockIngredients = [
            {
              name: "Broccoli",
              daysLeft: 4,
              storageTip: "Store in refrigerator in airtight container. Keep the stem moist.",
              condition: "Fresh with slight wilting on stem tips. Still good for cooking.",
              recipes: ["Broccoli Stir-Fry", "Roasted Vegetables", "Soup", "Pasta Bake"]
            },
            {
              name: "Spinach",
              daysLeft: 2,
              storageTip: "Keep in plastic bag in the crisper drawer. Can wrap in paper towel.",
              condition: "Starting to wilt slightly at the edges. Use in cooked dishes.",
              recipes: ["Salad", "Smoothie", "Sautéed", "Pasta"]
            },
            {
              name: "Half-Used Onion",
              daysLeft: 7,
              storageTip: "Wrap tightly in plastic wrap. Store in vegetable crisper drawer.",
              condition: "Cut surface is dry. No visible mold or spoilage.",
              recipes: ["Soup", "Stew", "Stir-Fry", "Caramelized Onions"]
            },
            {
              name: "Carrots",
              daysLeft: 14,
              storageTip: "Store in vegetable crisper drawer. Remove any green tops if present.",
              condition: "Firm and fresh. No soft spots or sprouting.",
              recipes: ["Roasted", "Soup", "Stir-Fry", "Snacks", "Juice"]
            },
            {
              name: "Bell Pepper",
              daysLeft: 5,
              storageTip: "Store whole in refrigerator crisper. Don't wash until ready to use.",
              condition: "Still firm with vibrant color. Minor wrinkles appearing.",
              recipes: ["Stir-Fry", "Salad", "Stuffed", "Roasted", "Fajitas"]
            },
            {
              name: "Garlic",
              daysLeft: 30,
              storageTip: "Store in cool, dark, well-ventilated place. Avoid refrigerator.",
              condition: "Cloves are firm. No sprouts or soft spots.",
              recipes: ["Any savory dish", "Garlic Bread", "Salad Dressing", "Pasta"]
            }
          ];

          console.log('[Mock API] Returning mock data:', mockIngredients);

          resolve({
            ok: true,
            status: 200,
            json: async () => ({
              ingredients: mockIngredients
            })
          });
        }, 1500); // Simulate 1.5s API delay
      });
    }
    
    // Fall back to real fetch for other requests
    return originalFetch(...args);
  };
  
  console.log('%c✅ Mock API Enabled!', 'color: #10b981; font-size: 16px; font-weight: bold;');
  console.log('%cNow upload an image and you\'ll get mock ingredient data!', 'color: #666; font-size: 14px;');
  console.log('%cTo disable, refresh the page.', 'color: #f59e0b; font-size: 12px;');
};

// Auto-enable mock API
mockApiEnabled();
