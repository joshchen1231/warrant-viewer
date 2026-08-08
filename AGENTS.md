# 權證檢視器 (warrant-viewer) — project instruction file

- Conversation replies & human documents: Traditional Chinese. Code, comments, commit
  messages, machine docs: English.
- Sole build basis: docs/04-psm.md (design ladder: docs/01..04).
- Environment (Windows, PowerShell 5.1):
  - Python: use the `py` launcher (bare `python` may be a Microsoft Store stub).
  - Frontend: Node + Vite, dev server fixed http://localhost:5173 (strictPort), proxy /api -> 127.0.0.1:8000.
- Commands: backend tests `py -m pytest backend/tests`; frontend `npm run dev` / `npm run build`; backend server `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-server.ps1` (kills previous instance via data/server.pid and polls /api/health).
- Git: Conventional Commits; feature branch + PR, keep the default branch clean.
- UX language: Traditional Chinese only, no i18n module (D6).
