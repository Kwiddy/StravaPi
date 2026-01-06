# Strava Dashboard

A simple dashboard for viewing your Strava running activities.

## Prerequisites

- Python 3.x
- Node.js and npm
- Strava API credentials (Client ID and Client Secret)

## Setup

### 1. Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install requests python-dotenv flask flask-cors
```

**Important:** Make sure `flask-cors` is installed. If you get CORS errors, verify installation with:
```bash
pip list | grep -i flask
```

3. Set up your Strava API tokens:
```bash
python setup_tokens.py
```

This will guide you through:
- Entering your Strava Client ID and Client Secret
- Authorizing the application
- Saving tokens to a `.env` file

### 2. Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Project

### Backend API Server

Start the Flask API server (required for the frontend):
```bash
cd backend
python api.py
```

The API server will run on `http://localhost:5489`.

**Note:** You can also run the CLI script directly to view runs in the terminal:
```bash
cd backend
python strava_runs.py
```

### Frontend

To start the React development server:
```bash
cd frontend
npm start
```

The app will open in your browser at `http://localhost:3000` and will display all runs and swims from the start of the current year.

**Note:** Activities are cached locally in `backend/activities.json` for fast loading. Click the refresh button to fetch new activities from Strava.

## Environment Variables

The backend requires a `.env` file in the `backend` directory with:
- `STRAVA_CLIENT_ID` - Your Strava application Client ID
- `STRAVA_CLIENT_SECRET` - Your Strava application Client Secret
- `STRAVA_ACCESS_TOKEN` - Your Strava access token
- `STRAVA_REFRESH_TOKEN` - Your Strava refresh token

These are automatically set up when you run `setup_tokens.py`.

## Caching System

The application uses a local caching system optimized for Raspberry Pi:

- **Fast Loading**: Activities are stored in `backend/activities.json` and load instantly on app startup
- **Efficient Updates**: Click the refresh button to fetch only new activities from Strava API
- **Smart Fetching**: Stops fetching once it encounters activities already in cache
- **Offline Support**: App works offline, showing cached data even without internet connection

The cache file is automatically created on first refresh and updated whenever you click the refresh button.

