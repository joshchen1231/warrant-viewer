export interface UnderlyingResult {
  code: string
  name: string
  market: string
}

export interface WarrantRow {
  code: string
  name: string
  market: string
  underlying_code: string
  underlying_name: string
  call_put: string
  exercise_style: string
  warrant_type: string
  issuer: string
  strike_price: number | null
  exercise_ratio: number | null
  expiry_date: string | null
  last_trading_date: string | null
  cap_price: number | null
  floor_price: number | null
  reset: number
  active: number
  quote_date: string | null
  close: number | null
  underlying_close: number | null
  iv_close: number | null
  delta: number | null
  moneyness: number | null
  premium: number | null
  leverage: number | null
  theoretical_price: number | null
  breakeven: number | null
  days_to_maturity: number | null
  analysis_status: string | null
}

export interface WarrantListResponse {
  count: number
  rows: WarrantRow[]
}

export interface RealtimeQuote {
  code: string
  name: string
  date: string
  ts: string
  close: number | null
  prev_close: number | null
  volume: number | null
  bid: number | null
  ask: number | null
}

export interface RealtimeResponse {
  fetched_at: string
  count: number
  rows: RealtimeQuote[]
}

export interface MarketStatus {
  market: string
  last_date: string | null
  codes: number
}

export interface CollectLogEntry {
  date: string
  market: string
  status: string
  row_count: number
  message: string
}

export interface DataStatus {
  data_date: string | null
  markets: MarketStatus[]
  collect_log: CollectLogEntry[]
}
