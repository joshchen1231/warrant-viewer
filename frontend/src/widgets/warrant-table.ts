import { fmtDays, fmtNum, fmtPct, fmtRatio } from '../shared/format'
import type { RealtimeQuote, WarrantRow } from '../shared/types'

const realtimeByCode = new Map<string, RealtimeQuote>()

export interface SortState {
  key: string
  descending: boolean
}

export const SORTABLE_COLUMNS: Record<string, string> = {
  code: '代碼',
  close: '收盤價',
  exercise_ratio: '行使比例',
  iv_close: 'IV',
  moneyness: '價內',
  days_to_maturity: '剩餘天數',
  premium: '溢價',
  leverage: '槓桿',
}

interface Column {
  key: string
  title: string
  sortable: boolean
  align: 'left' | 'right'
  render: (r: WarrantRow) => string
}

const COLUMNS: Column[] = [
  { key: 'code', title: '代碼', sortable: true, align: 'left', render: (r) => r.code },
  { key: 'name', title: '名稱', sortable: false, align: 'left', render: (r) => r.name },
  { key: 'call_put', title: '認購/售', sortable: false, align: 'left', render: (r) => (r.call_put === 'CALL' ? '購' : '售') },
  { key: 'warrant_type', title: '類型', sortable: false, align: 'left', render: (r) => r.warrant_type },
  { key: 'issuer', title: '發行商', sortable: false, align: 'left', render: (r) => r.issuer || '—' },
  { key: 'close', title: '收盤價', sortable: true, align: 'right', render: (r) => fmtNum(r.close) },
  { key: '_rt_close', title: '即時價', sortable: false, align: 'right', render: (r) => fmtNum(realtimeByCode.get(r.code)?.close) },
  { key: '_rt_chg', title: '漲跌%', sortable: false, align: 'right', render: (r) => rtChg(r.code) },
  { key: 'underlying_close', title: '標的收盤', sortable: false, align: 'right', render: (r) => fmtNum(r.underlying_close) },
  { key: 'exercise_ratio', title: '行使比例', sortable: true, align: 'right', render: (r) => fmtRatio(r.exercise_ratio) },
  { key: 'strike_price', title: '履約價', sortable: false, align: 'right', render: (r) => fmtNum(r.strike_price) },
  { key: 'expiry_date', title: '到期日', sortable: false, align: 'right', render: (r) => r.expiry_date ?? '—' },
  { key: 'days_to_maturity', title: '剩餘天數', sortable: true, align: 'right', render: (r) => fmtDays(r.days_to_maturity) },
  { key: 'iv_close', title: 'IV', sortable: true, align: 'right', render: (r) => fmtPct(r.iv_close) },
  { key: 'delta', title: 'Delta', sortable: false, align: 'right', render: (r) => fmtNum(r.delta, 3) },
  { key: 'moneyness', title: '價內', sortable: true, align: 'right', render: (r) => fmtNum(r.moneyness, 3) },
  { key: 'premium', title: '溢價', sortable: true, align: 'right', render: (r) => fmtPct(r.premium) },
  { key: 'leverage', title: '槓桿', sortable: true, align: 'right', render: (r) => fmtNum(r.leverage, 1) },
  { key: 'theoretical_price', title: '理論價', sortable: false, align: 'right', render: (r) => fmtNum(r.theoretical_price) },
  { key: 'breakeven', title: '損益兩平', sortable: false, align: 'right', render: (r) => fmtNum(r.breakeven) },
]

function rtChg(code: string): string {
  const q = realtimeByCode.get(code)
  if (!q || q.close == null || q.prev_close == null || q.prev_close === 0) return '—'
  return fmtPct((q.close - q.prev_close) / q.prev_close)
}

function rtChgClass(code: string): string {
  const q = realtimeByCode.get(code)
  if (!q || q.close == null || q.prev_close == null) return ''
  if (q.close > q.prev_close) return ' rt-up'
  if (q.close < q.prev_close) return ' rt-down'
  return ' rt-flat'
}

export interface TableController {
  el: HTMLElement
  setRows(rows: WarrantRow[], sort: SortState): void
  setLoading(loading: boolean): void
  setError(message: string | null): void
  updateRealtime(quotes: RealtimeQuote[]): void
  setRealtimeStatus(note: string | null): void
}

