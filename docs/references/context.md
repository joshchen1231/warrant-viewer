# warrant-viewer — Project Context Glossary

> Persistent vocabulary for the 權證檢視器 project. English only.
> Sole source: docs/02-pim.md §2. Terms below are quoted verbatim in code and downstream docs.

## Domain glossary

| Term (identifier) | zh-TW display | Definition (one line) |
|---|---|---|
| Warrant | 權證 | Short-dated derivative issued by a broker, linked to one underlying stock |
| Underlying Stock | 標的股票 | Listed (TSE) or OTC-listed stock a warrant links to |
| Issuer | 發行券商 | Broker that issues a warrant and acts as liquidity provider |
| Call / Put | 認購／認售 | Warrant direction (bullish/bearish on underlying) |
| Exercise Style | 履約型態 | American (early exercise) vs European; special types via Warrant Type |
| Warrant Type | 權證類型 | General / upper-limit / lower-limit / reset / bull-bear (wcb) / extendable bull-bear (wxy) |
| Strike Price | 履約價 | Latest strike (adjusted over life for corporate actions) |
| Exercise Ratio | 行使比例 | Underlying shares per 1 warrant unit; > 0 (INV-2); normalized to per-unit (G1) |
| Listing Date | 上市日 | First trading day of the warrant |
| Expiry Date | 到期日 | End of warrant life |
| Last Trading Date | 最後交易日 | Last day warrant trades |
| Time To Maturity | 距到期日 | Remaining life in years (calendar/365) |
| Moneyness | 價內外程度 | (S/K − 1) for call; (K/S − 1) for put; positive = in-the-money |
| Close IV | 收盤隱波 | Implied volatility back-solved from warrant close price (B-S), primary IV semantic (R3) |
| Bid IV / Ask IV | 委買／委賣隱波 | IV of liquidity-provider quotes; not computed by this tool (extension E2 only) |
| Historical Volatility | 歷史波動率 | Annualized stdev of underlying log returns over N=20 days |
| Theoretical Price | 理論價 | B-S theoretical price per warrant unit at Close IV (paramsSnapshot, INV-9) |
| Premium | 溢價率 | Extra cost of the warrant vs direct underlying holding; call (K−S+Pw/R)/S |
| Leverage | 槓桿倍數 | S / (Pw/R) |
| Break-even Price | 損益平衡價 | Underlying price at expiry for zero warrant P&L; call K + Pw/R |
| Payoff | 到期損益 | Expiry settlement P&L; call max(S−K,0)·R − Pw |
| Return Rate | 收益率 | Warrant return under a scenario (underlying move ±x%, IV held constant) |
| Allocation | 資金配置 | Weight vector distributing budget over candidate warrants |
| Daily Snapshot | 每日快照 | All rows for one Data Date across WarrantMaster/DailyQuote/UnderlyingDaily/Analysis |
| Data Collection Job | 資料收集任務 | Daily post-close collection run (state machine, PIM §4.1) |
| Data Date | 資料日期 | Trading day a quote belongs to; globally visible (R4, R9) |

## Platform identifiers (from 03-verification.md gap register)

- G1: Exercise Ratio normalization — TWSE reports per-1000-units (`最新標的履約配發數量(每仟單位權證)`); divide by 1000 to per-unit.
- G2: TWSE listed-warrant daily close has no published JSON endpoint; ladder: reverse-engineer `data-api=/stock/warrantStock` → CSV download → mis.twse.com.tw fallback.
- G3: Official IV (disclosure platform) = random-sampled liquidity-provider quotes; never mixed into Close IV column.
- G4: Risk-free rate = Taiwan Bank 1-year deposit, manually maintained in config.
- G5: B-S model used uniformly (matches official practice); deep-ITM American warrants carry known valuation limitation.
- G6: WarrantMaster = latest-disclosure upsert; DailyQuote = append-only; never conflate.

## Ops facts

- ops-relaxation: L0 (approved 2026-08-08)
- Python must be invoked via `py` (bare `python` is a Store stub on this machine).
- Vite dev server fixed at localhost:5173 strictPort.
- git NOT installed on this machine; D7 resolved 2026-08-08: document-based workflow substitute + degradation declaration (docs/04-psm.md §10).
