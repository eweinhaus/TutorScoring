# Sub-PRD: Frontend Dashboard
## Tutor Quality Scoring System - MVP

**Version:** 1.0  
**Parent PRD:** PRD_MVP.md  
**Dependencies:** PRD_Environment_Setup.md, PRD_Backend_Services.md  
**Status:** Ready for Implementation

---

## 1. Overview

### 1.1 Purpose
Build a React-based dashboard application that visualizes tutor performance data, displays risk flags, and provides actionable insights. The dashboard serves as the primary interface for administrators to monitor and manage tutor quality.

### 1.2 Goals
- Create intuitive, clean dashboard interface
- Display tutor list with reschedule rate flags
- Show detailed tutor performance metrics
- Visualize trends and patterns
- Enable quick identification of at-risk tutors
- Provide actionable insights and recommendations

### 1.3 Success Criteria
- ✅ Dashboard loads in <2 seconds
- ✅ Tutor list displays with risk flags
- ✅ Tutor detail view shows comprehensive metrics
- ✅ Charts and visualizations render correctly
- ✅ Real-time updates work (polling)
- ✅ Mobile-responsive design
- ✅ Clean, professional UI

---

## 2. Application Structure

### 2.1 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable components
│   │   ├── tutor/           # Tutor-specific components
│   │   └── charts/          # Chart components
│   ├── pages/
│   │   ├── Dashboard.jsx     # Main dashboard page
│   │   ├── TutorList.jsx     # Tutor list view
│   │   └── TutorDetail.jsx   # Tutor detail view
│   ├── services/
│   │   └── api.js            # API client
│   ├── hooks/
│   │   ├── useTutors.js      # Tutor data hook
│   │   └── useTutorDetail.js # Tutor detail hook
│   ├── utils/
│   │   ├── formatters.js     # Data formatting
│   │   └── constants.js      # Constants
│   ├── styles/
│   │   └── global.css        # Global styles
│   ├── App.jsx               # Main app component
│   └── main.jsx              # Entry point
├── public/
│   └── index.html
└── package.json
```

### 2.2 Technology Stack

**Core:**
- React 18+
- React Router 6+ (for navigation)
- Vite (build tool)

**Data Fetching:**
- React Query (@tanstack/react-query) - Server state management
- Axios - HTTP client

**Visualization:**
- Recharts - Chart library

**Styling:**
- CSS Modules or Tailwind CSS (recommended: Tailwind for speed)
- Responsive design utilities

---

## 3. Dashboard Pages

### 3.1 Main Dashboard Page

**File:** `src/pages/Dashboard.jsx`

**Purpose:** Overview with key metrics and quick access

**Components:**
- Summary cards (total tutors, high-risk count, etc.)
- Quick stats (average reschedule rate, recent activity)
- Navigation to tutor list
- Recent alerts or highlights

**Layout:**
```
┌─────────────────────────────────┐
│  Dashboard Header               │
├─────────────────────────────────┤
│  Summary Cards (3-4 metrics)    │
├─────────────────────────────────┤
│  Quick Stats                     │
├─────────────────────────────────┤
│  Recent Activity / Alerts        │
└─────────────────────────────────┘
```

### 3.2 Tutor List Page

**File:** `src/pages/TutorList.jsx`

**Purpose:** Display all tutors with reschedule rates and risk flags

**Features:**
- Table/grid view of tutors
- Sorting by reschedule rate, total sessions, name
- Filtering by risk status (high-risk, low-risk, all)
- Search by tutor name
- Pagination
- Click tutor to view details

**Table Columns:**
- Tutor Name
- Reschedule Rate (30-day)
- Risk Flag (visual indicator)
- Total Sessions (30-day)
- Last Updated
- Actions (view details)

**Visual Indicators:**
- Red badge for high-risk tutors
- Green badge for low-risk tutors
- Color-coded reschedule rates (red >15%, yellow 10-15%, green <10%)

**Filters:**
- Risk Status dropdown (All, High Risk, Low Risk)
- Sort dropdown (Rate, Sessions, Name)
- Search input (tutor name)

### 3.3 Tutor Detail Page

**File:** `src/pages/TutorDetail.jsx`

**Purpose:** Comprehensive view of individual tutor performance

**Sections:**

#### 3.3.1 Tutor Header
- Tutor name and email
- Overall risk status
- Quick stats (total sessions, reschedule rate)

#### 3.3.2 Reschedule Rate Trends
- Line chart showing rate over time (7-day, 30-day, 90-day)
- Time period selector
- Comparison to threshold line

#### 3.3.3 Recent Reschedules
- Table of recent reschedule events
- Columns: Date, Original Time, New Time, Reason, Hours Before
- Sortable and filterable

#### 3.3.4 Session Statistics
- Summary cards:
  - Total sessions (7d, 30d, 90d)
  - Tutor reschedules (7d, 30d, 90d)
  - Reschedule rates (7d, 30d, 90d)

#### 3.3.5 Insights & Recommendations
- AI-generated or rule-based insights
- Actionable recommendations
- Risk level description

**Layout:**
```
┌─────────────────────────────────┐
│  Tutor Header                   │
├─────────────────────────────────┤
│  Reschedule Rate Chart          │
├─────────────────────────────────┤
│  Recent Reschedules Table       │
├─────────────────────────────────┤
│  Statistics Cards               │
├─────────────────────────────────┤
│  Insights & Recommendations     │
└─────────────────────────────────┘
```

---

## 4. React Components

### 4.1 Common Components

**Location:** `src/components/common/`

#### 4.1.1 Header Component
- App title and navigation
- User info (if authentication added)

#### 4.1.2 Loading Spinner
- Reusable loading indicator
- Used during data fetching

#### 4.1.3 Error Message
- Error display component
- Retry functionality

#### 4.1.4 Risk Badge
- Visual risk indicator
- Color-coded (red/yellow/green)
- Shows risk level text

#### 4.1.5 DataTable
- Reusable table component
- Sorting, filtering, pagination
- Responsive design

### 4.2 Tutor Components

**Location:** `src/components/tutor/`

#### 4.2.1 TutorCard
- Summary card for tutor
- Used in list view
- Clickable to navigate to detail

#### 4.2.2 TutorRow
- Table row component
- Displays tutor data in list
- Risk indicators

#### 4.2.3 RescheduleTable
- Table of reschedule events
- Sortable columns
- Date formatting

### 4.3 Chart Components

**Location:** `src/components/charts/`

#### 4.3.1 RescheduleRateChart
- Line chart showing rate trends
- Multiple time periods
- Threshold line indicator

**Chart Data:**
```javascript
{
  data: [
    { date: "2024-01-01", rate7d: 12.5, rate30d: 15.2, rate90d: 14.8 },
    { date: "2024-01-08", rate7d: 15.0, rate30d: 16.5, rate90d: 15.1 }
  ],
  threshold: 15.0
}
```

#### 4.3.2 StatsCard
- Summary statistic card
- Label, value, trend indicator
- Color-coded by value

---

## 5. API Integration

### 5.1 API Client Service

**File:** `src/services/api.js`

**Purpose:** Centralized API communication

**Methods:**
- `getTutors(filters)` - Fetch tutor list
- `getTutor(id)` - Fetch tutor details
- `getTutorHistory(id, days)` - Fetch reschedule history
- `createSession(sessionData)` - Submit session (for testing)

**Implementation:**
```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL;
const API_KEY = import.meta.env.VITE_API_KEY;

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

