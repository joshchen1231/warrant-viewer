# 權證檢視器 — 施工規格（PSM）

> 階層：PSM（平台特定模型）｜主體語言：English（spec body，給實作會話讀）
> 中文僅用於使用者決策面：測量結果、決策登記、手動 UAT 檢查表、降級宣告、開放問題
> 日期：2026-08-08｜狀態：定案（D1–D9 已裁定；唯一待答問題見 §12）
> **Sole build basis**：本文件為唯一施工依據。所有規範內文在此內聯，不委託其他文件。

---

## 1. Stack & versions (decided 2026-08-08; 中文理由見 §10 決策登記)

| Layer | Choice | Version (pin at install) |
|---|---|---|
| Backend | Python 3.12 + FastAPI + uvicorn | fastapi>=0.115, uvicorn>=0.30 |
| Storage | SQLite (stdlib `sqlite3`, single file) | bundled with Python 3.12 |
| Data pipeline | pandas + requests + APScheduler | pandas>=2.2, requests>=2.32, APScheduler>=3.10 |
| Pricing math | numpy + scipy (brentq for IV inverse; optimize for M2) | numpy>=2.0, scipy>=1.14 |
| Frontend | Vite 8 + TypeScript (vanilla, no framework; see §10 D4) + ECharts | vite ^8.2.0, echarts ^6 (bare Vite + TS scaffold convention) |
| Tests | pytest (backend) / vitest (frontend, minimal) | pytest>=8.0 |
| Repo | git feature-branch + PR (L0 ops level) | — |

## 2. Environment facts (locally verified 2026-08-08)

- Windows 11, PowerShell 5.1 default shell.
- Python 3.12; **always invoke via `py` launcher** (bare `python` is a Microsoft Store stub).
- scipy / pandas / fastapi NOT yet installed; install in M0 (`py -m pip install ...`), then `py -m pip freeze > requirements.txt` for the pinned manifest (dependency intake rule).
- Node v24 + npm on PATH. Vite dev server MUST run at `http://localhost:5173` with `server: { host: 'localhost', port: 5173, strictPort: true }`.
- Frontend scaffold convention: bare Vite + TS, no framework.
- User interface language: Traditional Chinese only (single user; no i18n module — recorded decision D6).
- Data sources (verified this session, endpoints live):
  - TPEx OpenAPI (base `https://www.tpex.org.tw/openapi/v1`): `/tpex_warrant`, `/tpex_warrant_issue`, `/tpex_warrant_daily_quts`, `/tpex_warrant_wcb_daily_quts`, `/tpex_warrant_wxy_daily_quts` (+ monthly variants). JSON or CSV. Fields: `Code, Name, UnderlyingCode/UnderlyingStockCode, Call/Put, ExerciseStyle, American/European, LatestStrikePrice, LatestExerciseRatio, ExpirationDate, Open, High, Low, Close, UnderlyingStockClosePrice, TradeVol., ...`.
  - TWSE OpenAPI (base `https://openapi.twse.com.tw/v1`): `/opendata/t187ap37_L` (上市權證基本資料彙總表; 20 fields incl. `最新標的履約配發數量(每仟單位權證)`, `最新履約價格(元)/履約指數`, `最後交易日`, `履約截止日`), `/opendata/t187ap42_L` (上市認購(售)權證每日成交資料檔: 成交金額/張數 — no close price).
  - TWSE 上市權證每日收盤行情彙總表: HTML page `https://www.twse.com.tw/zh/products/securities/warrant/infomation/stock.html` with CSV download (≈1 month history) and `data-api="/stock/warrantStock"` JSON endpoint whose exact params are NOT yet reverse-engineered (G2).
  - Fallback source (G2): `mis.twse.com.tw` warrant quotes (proven feasible by prior art `vaalgit/WarrantsStrategy`).
  - Risk-free rate: Taiwan Bank 1-year time-deposit rate, manually maintained in config (G4).

## 3. File layout (implements PIM §5 tables; milestones per §8)

