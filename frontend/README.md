# Frontend Dashboard - Tutor Quality Scoring System

React-based dashboard for monitoring tutor performance and quality metrics.

## Setup Instructions

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn package manager

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with your backend API URL:
   ```env
   VITE_API_URL=http://localhost:8001
   VITE_API_KEY=your-api-key-here
   ```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── common/      # Reusable components (Header, LoadingSpinner, etc.)
│   │   ├── tutor/       # Tutor-specific components
│   │   └── charts/      # Chart components
│   ├── pages/           # Page components (Dashboard, TutorList, TutorDetail)
│   ├── hooks/           # Custom React hooks (useTutors, useTutorDetail)
│   ├── services/        # API client service
│   ├── utils/           # Utility functions and constants
│   ├── styles/          # Global styles
│   ├── App.jsx          # Main app component with routing
│   └── main.jsx         # Entry point
├── public/              # Static assets
├── package.json         # Dependencies and scripts
└── vite.config.js       # Vite configuration
```

## Features

- **Dashboard**: Overview of tutor metrics and statistics
- **Tutor List**: Filterable and sortable list of all tutors
- **Tutor Detail**: Comprehensive view of individual tutor performance
- **Real-time Updates**: Automatic polling every 30 seconds
- **Responsive Design**: Works on mobile, tablet, and desktop
- **Charts**: Visual representation of reschedule rate trends
- **Risk Badges**: Color-coded indicators for tutor risk levels

## Technology Stack

- **React 18+**: UI framework
- **React Router 6+**: Client-side routing
- **React Query**: Server state management and caching
- **Axios**: HTTP client
- **Recharts**: Chart library
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Build tool and dev server

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8001)
- `VITE_API_KEY`: API key for backend authentication (optional)

## API Integration

The frontend communicates with the backend API at `/api` endpoints:

- `GET /api/tutors` - List tutors with filters
- `GET /api/tutors/:id` - Get tutor details
- `GET /api/tutors/:id/history` - Get tutor reschedule history
- `POST /api/sessions` - Create session (for testing)

## Development Notes

- The app uses React Query for data fetching with automatic caching
- Pages are lazy-loaded for code splitting
- Components are memoized for performance optimization
- Tailwind CSS is used for styling

## Deployment

For production deployment, ensure:

1. Environment variables are set correctly
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Backend API URL is configured for production

See `render.yaml` for Render deployment configuration.