export const getTutors = async (filters = {}) => {
  const response = await apiClient.get('/tutors', { params: filters });
  return response.data;
};

export const getTutor = async (id) => {
  const response = await apiClient.get(`/tutors/${id}`);
  return response.data;
};

export const getTutorHistory = async (id, days = 90) => {
  const response = await apiClient.get(`/tutors/${id}/history`, {
    params: { days }
  });
  return response.data;
};
```

### 5.2 React Query Hooks

**File:** `src/hooks/useTutors.js`

**Purpose:** Custom hook for tutor data with caching

**Implementation:**
```javascript
import { useQuery } from '@tanstack/react-query';
import { getTutors } from '../services/api';

export const useTutors = (filters = {}) => {
  return useQuery({
    queryKey: ['tutors', filters],
    queryFn: () => getTutors(filters),
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000 // Poll every 30 seconds
  });
};
```

**File:** `src/hooks/useTutorDetail.js`

**Purpose:** Custom hook for tutor detail data

**Implementation:**
```javascript
import { useQuery } from '@tanstack/react-query';
import { getTutor, getTutorHistory } from '../services/api';

export const useTutorDetail = (tutorId) => {
  const tutorQuery = useQuery({
    queryKey: ['tutor', tutorId],
    queryFn: () => getTutor(tutorId),
    enabled: !!tutorId
  });

  const historyQuery = useQuery({
    queryKey: ['tutor-history', tutorId],
    queryFn: () => getTutorHistory(tutorId),
    enabled: !!tutorId
  });

  return {
    tutor: tutorQuery.data,
    history: historyQuery.data,
    isLoading: tutorQuery.isLoading || historyQuery.isLoading,
    error: tutorQuery.error || historyQuery.error
  };
};
```

### 5.3 Real-Time Updates

**Strategy:** Polling every 30 seconds

**Implementation:**
- Use React Query's `refetchInterval`
- Update query keys when data changes
- Show loading states during updates

---

## 6. Data Formatting & Utilities

### 6.1 Formatters

**File:** `src/utils/formatters.js`

**Functions:**
- `formatPercentage(value)` - Format as percentage (e.g., 15.5%)
- `formatDate(date)` - Format date (e.g., "Jan 15, 2024")
- `formatDateTime(date)` - Format datetime
- `formatHours(hours)` - Format hours (e.g., "12.5 hours")
- `getRiskColor(rate, threshold)` - Get color for risk level

**Example:**
```javascript
export const formatPercentage = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)}%`;
};

export const getRiskColor = (rate, threshold = 15) => {
  if (rate >= threshold) return 'red';
  if (rate >= threshold * 0.67) return 'yellow';
  return 'green';
};
```