```
權證檢視器/
├── AGENTS.md
├── docs/                     # design ladder docs (this set) + references/context.md
├── data/                     # SQLite db file (gitignored)
├── backend/
│   ├── requirements.txt      # pinned (frozen after M0 install)
│   ├── run.py                # uvicorn entry; binds 127.0.0.1:8000
│   ├── app/
│   │   ├── main.py           # FastAPI app factory; serves ../frontend/dist when built
│   │   ├── config.py         # risk-free rate, defaults, paths
│   │   ├── validation.py     # INV-10 unified allowlist layer (single module)
│   │   ├── db.py             # sqlite3 wrapper + schema migrations (schema_migrations table)
│   │   ├── models.py         # dataclasses mirroring PIM schemas
│   │   ├── collectors/
│   │   │   ├── base.py       # provider interface: fetch → normalized rows
│   │   │   ├── tpex.py       # TPEx OpenAPI warrant endpoints (incl. wcb/wxy)
│   │   │   ├── twse.py       # t187ap37_L, t187ap42_L, warrantStock/CSV (G2 ladder)
│   │   │   ├── mis_fallback.py
│   │   │   ├── underlying.py # underlying daily close (TWSE/TPEx daily close APIs)
│   │   │   └── scheduler.py  # APScheduler: 16:30 weekdays; manual trigger endpoint
│   │   ├── pricing/
│   │   │   ├── black_scholes.py   # C/P price + Greeks (per-warrant-unit = ratio × BS)
│   │   │   ├── implied_vol.py     # brentq inverse (INV-3)
│   │   │   ├── hv.py              # HV20 = stdev(ln-returns)×√252
│   │   │   ├── metrics.py         # moneyness, premium, leverage, breakeven, payoff
│   │   │   └── scenario.py        # scenario return rates (M1)
│   │   ├── optimizer.py       # M2 allocation (scipy.optimize)
│   │   └── routers/           # warrants.py, analysis.py, optimize.py, data.py
│   └── tests/
│       ├── fixtures/          # captured real API responses (frozen, committed)
│       └── test_*.py
├── frontend/
│   ├── package.json, vite.config.ts   # port 5173 strictPort; dev proxy /api → 127.0.0.1:8000
│   └── src/
│       ├── api/client.ts      # typed API client
│       ├── pages/             # Search / WarrantList / WarrantDetail / Optimize / DataStatus
│       ├── components/        # FilterBar, WarrantTable, charts (ECharts wrappers)
│       └── styles/            # 簡潔自訂 visual direction (D5)
└── scripts/                   # dev helpers (collect-once, db-migrate)
```

## 4. Data model (SQLite; implements PIM §5, INV-1..9)

Tables mirror PIM §5 with these physical rules:

- `WarrantMaster`: PK `code`. **Upsert semantics** (latest disclosure wins — G6); row kept after delisting with `active` flag. Column mapping normalizes G1: TPEx `LatestExerciseRatio` as-is; TWSE `最新標的履約配發數量(每仟單位權證) / 1000`.
- `DailyQuote`, `UnderlyingDaily`, `Analysis`: PK `(code, date)` (INV-1). Append-only (INV-6); collector checks existence before insert.
- `Analysis.paramsSnapshot`: JSON `{"model":"black_scholes_european","risk_free_rate":0.0x,"computed_on":"YYYY-MM-DD"}` (INV-9). `status`: `OK | IV_FAILED | UNDERLYING_MISSING` (INV-3, INV-5).
- `CollectLog`: one row per (date, market) job attempt (INV-8); `status ∈ SUCCESS|PARTIAL|FAILED`; message carries per-source row counts and failures.
- Migration: `schema_migrations` table; each migration = numbered SQL script `scripts/migrate/000N.sql` + reverse `000N_down.sql` (rollback path).

**Error paths**: collector network failure → that (date, market) attempt marked FAILED in CollectLog, nothing written (transaction per job, INV-8); UI data-status endpoint surfaces missing dates prominently (R9). Retry ≤3 then stop until next trading day (state machine §4.1 PIM).

## 5. Computation layer (implements R3, R6; exact formulas = contract)

Conventions: S = underlying close, K = latest strike, T = years to expiry (calendar/365), r = config risk-free rate, σ = volatility, R = exercise ratio, Pw = warrant close price.

