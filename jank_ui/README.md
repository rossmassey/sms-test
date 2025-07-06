# SMS Outreach System - Demo UI

A React-based demonstration interface for the SMS outreach system backend.

## Technical Overview

This is a basic React application built with Create React App that provides a frontend interface for testing and demonstrating the SMS outreach system functionality. The app communicates with a FastAPI backend via REST API calls.

**Key Features:**
- Customer management interface
- AI conversation testing
- Mock SMS response simulation
- Manual staff intervention controls
- Real-time message updates (3-second polling)

## Requirements

- **Node.js**: 16.x or higher (tested with 16+)
- **npm**: 7.x or higher
- **Backend**: SMS outreach system running on port 8000

## Dependencies

### Production Dependencies
- **React**: ^18.2.0 - Core React library
- **React DOM**: ^18.2.0 - React DOM rendering
- **React Scripts**: 5.0.1 - Build toolchain from Create React App
- **Web Vitals**: ^2.1.4 - Performance metrics

### Development Dependencies
- **Testing Library**: Jest DOM, React, and User Event for testing
- **Proxy Configuration**: Configured to proxy API requests to `http://localhost:8000`

## Setup & Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the backend** (from project root):
   ```bash
   cd ..
   python run_dev.py
   ```
   Backend must be running on http://localhost:8000

3. **Start the frontend**:
   ```bash
   npm start
   ```
   Application will open on http://localhost:3000

## Build & Deploy

```bash
# Production build
npm run build

# Run tests
npm test

# Eject from Create React App (not recommended)
npm run eject
```

## API Integration

The application communicates with the backend via REST API calls. API requests are automatically proxied to the backend server through the proxy configuration in `package.json`.

## Limitations

- No real SMS integration (uses mock endpoints)
- Basic styling (intentionally minimal for rapid development)
- Simple error handling with browser alerts
- Hardcoded API configurations for demo purposes
