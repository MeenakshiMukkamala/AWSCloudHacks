# Scrapless Frontend - Configuration & Best Practices

## 🔧 Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

### Available Variables

```env
# Backend API URL
VITE_API_URL=http://localhost:8000

# API timeout in milliseconds
VITE_API_TIMEOUT=30000

# Maximum image size in bytes (5MB)
VITE_MAX_IMAGE_SIZE=5242880

# Enable mock data for testing
VITE_ENABLE_MOCK_DATA=false
```

### Using Environment Variables in Code

```javascript
// Access in components
const apiUrl = import.meta.env.VITE_API_URL;
const timeout = import.meta.env.VITE_API_TIMEOUT;
const maxSize = import.meta.env.VITE_MAX_IMAGE_SIZE;
const useMockData = import.meta.env.VITE_ENABLE_MOCK_DATA === 'true';
```

---

## 📋 Best Practices

### Code Style

#### Component Structure
```javascript
// 1. Imports at top
import React, { useState } from 'react';
import './component.css';

// 2. Component definition
export default function MyComponent() {
  // 3. State declarations
  const [state, setState] = useState(null);
  
  // 4. Functions
  const handleClick = () => {
    // Logic
  };
  
  // 5. Effects
  React.useEffect(() => {
    // Side effects
  }, []);
  
  // 6. Render
  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

#### Naming Conventions
```javascript
// Components: PascalCase
function MyComponent() {}

// Functions: camelCase
const myFunction = () => {};

// Constants: UPPER_SNAKE_CASE
const MAX_SIZE = 5242880;

// Boolean: with is/has prefix
const isLoading = true;
const hasError = false;

// Arrays: plural
const ingredients = [];

// CSS classes: kebab-case
className="ingredient-card"
```

### State Management

#### Do's ✅
```javascript
// Group related state
const [formData, setFormData] = useState({
  name: '',
  email: '',
  phone: ''
});

// Use single setState for updates
setFormData({ ...formData, name: 'John' });

// Use callbacks for complex logic
const handleSubmit = useCallback(() => {
  // Logic
}, [dependencies]);
```

#### Don'ts ❌
```javascript
// Don't create state for derived values
const [name, setName] = useState('');
const [displayName, setDisplayName] = useState(''); // Avoid

// Don't use multiple setState calls
setName('John');
setEmail('john@example.com'); // Consider grouping

// Don't forget dependencies
useEffect(() => {
  // Logic
}, []); // Add dependencies if needed
```

### Error Handling

#### API Calls
```javascript
const analyzeImage = async (file) => {
  setLoading(true);
  setError(null);
  
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    setIngredients(data.ingredients);
  } catch (error) {
    setError('Failed to analyze image. Please try again.');
    console.error('Error:', error);
  } finally {
    setLoading(false);
  }
};
```

#### User Feedback
```javascript
// Always show error to user
{error && (
  <div className="error-message">
    {error}
  </div>
)}

// Show loading state
{loading && (
  <div className="loader">
    <p>Processing...</p>
  </div>
)}
```

### Performance

#### Optimization Techniques

1. **Lazy Loading**
   ```javascript
   import { lazy, Suspense } from 'react';
   const HeavyComponent = lazy(() => import('./HeavyComponent'));
   
   <Suspense fallback={<Loading />}>
     <HeavyComponent />
   </Suspense>
   ```

2. **Memoization**
   ```javascript
   import { memo, useMemo, useCallback } from 'react';
   
   const IngredientCard = memo(function IngredientCard({ ingredient }) {
     return <div>{ingredient.name}</div>;
   });
   
   const processedList = useMemo(() => {
     return ingredients.filter(i => i.daysLeft < 3);
   }, [ingredients]);
   ```

3. **Event Debouncing**
   ```javascript
   import { useDebounce } from './hooks';
   
   const debouncedSearch = useDebounce(searchTerm, 500);
   ```

4. **Image Optimization**
   ```javascript
   // Compress before upload
   const handleImageUpload = (file) => {
     // Consider compression library like imagemin
     analyzeImage(file);
   };
   ```

### Testing

#### Unit Tests (Example)
```javascript
import { render, screen } from '@testing-library/react';
import Scrapless from './main';

describe('Scrapless Component', () => {
  it('renders upload section', () => {
    render(<Scrapless />);
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
  });
  
  it('displays ingredients after upload', async () => {
    // Test logic
  });
});
```

#### Integration Tests
```javascript
it('uploads image and displays results', async () => {
  // 1. Render component
  // 2. Simulate file upload
  // 3. Wait for API response
  // 4. Check ingredients displayed
});
```

---

## 🚀 Deployment

### Development Deployment

```bash
# Local development
npm run dev

# Build preview
npm run build
npm run preview
```

### Production Deployment

#### Option 1: Vercel (Recommended)

```bash
# Install CLI
npm i -g vercel

# Deploy
vercel --prod

# Configure
# - Set environment variables in Vercel dashboard
# - Add VITE_API_URL pointing to your backend
```

#### Option 2: Netlify

```bash
# Install CLI
npm i -g netlify-cli

# Build first
npm run build

# Deploy
netlify deploy --prod --dir=dist