- **B-S price per warrant unit**: `V_unit = R × BS(S, K, T, r, σ)` for call; put symmetric. Greeks scaled by R likewise. (INV-2 guards R>0.)
- **Close IV** (INV-3): solve `R × BS(S,K,T,r,σ) = Pw` for σ∈[0,5] via `scipy.optimize.brentq`; failure → NULL + `IV_FAILED`.
- **Theoretical Price**: `V_unit` at Close IV (for display/repro).
- **Moneyness**: call `S/K − 1`; put `K/S − 1`.
- **Premium (溢價率)**: call `(K − S + Pw/R)/S`; put `(S − K + Pw/R)/S`.
- **Leverage**: `S / (Pw/R)`.
- **Break-even**: call `K + Pw/R`; put `K − Pw/R`.
- **HV20**: annualized stdev of daily log returns of underlying, 20-day window, ×√252.
- **Payoff / Return Rate (M1)**: scenario = underlying moves ±x% (user-set grid, default ±5/±10), IV held constant (explicit assumption shown in UI, R8/R6): new warrant value via B-S at shifted S; Return Rate = (new − Pw)/Pw. Also payoff at expiry `max(S_K − K,0)·R − Pw` (call) charted.
- **Delta** (M1): analytic BS delta × R.

## 6. API contract (implements INV-10; single validation layer in `validation.py`)

Base: `http://127.0.0.1:8000`. All responses JSON; errors: `{"error": {"code": "VALIDATION|NOT_FOUND|UPSTREAM|INTERNAL", "message": <generic for 5xx, specific for 4xx>}}`.

| Method/Path | Query/Body | Response |
|---|---|---|
| GET `/api/health` | — | `{status: "ok", data_date: "YYYY-MM-DD"}` |
| GET `/api/underlying/search?q=` | q: code or name prefix, len 1..20, `[0-9A-Za-z\u4e00-\u9fff]` | list of `{code, name, market}` |
| GET `/api/warrants` | `underlying_code` (required), optional filters: `market[TSE/OTC]`, `call_put[CALL/PUT]`, `exercise_ratio_min`, `iv_max`, `iv_min`, `moneyness_min/max`, `days_to_maturity_min/max`, `issuer`, `warrant_type`; all numeric ranges numeric allowlist; `sort` whitelist | `{data_date, rows:[{code,name,market,callPut,strikePrice,exerciseRatio,close,ivClose,delta,moneyness,premium,leverage,ttmDays,issuer,status}]}` |
| GET `/api/warrants/{code}` | code `[0-9A-Za-z]{4,8}` | full WarrantMaster + latest DailyQuote + Analysis |
| GET `/api/warrants/{code}/history` | `metric ∈ [close, ivClose, premium, moneyness, leverage]`, optional date range | `[{date, value}]` (≥2 points or 404-ish empty) |
| GET `/api/analysis/payoff` | `code`, `scenarios=[-20,-10,-5,0,5,10,20]` (allowlist grid) | `{data_date, chart:[{scenarioPct, warrantPrice, returnPct}], breakeven}` |
| POST `/api/optimize` (M2) | `{budget, candidates:[code...], scenario_probs:{up:0.4,flat:0.3,down:0.3}, move_pct, max_weight}` | `{weights:[{code,w}], expected_return, risk, sharpe, frontier:[{ret,risk}...], assumptions:[...]}` |
| POST `/api/data/collect` | header `X-Collect-Token` (one-time token, config) | `{job: "accepted"}` then poll `/api/data/status` |
| GET `/api/data/status` | — | `{last_dates:{TSE:"YYYY-MM-DD",OTC:"..."}, missing:[...], collect_log:[...]}` |

Validation layer (`validation.py`) is the ONLY place that parses user input; routers call typed validators only (INV-10). SQLite access via parameterized statements only.

## 7. Frontend (Vite 8 + TS; framework pending D4)

Pages (Chinese UI): ① 搜尋與權證清單（FilterBar + WarrantTable，可排序、篩選即時生效 R5）② 單檔分析（ECharts: 損益情境圖、價格/IV 歷史折線）③ 配置最佳化（M2，權重長條圖 + 效率前緣散佈圖）④ 資料狀態（顯示 Data Date、缺漏警示 R4/R9）。Vite dev proxy `/api → http://127.0.0.1:8000`; production build served by FastAPI static. Visual: 簡潔自訂 (D5) — muted finance palette, no framework-default styling.

**User-adjustable defaults (D9)**: every filter condition (exercise ratio, IV, moneyness, days, issuer, type…) and every optimization scenario parameter (scenario probabilities, move %) ships with initial values but is fully adjustable in the UI; filter settings persist to `localStorage` across sessions (R5). No condition is ever hard-coded.

