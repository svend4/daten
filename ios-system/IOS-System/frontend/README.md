# 🎨 IOS SYSTEM - FRONTEND

Modern React application built with TypeScript, Vite, and Tailwind CSS.

---

## 📋 TECH STACK

**Core:**
- ⚛️ React 18
- 📘 TypeScript
- ⚡ Vite
- 🎨 Tailwind CSS

**State Management:**
- 🐻 Zustand (Auth state)
- 🔄 TanStack Query (Server state)

**Routing:**
- 🛣️ React Router v6

**UI/UX:**
- 🎭 Lucide React (Icons)
- 🔔 Sonner (Toast notifications)
- 📊 Recharts (Charts)

**Forms:**
- 📝 React Hook Form
- ✅ Zod (Validation)

---

## 🚀 QUICK START

### 1. Installation

```bash
cd frontend
npm install
```

### 2. Environment Setup

```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_URL=http://localhost:8000
```

### 3. Development

```bash
npm run dev
```

Open http://localhost:3000

### 4. Production Build

```bash
npm run build
npm run preview
```

---

## 📁 PROJECT STRUCTURE

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   └── Layout.tsx     # Main layout with sidebar
│   ├── pages/             # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── DocumentsPage.tsx
│   ├── services/          # API services
│   │   └── api.ts         # API client
│   ├── store/             # State management
│   │   └── authStore.ts   # Auth state
│   ├── hooks/             # Custom hooks
│   ├── types/             # TypeScript types
│   ├── utils/             # Utility functions
│   ├── App.tsx            # Main app component
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── public/                # Static assets
├── index.html             # HTML template
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies
```

---

## 🎨 FEATURES

### ✅ Implemented

**Authentication:**
- Login/Logout
- JWT token management
- Protected routes
- Session persistence

**Dashboard:**
- Statistics cards
- Recent activity feed
- Quick actions

**Documents:**
- List view with pagination
- Search and filtering
- CRUD operations
- Category management

**UI Components:**
- Responsive layout
- Sidebar navigation
- Mobile menu
- Toast notifications
- Loading states
- Error handling

**State Management:**
- Auth state (Zustand)
- Server state (TanStack Query)
- Persistent storage

---

## 🔧 CONFIGURATION

### API Integration

All API calls go through `/src/services/api.ts`:

```typescript
import api from '@services/api'

// Usage
const documents = await api.getDocuments()
const user = await api.getCurrentUser()
```

### Auth State

```typescript
import { useAuthStore } from '@store/authStore'

function MyComponent() {
  const { user, login, logout } = useAuthStore()
  
  // Use auth state
}
```

### Protected Routes

Routes automatically redirect to `/login` if not authenticated.

---

## 🎯 PAGES

### 1. Login Page (`/login`)
- Username/password form
- Remember me checkbox
- Forgot password link
- Demo credentials display
- Error handling

### 2. Dashboard (`/dashboard`)
- Statistics overview
- Recent activity
- Quick actions
- Real-time updates

### 3. Documents (`/documents`)
- Document list
- Search & filters
- Pagination
- CRUD actions
- Category management

### 4. Search (Coming Soon)
- Full-text search
- Semantic search
- Filters
- Results display

### 5. Settings (Coming Soon)
- User profile
- Preferences
- Security settings

---

## 🎨 STYLING

### Tailwind CSS

Using custom color scheme:

```javascript
primary: {
  50: '#f0f9ff',
  500: '#0ea5e9',
  600: '#0284c7',
  700: '#0369a1',
}
```

### Custom Components

Consistent design system:
- Rounded corners (lg = 0.5rem)
- Shadow elevations
- Hover states
- Focus states
- Transitions

---

## 🔐 AUTHENTICATION FLOW

```
1. User enters credentials
   ↓
2. POST /api/auth/login
   ↓
3. Receive JWT token
   ↓
4. Store in localStorage
   ↓
5. Add to all API requests
   ↓
6. Redirect to /dashboard
```

**Token Storage:**
- `localStorage.getItem('auth_token')`
- Automatically added to headers
- Cleared on logout

**Protected Routes:**
- Check `isAuthenticated` from store
- Redirect to `/login` if false
- Fetch user on app mount

---

## 📊 STATE MANAGEMENT

### Auth Store (Zustand)

```typescript
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username, password) => Promise<void>
  logout: () => Promise<void>
  fetchUser: () => Promise<void>
}
```

**Persisted to localStorage**

### Server State (TanStack Query)

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.getDocuments(),
})
```

**Benefits:**
- Automatic caching
- Background refetching
- Loading/error states
- Devtools

---

## 🧪 TESTING

```bash
# Run tests
npm run test

# Run with UI
npm run test:ui
```

---

## 🔨 BUILD & DEPLOYMENT

### Development Build

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

Output: `dist/`

### Preview Production Build

```bash
npm run preview
```

### Environment Variables

**Development** (`.env.development`):
```env
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

**Production** (`.env.production`):
```env
VITE_API_URL=https://api.yourdomain.com
VITE_ENV=production
```

---

## 📦 DEPLOYMENT

### Option 1: Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/ios-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### Option 2: Docker

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Option 3: Vercel/Netlify

```bash
npm run build
# Deploy dist/ folder
```

---

## 🐛 TROUBLESHOOTING

### API Connection Issues

```typescript
// Check VITE_API_URL in .env
console.log(import.meta.env.VITE_API_URL)

// Check network tab in DevTools
// Should see requests to http://localhost:8000/api
```

### Auth Token Not Persisting

```typescript
// Check localStorage
console.log(localStorage.getItem('auth_token'))

// Clear and re-login
localStorage.clear()
```

### Build Errors

```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

---

## 📚 API ENDPOINTS USED

```
Auth:
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/auth/me

Documents:
  GET    /api/documents
  GET    /api/documents/:id
  POST   /api/documents
  PATCH  /api/documents/:id
  DELETE /api/documents/:id

Search:
  GET    /api/search
  POST   /api/search/semantic

Dashboard:
  GET    /api/dashboard
  GET    /api/activity/recent

Tags:
  GET    /api/tags
  POST   /api/tags
```

---

## 🎓 BEST PRACTICES

### Component Structure

```typescript
// Good
function MyComponent() {
  // Hooks
  const { data } = useQuery(...)
  const navigate = useNavigate()
  
  // Handlers
  const handleClick = () => {...}
  
  // Render
  return <div>...</div>
}
```

### API Calls

```typescript
// Good - Use TanStack Query
const { data } = useQuery({
  queryKey: ['documents'],
  queryFn: () => api.getDocuments(),
})

// Bad - Direct fetch in component
useEffect(() => {
  fetch('/api/documents')
}, [])
```

### Error Handling

```typescript
// API errors handled globally in axios interceptor
// Toast notifications shown automatically
// Component-level error states via TanStack Query
```

---

## 🔄 FUTURE ENHANCEMENTS

- [ ] Search page
- [ ] Settings page
- [ ] Document editor (rich text)
- [ ] Real-time collaboration
- [ ] Dark mode
- [ ] Mobile app (React Native)
- [ ] Offline mode (PWA)
- [ ] i18n (Internationalization)
- [ ] Accessibility improvements
- [ ] Analytics integration

---

## 📝 SCRIPTS

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
npm run test         # Run tests
npm run test:ui      # Run tests with UI
```

---

## 🤝 CONTRIBUTING

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Write meaningful commit messages
4. Test before committing
5. Keep components small and focused

---

**Version:** 1.0  
**Last Updated:** December 15, 2024  
**Author:** IOS System Team
