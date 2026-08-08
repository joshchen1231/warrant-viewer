# 權證檢視器 — 平台無關模型（PIM）＋語意契約

> 階層：PIM（平台無關模型）｜語言：雙語（概念與理由用中文；詞彙、INV、型別、狀態名用英文，下游文件與程式碼逐字引用）
> 日期：2026-08-08｜狀態：初版，待驗證關卡（03-verification.md）

## 1. 領域概念與關係

本工具的領域很單純，主體是一個以交易日為單位的「每日快照」體系：

```
Underlying Stock (標的股票) 1 ──< 連結 >── * Warrant (權證)
Warrant 1 ──< 每日收集 >── * DailyQuote (每日行情)
Underlying Stock 1 ──< 每日收集 >── * UnderlyingDaily (標的每日行情)
DailyQuote 1 ──< 由計算層衍生 >── 1 Analysis (分析結果)
DailyQuote + UnderlyingDaily ──< 使用 >── 計算層（IV、Greeks、溢價…）
```

- **權證是衍生品**：其價格由「標的股價、履約價、距到期日、無風險利率、波動率、行使比例」決定（Black-Scholes 家族模型，R3）。本工具絕不存「權證絕對合理價」這種單一真理，而是存「參數快照下的理論價」（R6）。
- **行使比例是關鍵的尺度因子**：權證報價與標的股價不同數量級，所有跨檔比較（溢價、槓桿、損益）都要先換算成「每單位權證對應的標的股數」再比（INV-2）。
- **資料日期（Data Date）是全域語意**：所有行情數字都屬於某個交易日。使用者看到任何數字都必須能反問「這是哪一天的？」（R4、R9）。
- **歷史是累積出來的**：上市權證收盤行情的官方來源只回溯一個月，本工具的歷史圖表能力靠每日收集自己累積（R7）。

## 2. 詞彙契約（Glossary）— 每個領域名詞只有一個名字、一個定義

程式碼識別字與下游文件逐字使用下表英文欄。中文欄為定義與介面顯示用。

| 英文名（識別字） | 中文 | 定義 |
|---|---|---|
| Warrant | 權證 | 發行券商發行、連結特定標的股票之短年期衍生性商品 |
| Underlying Stock | 標的股票 | 權證所連結之上市（TSE）或上櫃（OTC）股票 |
| Issuer | 發行券商 | 發行權證並負造市義務之券商 |
| Call / Put | 認購／認售 | 權證方向（看多／看空標的） |
| Exercise Style | 履約型態 | 美式（可提前履約）或歐式；另有上限型、下限型、重設型、牛熊證、展延型牛熊證等特殊型態，以 Warrant Type 區分 |
| Warrant Type | 權證類型 | 一般／上限型／下限型／重設型／牛熊證／展延型牛熊證 |
| Strike Price | 履約價 | 最新履約價（權證存續期間可能因除權息調整，故以「最新」為準） |
| Exercise Ratio | 行使比例 | 每 1 單位權證對應之標的股數（>0，INV-2）；跨來源單位不一致之正規化見 03-verification.md G1 |
| Listing Date | 上市日 | 權證開始在市場買賣之日 |
| Expiry Date | 到期日 | 權證生命終止日 |
| Last Trading Date | 最後交易日 | 市場上最後可買賣權證之日 |
| Time To Maturity | 距到期日 | 剩餘存續期間，計算用（年），由 Expiry Date 與 Data Date 推得 |
| Moneyness | 價內外程度 | 標的價對履約價的相對位置（認購：(S/K−1)；認售：(K/S−1)），正值＝價內 |
| Close IV | 收盤隱波 | 由權證收盤價以 Black-Scholes 反解之隱含波動率（本工具主語意，R3） |
| Bid IV / Ask IV | 委買／委賣隱波 | 造市商報價反解之隱波；本工具不自算，僅作官方對照（E2，未排入） |
| Historical Volatility | 歷史波動率 | 標的過去 N 個交易日之對數報酬年化標準差（預設 N=20） |
| Theoretical Price | 理論價 | 給定參數快照與波動率之 Black-Scholes 理論價格（每權證單位） |
| Premium | 溢價率 | 買權證相對直接持有標的之額外成本比例（公式見 PSM §計算層） |
| Leverage | 槓桿倍數 | 標的價格對（權證價／行使比例）之比值 |
| Break-even Price | 損益平衡價 | 到期時標的須達之價位使權證損益為零（認購：履約價＋權證價／行使比例） |
| Payoff | 到期損益 | 到期結算損益（認購：max(S−K,0)×比例−成本；認售對稱） |
| Return Rate | 收益率 | 情境模擬下之權證報酬率（情境＝標的變動幅度＋隱波不變假設） |
| Allocation | 資金配置 | 將預算分配於候選權證之權重向量 |
| Daily Snapshot | 每日快照 | 同一 Data Date 下之 WarrantMaster + DailyQuote + UnderlyingDaily + Analysis 全體 |
| Data Collection Job | 資料收集任務 | 每日盤後執行之收集作業（狀態機見 §4） |
| Data Date | 資料日期 | 行情數字所屬之交易日；全域可見、可追溯（R4、R9） |

