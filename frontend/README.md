# Cyclecast frontend

React + TypeScript + Vite, built with Node.js 24 and a pinned npm lock file.

**Live:** [Cyclecast](https://169.58.96.231/bike-rentals/). The application has two views:

- **The case study:** eight chronological chapters explaining the business scenario, dataset, EDA, leakage prevention, initial model choice, grid search, measured results and potential business value.
- **Forecast lab:** five historical replays and a custom JSON request mode, calling the real prediction API.

Start the API on port 8003 first. Then, from this folder:

```bash
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/bike-rentals/`. Development and preview proxy API requests to the local backend; production uses the same `/bike-rentals/` path behind Nginx.

```bash
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser tests cover desktop/mobile views, real predictions, image loading, horizontal overflow and invalid custom input. Build output is ignored by Git. `package-lock.json` pins the frontend environment.

Code map:

- `src/App.tsx`: shared layout and view navigation.
- `src/pages/CaseStudy.tsx`: sequential project narrative.
- `src/pages/ForecastLab.tsx`: scenario loading and prediction state.
- `src/components/Charts.tsx`: charts and demand heatmap.
- `src/components/BusinessValue.tsx`: assumption-based planning-time calculator.
- `src/api.ts` and `src/types.ts`: API boundary.
- `src/styles.css`: shared visual system and responsive layout.
- `src/ride.css`: bike photography, editorial hero and responsive image layout.
- `public/images/` and [CREDITS.md](CREDITS.md): locally served cycling photos and attribution.

All measured values come from exported experiment artifacts. The financial calculator is explicitly hypothetical; no client profit or revenue lift is claimed. The replay is historical, not a current live-demand feed. Cycling photos illustrate city life rather than the source observations. The visual system uses charcoal, cream and orange, with an editorial photo-led hero.
