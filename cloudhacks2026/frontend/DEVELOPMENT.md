# Scrapless Frontend - Development Guide

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Set Up Environment Variables
Create a `.env` file by copying `.env.example`:
```bash
cp .env.example .env
```

### 3. Start Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

---

## Project Architecture

### File Structure
```
frontend/
├── main.jsx              # Main component (Scrapless UI)
├── main.css              # Global styles
├── index.jsx             # React app entry point
├── index.html            # HTML template
├── package.json          # Dependencies
├── vite.config.js        # Vite build config
├── api.js                # API client
├── utils.js              # Utility functions
├── hooks.js              # Custom React hooks
├── mockData.js           # Mock data for testing
├── .env.example          # Environment variables template
└── README.md             # Project documentation
```

### Component Hierarchy

```
Scrapless (main.jsx)
├── Header
├── Main Content
│   ├── Upload Section
│   ├── Image Preview
│   ├── Loading State
│   ├── Ingredients Section
│   │   └── Ingredient Cards (expandable)
│   └── Empty State
└── Footer
```

---

## Key Components & Functions

### Main Component: `Scrapless`

**State Management:**
```javascript
const [uploadedImage, setUploadedImage] = useState(null);
const [ingredients, setIngredients] = useState([]);
const [loading, setLoading] = useState(false);
const [selectedIngredient, setSelectedIngredient] = useState(null);
```

**Key Methods:**
- `handleImageUpload()` - Process file uploads
- `handleCameraCapture()` - Capture from camera
- `analyzeImage()` - Send to API
- `getFreshnessColor()` - Determine color based on days left
- `getFreshnessLabel()` - Get status text

---

## API Integration

### Endpoint: POST `/api/analyze-ingredients`

**Expected Request:**
```
Content-Type: multipart/form-data
Form Data:
  - image: File object
```

**Expected Response:**
```json
{
  "ingredients": [
    {
      "name": "Broccoli",
      "emoji": "🥦",
      "daysLeft": 4,
      "storageTip": "Store in refrigerator in airtight container",
      "condition": "Fresh with slight wilting on stem",
      "recipes": ["Stir-Fry", "Roasted", "Soup"]
    }
  ]
}
```

### Using the API Client

```javascript
import apiClient from './api.js';

// Analyze image
const response = await apiClient.analyzeIngredients(imageFile);

// Get recipe suggestions
const recipes = await apiClient.getRecipeSuggestions(['broccoli', 'carrots']);

// Get storage tips
const tips = await apiClient.getStorageTips('Broccoli');
```

---

## Utility Functions

### Freshness Management
```javascript
import { getFreshnessColor, getFreshnessLabel } from './utils.js';

const color = getFreshnessColor(4);      // Returns: '#10b981' (green)
const label = getFreshnessLabel(4);      // Returns: 'Good'
```

### Ingredient Filtering
```javascript
import { 
  sortIngredientsByFreshness, 
  filterIngredientsNearExpiry,
  filterFreshIngredients 
} from './utils.js';

// Sort by freshness (expires first)
const sorted = sortIngredientsByFreshness(ingredients);

// Get items expiring within 2 days
const urgent = filterIngredientsNearExpiry(ingredients, 2);

// Get fresh items (> 5 days)
const fresh = filterFreshIngredients(ingredients, 5);
```

### Image Validation
```javascript
import { validateImage } from './utils.js';

const validation = validateImage(file);
if (!validation.valid) {
  console.error(validation.error);
}
```

---

## Custom Hooks

### useImageAnalysis()

Manages image upload and ingredient analysis:

```javascript
import { useImageAnalysis } from './hooks.js';

const { loading, error, ingredients, uploadedImage, analyzeImage, clearData } = 
  useImageAnalysis();

// Use in component
<input onChange={(e) => analyzeImage(e.target.files[0])} />
```

### useRecipeSuggestions()

Fetch recipes for ingredients:

```javascript
import { useRecipeSuggestions } from './hooks.js';

const { loading, error, recipes, fetchRecipes } = useRecipeSuggestions();

// Use in component
<button onClick={() => fetchRecipes(['broccoli', 'carrots'])}>
  Get Recipes
</button>
```

### useLocalStorage()

Persist data locally:

```javascript
import { useLocalStorage } from './hooks.js';

const [savedIngredients, setSavedIngredients] = useLocalStorage('ingredients', []);
```

---

## Styling Guide

### Color Scheme
- **Primary (Green):** `#10b981` - Fresh, confirmed, positive actions
- **Secondary (Amber):** `#f59e0b` - Warning, caution, use soon
- **Danger (Red):** `#ef4444` - Critical, urgent, use today
- **Text Primary:** `#1f2937` - Main text
- **Text Secondary:** `#6b7280` - Descriptive text
- **Background:** `#f9fafb` - Light background
- **Card Background:** `#ffffff` - Card background

### Responsive Breakpoints
- **Desktop:** 1200px+
- **Tablet:** 768px - 1199px
- **Mobile:** < 768px

### CSS Custom Properties (Variables)
```css
--primary-color: #10b981;
--primary-dark: #059669;
--secondary-color: #f59e0b;
--danger-color: #ef4444;
--light-bg: #f9fafb;
--card-bg: #ffffff;
```

---

## Using Mock Data

To develop without a backend, use mock data:

```javascript
import mockIngredientsResponse from './mockData.js';

// In your component
const handleAnalyzeImage = async (file) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Use mock data
  setIngredients(mockIngredientsResponse.ingredients);
};
```

Or modify the `analyzeImage` function in main.jsx:

```javascript
const analyzeImage = async (file) => {
  setLoading(true);
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Use mock data instead of API
    const mockData = await import('./mockData.js');
    setIngredients(mockData.mockIngredientsResponse.ingredients);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setLoading(false);
  }
};
```

---

## Building for Production

### Build Command
```bash
npm run build
```

This creates an optimized build in the `dist/` folder.

### Preview Build Locally
```bash
npm run preview
```

### Deploy to Production

#### Option 1: Netlify
```bash
npm run build
# Install Netlify CLI
npm install -g netlify-cli
# Deploy
netlify deploy --prod --dir=dist
```

#### Option 2: Vercel
```bash
npm run build
# Install Vercel CLI
npm install -g vercel
# Deploy
vercel --prod
```

#### Option 3: Docker
```bash
# Build Docker image
docker build -t scrapless-frontend .

# Run container
docker run -p 80:80 scrapless-frontend
```

---

## Debugging Tips

### Check API Connection
Open browser DevTools → Network tab → Try uploading an image
- Look for POST request to `/api/analyze-ingredients`
- Check response status (should be 200)
- Verify response JSON structure

### Verify Styling
```javascript
// In browser console
document.documentElement.style.cssText = 'background: red !important;'
// If red background appears, CSS is loaded
```

### Mock API Response
```javascript
// In browser console
window.fetch = async (url, options) => ({
  ok: true,
  json: async () => ({
    ingredients: [
      {
        name: "Test",
        emoji: "🥕",
        daysLeft: 5,
        recipes: ["Test Recipe"]
      }
    ]
  })
});
```

---

## Performance Optimization

### Image Compression
Consider using `sharp` or `imagemin` in your backend to optimize images before analysis.

### Lazy Loading
Images are loaded on demand - no additional optimization needed.

### Code Splitting
Vite automatically splits code. For manual chunks:

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          utils: ['./src/utils.js'],
          api: ['./src/api.js'],
        }
      }
    }
  }
}
```

---

## Accessibility

- Semantic HTML elements used throughout
- Proper ARIA labels for interactive elements
- Color contrast meets WCAG AA standards
- Keyboard navigation supported
- Touch-friendly button sizes (min 44px)

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Mobile

---

## Troubleshooting

### Issue: "Cannot find module"
**Solution:** Run `npm install` and restart dev server

### Issue: Styles not applying
**Solution:** Clear browser cache (Ctrl+Shift+Del) and restart

### Issue: Image upload not working
**Solution:** 
1. Check backend is running on port 8000
2. Verify CORS is enabled on backend
3. Check Network tab in DevTools for errors

### Issue: Loading spinner stuck
**Solution:** Backend may not be responding. Check console for error messages.

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Test thoroughly
4. Submit pull request with description

---

## Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)
- [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)

---

## Support & Questions

For issues or questions:
1. Check this documentation
2. Review mock data examples
3. Check browser console for errors
4. Submit an issue with detailed description

---

**Last Updated:** April 2024
**Version:** 1.0.0
