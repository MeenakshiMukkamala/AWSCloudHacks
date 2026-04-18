# 🚀 Scrapless Frontend - Complete Setup Guide

## What You're Getting

A **complete, production-ready frontend** for a food waste reduction app with:

- 🎨 Modern, responsive UI
- 📸 Image upload & camera capture
- 🤖 AI ingredient detection integration
- 📊 Freshness tracking & visualization
- 👨‍🍳 Recipe suggestions
- 📱 Mobile-first design
- ♿ Accessibility built-in
- 🧪 Testing utilities included

---

## 📂 Complete File Listing

### Core Application Files

| File | Size | Purpose |
|------|------|---------|
| `main.jsx` | 5KB | Main React component with all UI |
| `main.css` | 8KB | Complete styling & responsive design |
| `index.jsx` | 0.3KB | React entry point |
| `index.html` | 1KB | HTML template |

### Supporting Modules

| File | Size | Purpose |
|------|------|---------|
| `api.js` | 3KB | Backend API client |
| `utils.js` | 4KB | Utility functions for data processing |
| `hooks.js` | 4KB | Custom React hooks |
| `mockData.js` | 2KB | Mock data for development |
| `ExampleComponents.jsx` | 6KB | Example component implementations |

### Configuration Files

| File | Size | Purpose |
|------|------|---------|
| `vite.config.js` | 0.5KB | Build configuration |
| `package.json` | 0.5KB | Dependencies & scripts |
| `.env.example` | 0.2KB | Environment variables |
| `.gitignore` | 0.3KB | Git ignore rules |

### Documentation Files

| File | Type | Purpose |
|------|------|---------|
| `README.md` | Guide | Project overview & features |
| `DEVELOPMENT.md` | Guide | Detailed development documentation |
| `QUICK_REFERENCE.md` | Cheat Sheet | Quick lookup & examples |
| `PROJECT_SUMMARY.md` | Summary | High-level overview |
| `SETUP_GUIDE.md` | Guide | This file - step-by-step setup |

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 2: Start Dev Server
```bash
npm run dev
```

### Step 3: Open in Browser
```
http://localhost:5173
```

✅ **Done!** The UI is now running and ready to connect to your backend.

---

## 🔌 Connecting to Backend

The frontend expects your backend to provide this endpoint:

### Backend Requirement

```
POST /api/analyze-ingredients
Content-Type: multipart/form-data

Request:
  - image: File

Response:
  {
    "ingredients": [
      {
        "name": "Broccoli",
        "emoji": "🥦",
        "daysLeft": 4,
        "storageTip": "Store in refrigerator...",
        "condition": "Fresh with slight wilting...",
        "recipes": ["Stir-Fry", "Roasted"]
      }
    ]
  }
```

---

## 🧪 Testing Without Backend

Use mock data during development:

### Option 1: Modify analyzeImage() Function

Edit `main.jsx` and replace the fetch call:

```javascript
const analyzeImage = async (file) => {
  setLoading(true);
  try {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Use mock data
    const mockData = await import('./mockData.js');
    setIngredients(mockData.mockIngredientsResponse.ingredients);
  } catch (error) {
    console.error('Error:', error);
  } finally {
    setLoading(false);
  }
};
```

### Option 2: Use Browser DevTools

Open DevTools Console and paste:

```javascript
// Mock the fetch API
const mockResponse = {
  ingredients: [
    {
      name: "Test Broccoli",
      emoji: "🥦",
      daysLeft: 4,
      recipes: ["Stir-Fry", "Roasted"]
    }
  ]
};

window._mockApiResponse = mockResponse;
```

---

## 📋 Component Structure

```
Scrapless (Main Component)
│
├── Header
│   ├── Logo "🥬 Scrapless"
│   └── Tagline
│
├── Main Content
│   ├── Upload Section
│   │   ├── Take Photo Button
│   │   ├── Upload Image Button
│   │   └── Image Preview
│   │
│   ├── Loading Spinner (while analyzing)
│   │
│   ├── Ingredients Section
│   │   └── Ingredient Cards Grid
│   │       ├── Emoji & Name
│   │       ├── Freshness Progress Bar
│   │       ├── Days Left Badge
│   │       └── [Click to Expand]
│   │           ├── Storage Tips
│   │           ├── Condition
│   │           └── Recipe Suggestions
│   │
│   └── Empty State (when no ingredients)
│
└── Footer
```

---

## 🎯 Feature Breakdown

### 1️⃣ Image Capture
```jsx
// Camera capture
<input type="file" accept="image/*" capture="environment" />

// File upload
<input type="file" accept="image/*" />
```

### 2️⃣ Image Analysis
```javascript
const analyzeImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);
  
  const response = await fetch('/api/analyze-ingredients', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  setIngredients(data.ingredients);
};
```

### 3️⃣ Freshness Display
```javascript
// Color coding based on days left
const getFreshnessColor = (daysLeft) => {
  if (daysLeft > 5) return '#10b981';  // Green
  if (daysLeft > 2) return '#f59e0b';  // Amber
  return '#ef4444';                     // Red
};
```

### 4️⃣ Recipe Suggestions
```jsx
// Display as tags under expandable details
{ingredient.recipes.map((recipe, idx) => (
  <span key={idx} className="suggestion-tag">
    {recipe}
  </span>
))}
```

---