export function createWarrantTable(onSort: (s: SortState) => void): TableController {
  const wrap = document.createElement('div')
  wrap.className = 'table-wrap'

  const meta = document.createElement('div')
  meta.className = 'table-meta'
  wrap.appendChild(meta)

  const table = document.createElement('table')
  table.className = 'warrant-table'
  const thead = document.createElement('thead')
  const headRow = document.createElement('tr')
  for (const col of COLUMNS) {
    const th = document.createElement('th')
    th.className = col.align === 'right' ? 'num' : ''
    if (col.sortable) {
      const btn = document.createElement('button')
      btn.type = 'button'
      btn.className = 'th-sort'
      btn.textContent = col.title
      btn.dataset.key = col.key
      btn.dataset.label = col.title
      th.appendChild(btn)
    } else {
      th.textContent = col.title
    }
    headRow.appendChild(th)
  }
  thead.appendChild(headRow)
  table.appendChild(thead)

  const tbody = document.createElement('tbody')
  table.appendChild(tbody)
  wrap.appendChild(table)

  thead.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest<HTMLButtonElement>('.th-sort')
    if (!btn) return
    const key = btn.dataset.key ?? ''
    onSort({ key, descending: false })
  })

  function markSort(sort: SortState): void {
    thead.querySelectorAll<HTMLButtonElement>('.th-sort').forEach((btn) => {
      const active = btn.dataset.key === sort.key
      btn.classList.toggle('active', active)
      btn.textContent = active && sort.descending ? `▼ ${btn.dataset.label ?? ''}` : `▲ ${btn.dataset.label ?? ''}`
    })
  }

  let statusNote: string | null = null

  function setMeta(): void {
    const base = tbody.childElementCount === 0 ? '無符合條件的權證，請調整篩選條件' : `共 ${tbody.childElementCount} 檔`
    meta.textContent = statusNote ? `${base}（${statusNote}）` : base
  }

  function setRows(rows: WarrantRow[], sort: SortState): void {
    markSort(sort)
    tbody.replaceChildren()
    for (const r of rows) {
      const tr = document.createElement('tr')
      tr.dataset.code = r.code
      for (const col of COLUMNS) {
        const td = document.createElement('td')
        td.className = col.align === 'right' ? 'num' : ''
        if (col.key === 'close' && r.close != null) {
          td.className += ' close'
        }
        if (col.key === '_rt_close') {
          td.className += ` rt${rtChgClass(r.code)}`
        }
        if (col.key === '_rt_chg') {
          td.className += ` rt${rtChgClass(r.code)}`
        }
        td.textContent = col.render(r)
        tr.appendChild(td)
      }
      tr.title = `${r.name}｜${r.code}｜${r.underlying_code} ${r.underlying_name}`
      tbody.appendChild(tr)
    }
    setMeta()
  }

  function updateRealtime(quotes: RealtimeQuote[]): void {
    const rtIdx = COLUMNS.findIndex((c) => c.key === '_rt_close')
    for (const q of quotes) {
      realtimeByCode.set(q.code, q)
      const tr = tbody.querySelector<HTMLTableRowElement>(`tr[data-code="${q.code}"]`)
      if (!tr) continue
      const tds = tr.querySelectorAll<HTMLTableCellElement>('td')
      const closeTd = tds[rtIdx]
      const chgTd = tds[rtIdx + 1]
      if (!closeTd || !chgTd) continue
      const cls = `num${rtChgClass(q.code)}`
      closeTd.textContent = fmtNum(q.close)
      closeTd.className = cls
      chgTd.textContent = rtChg(q.code)
      chgTd.className = cls
    }
  }

  function setRealtimeStatus(note: string | null): void {
    statusNote = note
    setMeta()
  }

  function setLoading(loading: boolean): void {
    if (loading) {
      meta.textContent = '載入中…'
      tbody.replaceChildren()
    }
  }

  function setError(message: string | null): void {
    meta.textContent = message ? `錯誤：${message}` : ''
    if (message) tbody.replaceChildren()
  }

  return { el: wrap, setRows, setLoading, setError, updateRealtime, setRealtimeStatus }
}