## 3. 不變量（Invariants）— 任何實作都必須成立

- **INV-1** 每檔權證每交易日至多一筆 `DailyQuote`（主鍵：code + date）；同規則適用 `Analysis` 與 `UnderlyingDaily`。
- **INV-2** `Exercise Ratio` 必須 > 0（所有除法皆有定義）。
- **INV-3** IV 反解失敗（不收斂或超出可接受區間 [0, 5]）時存 `NULL` 並標記失敗狀態，不得塞入近似值。
- **INV-4** 金額一律以新台幣元（REAL）儲存；比率一律為無單位小數（0.05 表示 5%）；日期一律 ISO `YYYY-MM-DD`。
- **INV-5** `DailyQuote.underlyingClose` 若存在，必須與該標的當日 `UnderlyingDaily.close` 一致；無法核對時存 `NULL` 並標記。
- **INV-6** 歷史行情只追加不覆寫：收集任務對已存在之 (code, date) 記錄不得修改，只能先檢查再寫入新日期。
- **INV-7** 篩選與分析不改變資料庫；所有使用者輸入僅作為查詢參數。
- **INV-8** 收集任務以（date, market）為單位提交：單檔失敗不影響其他檔；當日失敗必須記載於 `CollectLog`；UI 必須顯示資料日期與缺口（R4、R9）。
- **INV-9** 每筆 `Analysis` 必須攜帶參數快照（無風險利率、模型名稱、計算日期），使結果可重現（R6）。
- **INV-10** 所有 API 參數一律經單一驗證層（型別／長度／格式／範圍白名單）；違反即拒絕，不執行查詢。

## 4. 狀態機（State Machines）

### 4.1 Data Collection Job（資料收集任務）

```
IDLE → RUNNING → SUCCESS
               → PARTIAL   （部分檔失敗，已記載）
               → FAILED    （整體失敗）
FAILED ──(重試，≤3 次)──→ RUNNING
任何終態 →（下一個交易日）→ IDLE
```

守衛（Guards）：進入 RUNNING 前檢查當日未重複提交（INV-1）；寫入時遵守 INV-6（append-only）；離開時寫 `CollectLog`（INV-8）。

### 4.2 Warrant Analysis（單檔分析產生）

```
REQUESTED → COMPUTED（帶 paramsSnapshot，INV-9）
          → ERROR    （IV 反解失敗等，INV-3）
```

## 5. 語意資料表（Schemas，僅語意層，實體格式見 PSM）

| 表 | 欄位（英文識別字） |
|---|---|
| WarrantMaster | code, name, market[TSE/OTC], underlyingCode, underlyingName, callPut, exerciseStyle, warrantType, issuer, strikePrice, exerciseRatio, listedDate, expiryDate, lastTradingDate, capPrice, floorPrice, reset, source, fetchedAt |
| DailyQuote | code, date, open, high, low, close, change, volume, tradeValue, underlyingClose, source |
| UnderlyingDaily | code, date, open, high, low, close, volume |
| Analysis | code, date, ivClose, delta, gamma, vega, theta, theoreticalPrice, premium, leverage, moneyness, hv20, breakeven, paramsSnapshot, status |
| CollectLog | date, market, status[SUCCESS/PARTIAL/FAILED], rowCount, message |

## 6. 敏感資料與資安（threat-model lite，本機單人規模，一段話）

資產：使用者本機資料庫與投資分析想法（低敏感性但不出本機）。未信任輸入進入點：①本機 HTTP API 參數 ②外部資料源回應（官方公開資料，半可信）③（未來）CSV 匯入。最壞合理濫用：本機瀏覽器被惡意網頁誘導呼叫 localhost API（CSRF 型）讀取資料或觸發重負載作業。防護方向：服務僅綁定本機回送位址、INV-10 單一驗證層、寫入型作業（資料更新）加一次性權杖。敏感欄位：無（全部為公開市場資料）。密鑰政策：不適用（無憑證）；依賴以固定版本清單管理。