## 🎨 Customizing Appearance

### Colors

Edit `main.css` CSS variables (top of file):

```css
:root {
  --primary-color: #10b981;      /* Green */
  --secondary-color: #f59e0b;    /* Amber */
  --danger-color: #ef4444;       /* Red */
}
```

### Fonts

All fonts use system fonts for best performance:

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

To use Google Fonts, add to `index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet" />
```

---

## 📱 Mobile Optimization

The UI is fully responsive:

- **Desktop** (1200px+): 3-column grid
- **Tablet** (768px+): 2-column grid  
- **Mobile** (<768px): 1-column, full width

All breakpoints defined in `main.css`:

```css
@media (max-width: 768px) {
  /* Tablet styles */
}

@media (max-width: 480px) {
  /* Mobile styles */
}
```

---

## 🔧 Extending the Project

### Adding a New Feature

1. **Create new component** in `main.jsx`:

```javascript
function MyNewFeature() {
  return <div>New Feature</div>;
}
```

2. **Add to UI**:

```javascript
<section className="my-new-section">
  <MyNewFeature />
</section>
```

3. **Add styling** to `main.css`:

```css
.my-new-section {
  /* Your styles */
}
```

### Modifying API Integration

Edit `api.js` to add new endpoints:

```javascript
async getMyData(params) {
  try {
    const response = await fetch(`${this.baseURL}/api/my-endpoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}
```

### Creating Custom Hooks

Add to `hooks.js`:

```javascript
export const useMyCustomHook = () => {
  const [state, setState] = useState(null);
  
  const handler = () => {
    // Your logic
  };
  
  return { state, handler };
};
```

---

## 📊 Data Flow

```
User Action
    ↓
handleImageUpload() / handleCameraCapture()
    ↓
Create FileReader (preview)
    ↓
analyzeImage(file)
    ↓
POST /api/analyze-ingredients
    ↓
Backend processes image with AI
    ↓
Returns ingredients array
    ↓
setIngredients(data)
    ↓
Component re-renders with cards
    ↓
User sees freshness info & recipes
```

---

## 🐛 Debugging

### Check Backend Connection

```javascript
// In browser console
fetch('http://localhost:8000/api/analyze-ingredients', {
  method: 'POST',
  body: new FormData() // Empty for testing
})
.then(r => r.json())
.then(d => console.log(d))
.catch(e => console.error(e))
```

### Inspect Component State

```javascript
// Add to component temporarily
console.log('Ingredients:', ingredients);
console.log('Loading:', loading);
console.log('Error:', error);
```

### Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Upload image
4. Look for POST request to `/api/analyze-ingredients`
5. Check request/response tabs

---

## 📦 Production Build

### Build Command
```bash
npm run build
```

This creates an optimized `dist/` folder.

### Deploy to Netlify
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Deploy to Vercel
```bash
npm install -g vercel
vercel --prod
```

### Deploy with Docker
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## ✅ Checklist Before Going Live

- [ ] Backend API is deployed and accessible
- [ ] API endpoint responds correctly to image uploads
- [ ] Backend returns correct JSON structure
- [ ] CORS is properly configured
- [ ] Environment variables are set
- [ ] Testing with various image sizes/formats
- [ ] Testing on mobile devices
- [ ] Tested with slow network (DevTools Throttling)
- [ ] Tested on different browsers
- [ ] Error messages are user-friendly
- [ ] Loading states work correctly
- [ ] Images load with good performance

---

## 📚 Documentation Reference

| Document | Best For |
|----------|----------|
| **README.md** | First-time users, overview |
| **DEVELOPMENT.md** | Detailed implementation details |
| **QUICK_REFERENCE.md** | Quick lookups, API examples |
| **PROJECT_SUMMARY.md** | High-level architecture |
| **SETUP_GUIDE.md** | This file - step-by-step |

---

## 🆘 Common Issues & Solutions

### "Cannot POST /api/analyze-ingredients"
**Cause:** Backend not running  
**Fix:** Start backend server on port 8000

### "Image upload button not working"
**Cause:** File input not properly connected  
**Fix:** Check input element has proper onChange handler

### "Ingredients not displaying"
**Cause:** API response format mismatch  
**Fix:** Verify API returns correct JSON structure

### "Styles look broken"
**Cause:** CSS not loading  
**Fix:** Restart dev server with `npm run dev`

### "Camera capture not working on mobile"
**Cause:** Browser doesn't have camera permission  
**Fix:** Check browser settings, use HTTPS

---

## 🎓 Learning Resources

- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [CSS Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [MDN Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)
- [Web Accessibility](https://www.w3.org/WAI/)

---

## 🎉 You're All Set!

The frontend is ready to:
✅ Connect to your backend  
✅ Accept image uploads  
✅ Display AI-identified ingredients  
✅ Show freshness tracking  
✅ Suggest recipes  
✅ Work on all devices  
✅ Scale to production  

**Next Steps:**
1. Configure backend connection
2. Test with mock data
3. Deploy backend API
4. Test full integration
5. Deploy frontend to production

---

## 📞 Need Help?

1. Check the troubleshooting section above
2. Review relevant documentation file
3. Check browser console for error messages
4. Try with mock data to isolate issues
5. Review example components for implementation patterns

---

**Happy coding! 🚀**

Version: 1.0.0  
Last Updated: April 2024
