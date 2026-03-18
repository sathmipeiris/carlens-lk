# CarLensLK — Frontend

> Sri Lanka used car price intelligence dashboard built with Next.js 14.

## Project structure

```
car-price-app/
├── pages/
│   ├── _app.js          ← App wrapper (navbar injected here)
│   ├── index.js         ← Landing page
│   ├── predict.js       ← Price predictor form
│   ├── dashboard.js     ← Market dashboard (economic indicators)
│   └── trends.js        ← Brand price trends + charts
├── components/
│   ├── Navbar.jsx       ← Top navigation bar
│   └── StatCard.jsx     ← Reusable metric card
├── lib/
│   └── api.js           ← All Flask API calls (centralised here)
├── styles/
│   └── globals.css      ← Fonts, base styles, utility classes
├── tailwind.config.js
├── next.config.js
└── .env.local.example   ← Copy to .env.local
```

## Setup

### 1. Install dependencies
```bash
cd car-price-app
npm install
```

### 2. Configure environment
```bash
cp .env.local.example .env.local
# Edit .env.local if your Flask API runs on a different port
```

### 3. Start your Flask backend first
```bash
# In your backend folder:
python app.py
# Should print: Running on http://127.0.0.1:5000
```

### 4. Start the frontend
```bash
npm run dev
# Open: http://localhost:3000
```

## Pages

| Page | Route | Backend endpoint |
|------|-------|-----------------|
| Landing | `/` | None |
| Price Predictor | `/predict` | `POST /predict` |
| Market Dashboard | `/dashboard` | `GET /api/dashboard/economic-indicators` + `GET /api/dashboard/market-health` |
| Brand Trends | `/trends` | `GET /api/dashboard/brand-trends` |

## What each page does

**Predict** — Car details form (brand, YOM, mileage, fuel type, equipment toggles).
Sends a POST to your Flask `/predict` endpoint and displays the estimated price in LKR Lakhs.

**Dashboard** — Pulls live economic indicators (USD/LKR, inflation, petrol price, CSE ASPI).
Shows a health gauge (0-100 score), impact badges per indicator, and a full impact table.

**Trends** — Brand-level price cards + interactive area/line charts using Recharts.
Falls back to illustrative historical data if the backend is unavailable.

## Customisation

- **Add more brands**: Edit the `brands` array in `trends.js` and `MOCK_HISTORY`.
- **Change colours**: Edit `BRAND_COLORS` in `trends.js` and `--gold` in `globals.css`.
- **Add more API endpoints**: Add functions to `lib/api.js`, import them in any page.
- **Deploy**: `npm run build` → deploy `/out` folder to Vercel, Netlify, or any static host.

## Production build

```bash
npm run build
npm start
```

For Vercel (recommended):
```bash
npm i -g vercel
vercel
# Set NEXT_PUBLIC_API_URL to your deployed Flask backend URL
```
