# Scrapless Frontend

A modern, responsive web interface for Scrapless - an AI-powered food waste reduction app that tracks ingredient freshness and suggests recipes.

## 🌟 Features

- **📸 Image Upload & Camera Capture** - Users can upload images or capture photos directly from their device
- **🤖 AI Ingredient Detection** - Backend analyzes images to identify ingredients
- **📊 Freshness Tracking** - Visual indicators show how many days each ingredient has left before spoilage
- **💡 Smart Storage Tips** - Get storage recommendations for each ingredient
- **👨‍🍳 Recipe Suggestions** - AI suggests recipes based on your available ingredients
- **📱 Fully Responsive** - Works seamlessly on desktop, tablet, and mobile devices
- **♿ Accessible** - Built with accessibility best practices in mind

## 📁 Project Structure

```
frontend/
├── main.jsx           # Main React component
├── main.css           # Styling
├── index.jsx          # React app entry point
├── index.html         # HTML template
├── package.json       # Dependencies
└── vite.config.js     # Vite configuration
```

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ installed
- npm or yarn package manager
- Backend API running on `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

Hot Module Replacement (HMR) is enabled, so changes will refresh automatically.

### Production Build

Build for production:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## 🎨 Component Architecture

### Main Component (`Scrapless`)
The primary component that manages:
- Image upload state
- Ingredient data
- Loading states
- User interactions

### Key Functions

- **`handleImageUpload`** - Processes file upload from input
- **`handleCameraCapture`** - Captures image from camera
- **`analyzeImage`** - Sends image to backend API for analysis
- **`getFreshnessColor`** - Returns color based on freshness (green/amber/red)
- **`getFreshnessLabel`** - Returns freshness status text

## 🔗 API Integration

### Endpoint: `/api/analyze-ingredients`

**Method:** POST

**Request:**
```
Content-Type: multipart/form-data
Form Data: image (file)
```

**Expected Response:**
```json
{
  "ingredients": [
    {
      "name": "Broccoli",
      "emoji": "🥦",
      "daysLeft": 4,
      "freshness": "Good",
      "storageTip": "Store in refrigerator in airtight container",
      "condition": "Fresh with slight wilting on stem",
      "recipes": ["Broccoli Stir-Fry", "Roasted Vegetables", "Soup"]
    },
    {
      "name": "Spinach",
      "emoji": "🥬",
      "daysLeft": 2,
      "freshness": "Use Soon",
      "storageTip": "Keep in plastic bag in crisper drawer",
      "condition": "Starting to wilt slightly",
      "recipes": ["Salad", "Smoothie", "Pasta"]
    }
  ]
}
```

## 🎯 UI Components Breakdown

### Upload Section
- Two upload options: Camera capture and file upload
- Image preview area
- User-friendly descriptions

### Ingredient Cards
- Ingredient emoji and name
- Freshness progress bar (color-coded)
- Status badge (Fresh/Use Soon/Use Today)
- Days remaining indicator
- Expandable details with storage tips and recipe suggestions

### Freshness Indicators
- **Green (> 5 days):** Fresh
- **Amber (2-5 days):** Use Soon
- **Red (< 2 days):** Use Today

## 🎨 Color Scheme

- Primary: `#10b981` (Green)
- Secondary: `#f59e0b` (Amber)
- Danger: `#ef4444` (Red)
- Light Background: `#f9fafb`

## 📱 Responsive Breakpoints

- **Desktop:** Full grid layout (auto-fill, minmax 250px)
- **Tablet (768px):** Adjusted typography and spacing
- **Mobile (480px):** Single column layout, simplified UI

## 🔒 Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

## 🧪 Testing

For testing, you can use mock data by modifying the `analyzeImage` function to return sample data instead of calling the API:

```javascript
// Mock data for testing
const mockData = {
  ingredients: [
    {
      name: "Broccoli",
      emoji: "🥦",
      daysLeft: 4,
      storageTip: "Store in refrigerator in airtight container",
      condition: "Fresh with slight wilting on stem",
      recipes: ["Stir-Fry", "Roasted", "Soup"]
    },
    // ... more items
  ]
};
setIngredients(mockData.ingredients);
```

## 📦 Build & Deployment

### Docker Deployment

Create a `Dockerfile` in the frontend directory:

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

### Deploy to Production

```bash
npm run build
# Upload dist/ folder to your hosting service
```

## 🐛 Troubleshooting

### Images not uploading?
- Check backend API is running on port 8000
- Verify CORS is enabled on backend
- Check browser console for error messages

### Freshness data not showing?
- Ensure backend returns the correct JSON structure
- Check API response in Network tab of DevTools
- Verify all required fields are present in response

### Styling issues?
- Clear browser cache (Ctrl+Shift+Del)
- Restart development server
- Check for CSS conflicts in main.css

## 🤝 Contributing

1. Create a new branch for your feature
2. Make changes and test thoroughly
3. Submit a pull request with clear description

## 📄 License

MIT License - feel free to use and modify

## 📞 Support

For issues or questions, please create an issue in the repository.

---

**Built with ❤️ for reducing food waste**