## 8. Milestones (work cards)

Each card cites PIM elements it implements. Acceptance per layer: UNIT (pytest/vitest with frozen fixtures), SIT (live-API integration + smoke), UAT (manual checklist §11).

### M0 — Data & screening (C1, C2, C3, C5; R1, R2, R4, R5, R7, R9; INV-1,2,4,5,6,7,8,10)

- Files: backend (db.py, config.py, validation.py, models.py, collectors/*, scheduler.py, routers/warrants.py, routers/data.py, main.py, run.py), scripts/migrate/0001.sql(+down), tests/collectors + fixtures, frontend scaffold (pages Search/WarrantList, FilterBar, WarrantTable), AGENTS.md.
- Contracts: §4 tables, §6 endpoints (warrants, underlying/search, data/status, health, collect).
- Error paths: per §4; upstream outage → FAILED log + status UI.
- Rollback: reverse migration 0001; delete `data/*.db` is NOT a rollback path (data loss) — migrations only.
- Test mapping: UNIT — collector parsers against frozen fixtures (TPEx JSON, TWSE CSV/JSON, G2 ladder variants), normalization asserts (G1 ratio ÷1000), validation layer cases; SIT — live collect for 2330 + 台積電 search, assert ≥50 warrants (CIM §7), data_date correct; UAT — §11 checklist items M0.
- Acceptance evidence: UNIT green; SIT log of one successful live collect (2330, counts per source, data_date = last trading day); UAT signed-off.

### M1 — Analysis & charts (C4; R3, R6, R9; INV-3, INV-9)

- Files: pricing/* (all), routers/analysis.py, routers/warrants.py (detail/history), frontend WarrantDetail page + charts, tests/pricing.
- Contracts: §5 formulas (exact), §6 analysis endpoints.
- Error paths: IV_FAILED status surfaced in table + detail (INV-3), never silent.
- Test mapping: UNIT — BS price/Greeks against textbook fixture (known S,K,T,r,σ → known price/delta; assert <1e-8); IV inverse round-trip (price → IV → price, err <1e-6); premium/leverage/breakeven hand-computed fixtures; SIT — 5 live warrants: Close IV within 1pp of 券商權證計算器 same-params values (user-provided reference, §11); UAT — §11 M1.
- Acceptance evidence: UNIT green; SIT comparison table (5 codes, our IV vs broker IV, Δpp ≤ 1); UAT signed-off.

### M2 — Allocation optimization (E1; R8)

- Files: optimizer.py, routers/optimize.py, frontend Optimize page, tests/optimizer.
- Contracts: §6 POST /api/optimize; model: expected return = Σ scenario_prob × scenario Return Rate (§5); risk = Σᵢ wᵢ·( |Δᵢ|·σ_underlying·Leverageᵢ ) (delta-scaled underlying vol, covariance off-diagonal = 0 documented as simplification); objective: max Sharpe under wᵢ ∈ [0, max_weight], Σw = 1 — solved `scipy.optimize.minimize` (SLSQP); frontier = sweep target return grid. **Every output includes `assumptions` list rendered in UI** (R8).
- Error paths: <2 valid candidates → 400 with message; solver non-convergence → 422 `OPTIMIZATION_FAILED` + suggestion.
- Test mapping: UNIT — weights sum to 1, bounds respected, single-candidate and zero-budget edge cases; SIT — live run with 5 candidates, frontier monotonic (ret↑ ⇒ risk↑); UAT — §11 M2.
- Acceptance evidence: UNIT green; SIT output dump; UAT signed-off.

## 9. Security implementation (implements PIM §6)

- Bind 127.0.0.1 only (uvicorn `--host 127.0.0.1`); no TLS (loopback only — recorded decision D6).
- INV-10 validation module as sole input parser; 4xx on violation (fail closed).
- `POST /api/data/collect` requires one-time `X-Collect-Token` from config (CSRF 型防護, PIM §6); all other endpoints GET/read-only (INV-7).
- Dependencies: pinned `requirements.txt` + `package-lock.json`; vet new packages (canonical name, maintenance, install script) before adding.
- Defender signals logged: collect job results (success/failed rows), validation rejections, token rejections — to `data/app.log`; UI surfaces job failures (R9).

## 10. Decision register (決策登記 — 使用者決策面)

| # | 決策 | 選擇 | 狀態 | 決策者/日期 | 中文理由 |
|---|---|---|---|---|---|
| D1 | 技術棧後端 | Python 3.12 + FastAPI | approved | user / 2026-08-08 | 你選擇：scipy 計算生態成熟；代價是第二條工具鏈 |
| D2 | 範圍 | M0+M1+M2 全做 | approved | user / 2026-08-08 | 你選擇一次到位，里程碑仍按序驗收 |
| D3 | 作業等級 | ops-relaxation: L0 嚴格 | approved | user / 2026-08-08 | 分支/PR、測試、文書照規則 |
| D4 | 前端框架 | 裸 Vite 8 + TypeScript（無框架） | approved | user / 2026-08-08 | 你選擇「照舊」：遵循既有裸 Vite + TS 慣例，依賴最少 |
| D5 | 視覺方向 | 簡潔自訂金融風 | approved | user / 2026-08-08 | 你選擇自訂、不用框架預設樣 |
| D6 | 介面語言/部署 | 繁中單一語言；僅本機 loopback，無 TLS | approved (impl) | agent / 2026-08-08 | 單人本機工具：i18n 與 TLS 為不必要負擔；若日後對外部署需重開 |
| D7 | 版本控制 | 文件流程替代（不安裝 git）；記降級宣告 | approved | user / 2026-08-08 | 初期環境未安裝 git，以每里程碑文件記錄 + data/ 備份替代分支/PR 紀律，其餘 L0 紀律不變；M0 完成後遷移至 git |
| D8 | G5 美式權證模型 | 統一 B-S（與官方一致），不實作二項樹 | approved (impl) | agent / 2026-08-08 | 與券商揭露一致可對照；深度價內美式誤差列已知限制（見 03 §G5）；若你日後要求再議 |
| D9 | 篩選/情境預設值 | 預設僅為初始值，全部可在 UI 微調並持久化（localStorage） | approved | user / 2026-08-08 | 你要求「以自己微調為主」：介面必須可改所有篩選標準與最佳化情境參數，無任何硬編碼 |

**降級宣告（degradation）**：① 版本控制降級（D7）：初期未安裝 git，以文件流程替代——每里程碑結束時於 docs/ 寫入變更記錄、備份 data/ 資料庫；其餘 L0 紀律（測試、驗收、決策登記）照常。M0 完成後已遷移至 git。② 本文件無 SKELETON 項目；唯一風險點 G2 已設三階橋接。

## 11. 手動 UAT 檢查表（第一里程碑 M0，中文）

1. 啟動後端（`py run.py`）與前端（`npm run dev`），`http://localhost:5173` 正常開啟。
2. 搜尋「2330」與「台積電」皆能列出標的；點入顯示權證清單，實測 ≥50 檔。
3. 權證清單欄位：行使比例（<1 的小數，如 0.05）、履約價、收盤價、資料日期——與 TWSE/TPEx 官方當日資料抽 5 檔逐筆核對一致。
4. 篩選「行使比例 ≥ 0.05」結果即時縮小；篩到 0 檔時有明確空態提示（R5）。
5. 資料狀態頁顯示各市場最近資料日期；人為斷網後按「立即更新」，出現失敗警示而非假資料（R9）。
6. 開啟前端 DevTools 網路面板：無失敗請求；所有請求回 200/400 語意正確。
7. （M1 追加）同參數下 5 檔權證 Close IV 與券商計算器誤差 ≤1pp。
8. （M2 追加）跑一組 5 檔候選：權重總和 = 1、各項約束滿足、假設列表完整顯示。
9. 篩選條件預設值可在介面微調（例如改成行使比例 ≥ 0.1、剩餘天數 10–365），重新整理頁面後設定仍在（D9）。

## 12. 開放問題（使用者需回答）

1. **資料回溯**：只從上線日起累積（建議），還是需要嘗試補抓上市權證歷史收盤（受官方 1 個月限制，補不到太多）？

## 13. Handoff

- 設計文件組：`01-cim.md`（概念）→ `02-pim.md`（語意契約）→ `03-verification.md`（驗證關卡，孤兒零、缺口 G1–G6 有橋接）→ 本文件（施工）。
- 實作開始條件：§12 開放問題回覆後，本文件即為唯一施工依據。
- 建議：實作開始前跑一次 phase-log checkpoint（workflow-checkpoint），將本設計階段存檔，方便跨會話續作。
