# Scrapless Frontend - Quick Reference Guide

## Project Files

| File | Purpose |
|------|---------|
| `main.jsx` | Main UI component with all features |
| `main.css` | All styling and responsive design |
| `index.jsx` | React app entry point |
| `index.html` | HTML template |
| `api.js` | API client for backend communication |
| `utils.js` | Utility functions for data processing |
| `hooks.js` | Custom React hooks |
| `mockData.js` | Mock data for testing/development |
| `vite.config.js` | Build configuration |
| `package.json` | Dependencies and scripts |

---

## Quick Commands

```bash
# Install dependencies
npm install

# Start development server (port 5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Component: Scrapless (Main UI)

### Features
- ✅ Photo upload & camera capture
- ✅ Image analysis via API
- ✅ Ingredient display with freshness tracking
- ✅ Expandable ingredient details
- ✅ Recipe suggestions
- ✅ Storage tips
- ✅ Fully responsive design
- ✅ Loading states
- ✅ Empty states

### State Variables
```javascript
uploadedImage      // Base64 image string
ingredients        // Array of ingredient objects
loading            // Boolean for API calls
selectedIngredient // Index of expanded ingredient
```

### Key Methods
```javascript
handleImageUpload()    // Process file upload
handleCameraCapture()  // Capture from device camera
analyzeImage()         // Send image to API
getFreshnessColor()    // Return color for status
getFreshnessLabel()    // Return text for status
```

---

## API Endpoints

### POST /api/analyze-ingredients
```javascript
const response = await fetch('/api/analyze-ingredients', {
  method: 'POST',
  body: formData,  // Contains image file
});

// Expected response:
{
  ingredients: [
    {
      name: string,
      emoji: string,
      daysLeft: number,
      storageTip: string,
      condition: string,
      recipes: string[]
    }
  ]
}
```

---

## Utility Functions

### Freshness Management
```javascript
import { getFreshnessColor, getFreshnessLabel } from './utils.js';

getFreshnessColor(4)    // '#10b981' (green)
getFreshnessLabel(4)    // 'Fresh'
```

### Ingredient Processing
```javascript
import {
  sortIngredientsByFreshness,
  filterIngredientsNearExpiry,
  filterFreshIngredients,
} from './utils.js';

sortIngredientsByFreshness(ingredients)  // Sort by expiry
filterIngredientsNearExpiry(ingredients, 2)  // Get urgent items
filterFreshIngredients(ingredients, 5)   // Get fresh items
```

### Validation
```javascript
import { validateImage } from './utils.js';

const result = validateImage(file);
// Returns: { valid: boolean, error?: string }
```

---

## Custom Hooks

### useImageAnalysis()
```javascript
import { useImageAnalysis } from './hooks.js';

const {
  loading,
  error,
  ingredients,
  uploadedImage,
  analyzeImage,
  clearData
} = useImageAnalysis();
```

### useRecipeSuggestions()
```javascript
import { useRecipeSuggestions } from './hooks.js';

const {
  loading,
  error,
  recipes,
  fetchRecipes
} = useRecipeSuggestions();
```

### useLocalStorage()
```javascript
import { useLocalStorage } from './hooks.js';

const [value, setValue] = useLocalStorage('key', initialValue);
```

---

## API Client

```javascript
import apiClient from './api.js';

// Analyze image
await apiClient.analyzeIngredients(file);

// Get recipes
await apiClient.getRecipeSuggestions(['broccoli', 'carrots']);

// Get storage tips
await apiClient.getStorageTips('Broccoli');

// Get history
await apiClient.getIngredientHistory();