# Or connect GitHub for automatic deploys
```

#### Option 3: Docker

```dockerfile
# Dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
RUN rm -rf /etc/nginx/conf.d/*
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Option 4: Traditional Hosting

```bash
# Build
npm run build

# Copy dist/ to your web server
# Example with SCP:
scp -r dist/* user@example.com:/var/www/html/

# Configure server for SPA (rewrite index.html)
```

### Environment Variables in Production

**Vercel:**
```bash
# In vercel.json
{
  "env": {
    "VITE_API_URL": "https://api.scrapless.com"
  }
}
```

**Netlify:**
```bash
# In netlify.toml
[build.environment]
VITE_API_URL = "https://api.scrapless.com"
```

**Docker:**
```dockerfile
ENV VITE_API_URL=https://api.scrapless.com
```

---

## 🔒 Security Best Practices

### Input Validation
```javascript
import { validateImage } from './utils';

const handleUpload = (file) => {
  const validation = validateImage(file);
  if (!validation.valid) {
    setError(validation.error);
    return;
  }
  analyzeImage(file);
};
```

### Secure API Calls
```javascript
// Use HTTPS in production
const apiUrl = import.meta.env.VITE_API_URL;
// Should be https:// in production

// Validate responses
if (!response.ok || !response.headers.get('content-type').includes('json')) {
  throw new Error('Invalid response');
}
```

### Content Security
```javascript
// Sanitize user input if displaying
// Use libraries like DOMPurify if needed

// Avoid eval() and innerHTML
// Use textContent instead of innerHTML
```

### CORS Configuration
```javascript
// Backend should configure CORS
// Example (Python Flask):
from flask_cors import CORS
CORS(app, resources={
  r"/api/*": {
    "origins": ["https://scrapless.com"],
    "methods": ["POST"],
    "allowed_headers": ["Content-Type"]
  }
})
```

---

## 📊 Monitoring & Analytics

### Error Tracking
```javascript
// Add Sentry for error tracking
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
});
```

### Performance Monitoring
```javascript
// Check Core Web Vitals
if ('PerformanceObserver' in window) {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      console.log('Performance:', entry);
    }
  });
  observer.observe({ entryTypes: ['navigation', 'resource'] });
}
```

### Analytics
```javascript
// Track user actions
const trackEvent = (eventName, eventData) => {
  if (window.gtag) {
    window.gtag('event', eventName, eventData);
  }
};

// Use in components
trackEvent('image_uploaded', { size: file.size });
```

---

## 🧹 Code Quality

### Linting Setup

```bash
# Install ESLint
npm install --save-dev eslint eslint-plugin-react

# Create config
npx eslint --init

# Run linter
npm run lint

# Fix issues
npm run lint -- --fix
```

### Prettier Formatting

```bash
# Install Prettier
npm install --save-dev prettier

# Create config (.prettierrc)
{
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "semi": true
}

# Format code
npx prettier --write .
```

### Git Hooks

```bash
# Install Husky
npm install husky --save-dev
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run lint"
```

---

## 📝 Documentation

### Inline Comments
```javascript
// Good - explains why, not what
// Debounce search to reduce API calls
const debouncedSearch = useDebounce(searchTerm, 500);

// Avoid - obvious from code
// Set the loading state to true
setLoading(true);
```

### Function Documentation
```javascript
/**
 * Analyze image for ingredients
 * @param {File} imageFile - Image file from input
 * @returns {Promise<Object>} Response with ingredients array
 * @throws {Error} If image upload fails
 */
async function analyzeImage(imageFile) {
  // Implementation
}
```

### README Updates
Keep documentation updated as you add features:
- Link to API documentation
- Update environment variables
- Add deployment instructions
- Include screenshots/GIFs

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: 18
      
      - run: npm install
      - run: npm run lint
      - run: npm run build
      
      - name: Deploy
        run: npm run deploy
```

---

## 🎯 Performance Checklist

- [ ] Bundle size < 500KB (gzipped)
- [ ] Time to First Paint (FCP) < 2s
- [ ] Largest Contentful Paint (LCP) < 2.5s
- [ ] Cumulative Layout Shift (CLS) < 0.1
- [ ] Images optimized and lazy-loaded
- [ ] Code splitting enabled
- [ ] Caching strategy implemented
- [ ] Minification enabled in production
- [ ] No console errors/warnings
- [ ] Lighthouse score > 90

---

## 🔗 Resources & References

### Tools
- [Vite](https://vitejs.dev)
- [React DevTools](https://react-devtools-tutorial.vercel.app/)
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)

### Libraries (Optional Additions)
- [Sentry](https://sentry.io) - Error tracking
- [Vercel Analytics](https://vercel.com/analytics) - Performance metrics
- [React Query](https://tanstack.com/query/latest) - Data fetching
- [Zustand](https://github.com/pmndrs/zustand) - State management
- [TailwindCSS](https://tailwindcss.com) - Styling

---

## ✅ Pre-Launch Checklist

- [ ] Backend API is production-ready
- [ ] Environment variables are configured
- [ ] CORS is properly set up
- [ ] HTTPS is enabled
- [ ] Error tracking is configured
- [ ] Analytics is set up
- [ ] Performance is optimized
- [ ] Security measures are in place
- [ ] Tests are passing
- [ ] Documentation is complete
- [ ] Mobile responsiveness verified
- [ ] Accessibility standards met

---

**Version:** 1.0.0  
**Last Updated:** April 2024
