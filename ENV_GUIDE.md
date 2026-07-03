# Spotify Hybrid Player - Environment Variables Setup Guide

This guide explains how to configure environment variables for both the **Next.js frontend** and the **FastAPI backend** to connect services, persist data, and enable high-fidelity Spotify API metadata and recommendations.

---

## 💻 1. Frontend Configuration (`client/`)

The Next.js client uses `process.env.NEXT_PUBLIC_API_URL` to route requests to the backend API.

### Steps:
1. Navigate to the `client/` directory.
2. Duplicate the `.env.example` file and rename it to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and verify the API endpoint matches your local backend port (default: `8000`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

---

## 🐍 2. Backend Configuration (`server/`)

The Python backend queries SQLite and reads optional Spotify developer keys. If these credentials are omitted, the backend's source-resolver automatically falls back to searching public Audius and YouTube metadata pipelines directly so the application remains fully functional out-of-the-box.

### Steps:
1. Navigate to the `server/` directory.
2. Duplicate the `.env.example` file and rename it to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Set your SQLite database path (default: `sqlite:///./spotify.db`).
4. To fetch search listings and seeds recommendations directly from Spotify's global music database, you will need to retrieve Spotify Client credentials. Follow the tutorial below.

---

## 🔑 How to Get Spotify Developer Credentials

To retrieve your Client ID and Client Secret:

1. **Go to the Spotify Developer Dashboard:**
   Open your browser and navigate to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard). Log in using your standard Spotify credentials.

2. **Create a Developer Application:**
   * Click the green **Create app** button in the top-right corner.
   * **App name:** Enter a name (e.g., `Spotify Hybrid Replica`).
   * **App description:** Enter a description.
   * **Redirect URIs:** Enter a placeholder URI (e.g., `http://localhost:3000/callback`). (Note: Although our backend runs client credentials flow and does not require user OAuth, Spotify requires this field to save).
   * Agree to the Spotify Developer terms and click **Save**.

3. **Retrieve Credentials:**
   * Open your newly created application from the Dashboard.
   * Click **Settings** in the top-right corner.
   * Copy the **Client ID**.
   * Click **Show client secret** and copy the **Client Secret**.

4. **Add Keys to Environment:**
   * Open `server/.env` in your editor.
   * Paste your copied keys into the fields:
     ```env
     SPOTIFY_CLIENT_ID=your_actual_client_id_here
     SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here
     ```

---

## 🚀 Running the Project

Once the `.env` files are in place:

### Start Backend
In one terminal:
```bash
cd server
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

### Start Frontend
In another terminal:
```bash
cd client
npm run dev
```
Open `http://localhost:3000` to stream!
