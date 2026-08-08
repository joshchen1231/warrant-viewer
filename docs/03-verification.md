# 權證檢視器 — 驗證關卡（Verification Gate）

> 階層：Verification（PIM 與 PSM 之間的硬關卡）｜語言：中文敘述，ID 用英文
> 日期：2026-08-08｜狀態：初版。依作業規則，作者（本次會話）不應為唯一驗證者——進入 PSM 前建議由未參與 PIM 寫作之審查者複查本矩陣

## 1. 可追溯矩陣（Traceability Matrix）

### 1.1 業務規則 → PIM 對應（CIM → PIM）

| CIM 業務規則 | PIM 對應 | 缺口 |
|---|---|---|
| R1 雙市場涵蓋＋依標的搜尋 | Glossary: Underlying Stock, Warrant, Market 概念；WarrantMaster.market / underlyingCode / underlyingName | 無（實作見 PSM M0） |
| R2 基本條件以官方揭露為準 | WarrantMaster.source / fetchedAt；Glossary: Strike Price（「最新」語意） | 部分——兩市場官方來源欄位口徑不同，正規化見 G1 |
| R3 IV 以 B-S 反解＋台銀定存利率 | Glossary: Close IV；Analysis.ivClose；INV-3, INV-9 | 無（方法與官方一致，已查證） |
| R4 每日收集＋資料日期可見 | Data Collection Job 狀態機；Data Date 概念；CollectLog；INV-8 | 無 |
| R5 篩選只縮小不竄改 | INV-7；查詢參數契約（PSM） | 無 |
| R6 數字可解釋 | INV-9（paramsSnapshot）；Analysis 全欄位 | 無 |
| R7 歷史只累積不覆寫 | INV-6；DailyQuote append-only | 無 |
| R8 配置建議附假設與限制 | Glossary: Allocation；M2 輸出規格（PSM） | 無（輸出契約待 PSM 定義） |
| R9 失敗明顯標示 | INV-8；CollectLog；資料新鮮度介面（PSM） | 無 |

### 1.2 PIM 元素 → 業務規則（反向，孤兒檢查）

| PIM 元素 | 回指 CIM |
|---|---|
| Glossary 全部詞彙 | R1/R2/R3/R5/R6/R8 |
| INV-1 | R4（每日一筆） |
| INV-2 | R2（行使比例正確性） |
| INV-3 | R3/R6 |
| INV-4 | R2/R7（儲存一致性） |
| INV-5 | R4/R9（資料可信度） |
| INV-6 | R7 |
| INV-7 | R5 |
| INV-8 | R4/R9 |
| INV-9 | R6 |
| INV-10 | R5（輸入防護，間接） |
| Data Collection Job 狀態機 | R4/R9 |
| Warrant Analysis 狀態機 | R6 |
| 五張語意資料表 | R1–R9 全體（承載面） |

**孤兒（Orphan）檢查結果**：雙向皆無孤兒。✔ 可進入 PSM。

## 2. 語意缺口登錄（Semantic Gap Register）

| 編號 | PIM 語意 | 缺口描述 | 橋接策略（Bridge） | 是否扭曲語意 |
|---|---|---|---|---|
| G1 | Exercise Ratio（每 1 單位權證對應股數） | 兩官方來源單位不同：TPEx 為每單位；TWSE 彙總表為「每仟單位權證配發數量」 | 收集層統一除以 1000 正規化為單一語意再入庫；來源記於 `source` | 否（純單位換算） |
| G2 | DailyQuote（上市權證每日收盤行情） | 上市收盤行情無已公開 JSON 端點（頁面 `data-api=/stock/warrantStock` 存在但直接呼叫 404，需逆向正確參數）；官方 CSV 下載僅回溯一個月 | M0 優先逆向 `warrantStock`；失敗則每日下載彙總表 CSV 累積；再失敗以 mis.twse.com.tw 為備援（2018 年開源專案 WarrantsStrategy 已驗證該源可行）。多源時以 `source` 區分 | 無（自建累積正好滿足 R7）|
| G3 | Close IV 語意 | 官方「權證資訊揭露平台」的隱波是「隨機取樣造市商報價」反解，與本工具「收盤價反解」不同語意 | 本工具以自行反解之 Close IV 為唯一主語意（與券商計算器同方法）；官方 BIV/SIV 僅屬 E2 延伸，永不混入同一欄位 | 否（兩種語意明確分名） |
| G4 | 無風險利率（台銀一年期定存） | 無官方開放 API | 設定檔手動維護＋預設值；每次計算寫入 paramsSnapshot（INV-9） | 可接受（利率敏感度低且可重現） |
| G5 | 美式權證提前履約 | Black-Scholes 為歐式模型；台股權證含美式與特殊型態 | 與官方揭露一致：統一用 B-S（已查證官方即此做法）；權證型態欄位保留供使用者自行留意。深度價內美式權證之理論價誤差列為已知限制（研究性註記，不做二項樹——見 PSM 決策登記） | 部分（已知限制，明文標記，不改語意） |
| G6 | Data Date 與「最新」語意 | 權證基本資料（如履約價）在存續期間會調整，官方更新時點為前一營業日申報 | WarrantMaster 以「最新揭露」為準（upsert），行情以日期追加（INV-6）；兩者語意不同，實作不得混用 | 否（語意分離寫入 PSM） |

## 3. 驗證結論

- 可追溯性：✔ 無孤兒。
- 缺口：G1–G6 均有橋接策略且無不可接受之扭曲；G2 為唯一的實作風險點，M0 需以「端點逆向 → CSV → mis 備援」順序實作並以 `source` 標記。
- 建議：進入 PSM 前由獨立審查者複查本文件（作者 ≠ 驗證者規則）。