### 6.2 Constants

**File:** `src/utils/constants.js`

**Constants:**
- Risk thresholds
- Time period options
- Status values
- API endpoints

---

## 7. Styling & Design

### 7.1 Design System

**Color Palette:**
- Primary: Blue (#3B82F6)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Danger: Red (#EF4444)
- Neutral: Gray scale

**Typography:**
- Headings: Bold, large size
- Body: Regular, readable size
- Labels: Small, muted color

### 7.2 Component Styling

**Approach:** Tailwind CSS (recommended) or CSS Modules

**Tailwind Benefits:**
- Fast development
- Responsive utilities
- Consistent spacing
- Easy customization

**Example Component:**
```jsx
<div className="bg-white rounded-lg shadow p-6">
  <h2 className="text-xl font-bold mb-4">Tutor List</h2>
  <div className="overflow-x-auto">
    {/* Table content */}
  </div>
</div>
```

### 7.3 Responsive Design

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

**Responsive Patterns:**
- Stack cards vertically on mobile
- Horizontal layout on desktop
- Collapsible filters on mobile
- Full-width tables on mobile

---

## 8. Routing

### 8.1 Route Configuration

**File:** `src/App.jsx`

**Routes:**
- `/` - Dashboard (overview)
- `/tutors` - Tutor list
- `/tutors/:id` - Tutor detail

**Implementation:**
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TutorList from './pages/TutorList';
import TutorDetail from './pages/TutorDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tutors" element={<TutorList />} />
        <Route path="/tutors/:id" element={<TutorDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 9. State Management

### 9.1 Server State (React Query)

**Usage:**
- All API data managed by React Query
- Automatic caching and refetching
- Loading and error states handled

### 9.2 Local State (React State)

**Usage:**
- UI state (filters, sort options)
- Form inputs
- Modal visibility
- Component-specific state

### 9.3 Context (Optional)

**If Needed:**
- Global UI state (theme, user preferences)
- Not needed for MVP

---

## 10. Error Handling

### 10.1 API Error Handling

**Strategies:**
- React Query error boundaries
- Error message display
- Retry functionality
- Fallback UI

### 10.2 User-Friendly Messages

**Error Types:**
- Network errors: "Unable to connect to server"
- Not found: "Tutor not found"
- Server errors: "Something went wrong. Please try again."
- Validation errors: Display specific messages

---

## 11. Performance Optimization

### 11.1 Code Splitting

**Lazy Loading:**
- Route-based code splitting
- Load components on demand

**Implementation:**
```jsx
import { lazy, Suspense } from 'react';

const TutorDetail = lazy(() => import('./pages/TutorDetail'));

<Suspense fallback={<LoadingSpinner />}>
  <TutorDetail />
</Suspense>
```

### 11.2 Memoization

**React.memo:**
- Memoize expensive components
- Prevent unnecessary re-renders

**useMemo:**
- Memoize computed values
- Expensive calculations

### 11.3 Image Optimization

**If Needed:**
- Optimize images
- Use appropriate formats
- Lazy load images

---

## 12. Testing

### 12.1 Component Tests (Optional for MVP)

**Tools:**
- Vitest (testing framework)
- React Testing Library

**Test Areas:**
- Component rendering
- User interactions
- Data display

### 12.2 Manual Testing Checklist

- [ ] Dashboard loads correctly
- [ ] Tutor list displays all tutors
- [ ] Filters and sorting work
- [ ] Tutor detail page loads
- [ ] Charts render correctly
- [ ] Real-time updates work
- [ ] Mobile responsive
- [ ] Error handling works
- [ ] Navigation works

---

## 13. Deployment

### 13.1 Build Configuration

**Vite Build:**
```bash
npm run build
```

**Output:**
- `dist/` directory with static files
- Optimized and minified
- Source maps for debugging

### 13.2 Render Static Site

**Configuration:**
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`
- Environment variables: Set `VITE_API_URL`

### 13.3 Environment Variables

**Production:**
- `VITE_API_URL` - Backend API URL
- `VITE_API_KEY` - API key (if needed client-side)

---

## 14. Success Criteria

### 14.1 Functional Requirements

- [ ] Dashboard displays correctly
- [ ] Tutor list shows all tutors with risk flags
- [ ] Tutor detail page shows comprehensive data
- [ ] Charts render with accurate data
- [ ] Filters and sorting work
- [ ] Real-time updates function
- [ ] Navigation works smoothly

### 14.2 Performance Requirements

- [ ] Dashboard loads in <2 seconds
- [ ] Smooth scrolling and interactions
- [ ] Charts render quickly
- [ ] No lag during updates

### 14.3 Usability Requirements

- [ ] Intuitive navigation
- [ ] Clear visual indicators
- [ ] Mobile-responsive design
- [ ] Accessible (basic WCAG compliance)
- [ ] Professional appearance

---

## 15. Dependencies

### 15.1 Required

- Backend Services complete (PRD_Backend_Services.md)
- API endpoints functional
- Test data available

### 15.2 External

- React Query for data fetching
- Recharts for visualizations
- Tailwind CSS for styling (or CSS Modules)

---

## 16. Future Enhancements

**Post-MVP:**
- Advanced filtering options
- Export functionality (CSV, PDF)
- Real-time WebSocket updates
- User authentication
- Customizable dashboards
- More chart types
- Drill-down analytics

---

## 17. Next Steps

After completing Frontend Dashboard:

1. **Integration Testing**
   - End-to-end testing
   - API integration verification
   - User acceptance testing

2. **Deployment**
   - Deploy to Render
   - Configure production environment
   - Monitor performance

3. **Documentation**
   - User guide
   - API documentation
   - Demo video preparation

