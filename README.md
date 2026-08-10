# Warrant Viewer (權證檢視器)

https://joshchen1231.github.io/warrant-viewer/

A local-first Taiwan warrant screening tool. Pick an underlying stock, filter
call/put warrants by exercise ratio, IV, moneyness, days to maturity and more,
and sort the results. Built for a single user on a local machine.

## Features

- After-hours warrant data collection from official sources (TWSE / TPEx)
  with a daily scheduler; results stored in a local SQLite database
- Underlying stock search and warrant list with live filtering + sorting
- Reusable saved filter presets (stored in browser localStorage)
- TSE realtime warrant quotes (intraday, polled every 20s) via the official
  `mis.twse.com.tw` API, with graceful degradation when the market is closed
- Traditional Chinese UI

## Tech stack

- Backend: Python 3.12 + FastAPI + uvicorn, SQLite (stdlib), pandas, APScheduler
- Pricing math: numpy + scipy (B-S implied volatility, Greeks)
- Frontend: Vite 8 + TypeScript (vanilla, no framework)

## Requirements

- Windows, PowerShell
- Python 3.12 (invoke via the `py` launcher)
- Node.js + npm — only if you want to develop the frontend; the prebuilt
  frontend is served directly by the backend

## Setup & run

```powershell
py -m pip install -r backend\requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-server.ps1
# open http://localhost:5173
```

Frontend development (optional):

```powershell
cd frontend
npm install
npm run dev        # dev server on http://localhost:5173 (proxies /api to 127.0.0.1:8000)
```

## Data collection

A scheduler runs after market close (16:30 Asia/Taipei) automatically. To
trigger a collection manually, set the token env var first, then POST to the
collect endpoint:

```powershell
$env:WARRANT_COLLECT_TOKEN = "your-secret"
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/data/collect -Method Post `
  -Headers @{ "X-Collect-Token" = $env:WARRANT_COLLECT_TOKEN }
```

Without the token set, the collect endpoint is always rejected (403).

## Tests

```powershell
py -m pytest backend\tests
```

## Data sources & disclaimer

- After-hours data: TWSE and TPEx official open endpoints
- TSE intraday quotes: official `mis.twse.com.tw` API
- OTC (TPEx) has no public free intraday source; realtime quotes are TSE-only
- All data is provided for reference only and is not investment advice.
  Data may be delayed or incomplete; verify before acting on it.

## License

MIT — see [LICENSE](LICENSE).