// Save ingredient
await apiClient.saveIngredient(ingredientObject);
```

---

## Ingredient Object Structure

```javascript
{
  name: string,              // e.g., "Broccoli"
  emoji: string,             // e.g., "🥦"
  daysLeft: number,          // e.g., 4
  freshness: string,         // e.g., "Good"
  storageTip: string,        // Storage instructions
  condition: string,         // Visual description
  recipes: string[]          // Recipe suggestions
}
```

---

## Color Coding Reference

| Color | Freshness | Days | Label |
|-------|-----------|------|-------|
| 🟢 Green | Fresh | > 5 | Fresh |
| 🟡 Amber | Good | 1-5 | Use Soon |
| 🔴 Red | Critical | < 1 | Dispose |

---

## CSS Classes

### Main Container
```css
.scrapless-container    /* Outer wrapper */
.header                 /* Top header */
.main-content           /* Main content area */
.footer                 /* Bottom footer */
```

### Upload Section
```css
.upload-section         /* Upload area */
.upload-container       /* Upload controls */
.upload-button          /* Upload buttons */
.image-preview          /* Image preview */
```

### Ingredients
```css
.ingredients-section    /* Ingredients area */
.ingredients-grid       /* Grid layout */
.ingredient-card        /* Individual card */
.ingredient-details     /* Expanded details */
.freshness-bar          /* Freshness progress bar */
```

---

## Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_MAX_IMAGE_SIZE=5242880
VITE_ENABLE_MOCK_DATA=false
```

---

## Responsive Breakpoints

```css
/* Desktop (1200px+) */
.ingredients-grid {
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

/* Tablet (768px - 1199px) */
@media (max-width: 768px) {
  .ingredients-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile (< 480px) */
@media (max-width: 480px) {
  .ingredients-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## Common Tasks

### Using Mock Data for Development
```javascript
import mockData from './mockData.js';

// In your component
setIngredients(mockData.ingredients);
```

### Displaying Freshness Status
```javascript
const { getFreshnessColor, getFreshnessLabel } = require('./utils.js');

const ingredient = { daysLeft: 3 };
const color = getFreshnessColor(ingredient.daysLeft);  // '#f59e0b'
const label = getFreshnessLabel(ingredient.daysLeft);  // 'Use Soon'
```

### Sorting by Expiry
```javascript
const { sortIngredientsByFreshness } = require('./utils.js');

const sorted = sortIngredientsByFreshness(ingredients);
// Items expiring first come first
```

### Getting Urgent Items
```javascript
const { filterIngredientsNearExpiry } = require('./utils.js');

const urgent = filterIngredientsNearExpiry(ingredients, 2);
// Gets items that expire within 2 days
```

---

## Import Examples

```javascript
// From main React
import Scrapless from './main';

// Utilities
import { getFreshnessColor, sortIngredientsByFreshness } from './utils';

// Hooks
import { useImageAnalysis, useLocalStorage } from './hooks';

// API
import apiClient from './api';

// Mock Data
import mockData from './mockData';

// Examples
import { AdvancedIngredientManager, FreshnessDashboard } from './ExampleComponents';
```

---

## Debugging Checklist

- [ ] Backend running on `http://localhost:8000`?
- [ ] Image format valid (JPG, PNG, WebP, GIF)?
- [ ] Image size < 5MB?
- [ ] API response contains all required fields?
- [ ] CORS enabled on backend?
- [ ] Dev server running: `npm run dev`?
- [ ] Check browser console for errors
- [ ] Check Network tab for API calls
- [ ] Try mock data to test UI

---

## Performance Tips

- ✅ Images are lazy-loaded
- ✅ Code is automatically split by Vite
- ✅ CSS is minified in production
- ✅ Use React.memo for expensive components
- ✅ Debounce search/filter inputs

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari 12+, Chrome Mobile

---

## File Size Guidelines

- Total bundle: < 500KB
- Images: < 5MB per upload
- Cache strategy: Browser cache for static assets

---

## Security Considerations

- ✅ Image validation on frontend
- ✅ File type checking
- ✅ Size limits enforced
- ✅ No sensitive data in localStorage
- ✅ HTTPS recommended for production

---

## Need Help?

1. Check [README.md](README.md) for overview
2. See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed guide
3. Review [ExampleComponents.jsx](ExampleComponents.jsx) for code examples
4. Check [mockData.js](mockData.js) for sample data
5. Review [utils.js](utils.js) for available functions

---

**Version:** 1.0.0  
**Last Updated:** April 2024
