import { listWarrants, realtimeQuotes } from '../shared/api'
import type { UnderlyingResult, WarrantRow } from '../shared/types'
import { applyFilters, createFilterBar, loadSavedFilters, type Filters } from '../widgets/filter-bar'
import { createSavedFilterSelect } from '../widgets/saved-filters'
import { createSearchBox } from '../widgets/search-box'
import { createStatusStrip } from '../widgets/status-strip'
import { createWarrantTable, type SortState } from '../widgets/warrant-table'

const REALTIME_POLL_MS = 20_000

export function createSearchPage(): HTMLElement {
  const root = document.createElement('div')
  root.className = 'page'

  const header = document.createElement('header')
  header.className = 'topbar'
  const title = document.createElement('h1')
  title.textContent = '權證檢視器'
  const statusHost = document.createElement('div')
  statusHost.className = 'topbar-status'
  statusHost.appendChild(createStatusStrip())
  header.append(title, statusHost)
  root.appendChild(header)

  const main = document.createElement('main')
  main.className = 'main'

  let selected: UnderlyingResult | null = null
  let filters: Filters = loadSavedFilters()
  let sort: SortState = { key: filters.sort || 'code', descending: filters.descending }
  let realtimeTimer: number | undefined
  let realtimeSeq = 0

  const searchHost = document.createElement('section')
  searchHost.className = 'search-section'
  const searchHint = document.createElement('p')
  searchHint.className = 'search-hint'
  searchHint.textContent = '先選擇標的，再以右側條件篩選權證'
  searchHost.appendChild(searchHint)
  searchHost.appendChild(createSearchBox({ onSelect: (u) => selectUnderlying(u) }))
  main.appendChild(searchHost)

  const savedFilterCtrl = createSavedFilterSelect((f) => {
    filters = f
    sort = { key: f.sort || 'code', descending: f.descending }
    applyFilters(filterBarEl, f)
    void loadWarrants()
  })
  main.appendChild(savedFilterCtrl.el)

  const selectedBar = document.createElement('div')
  selectedBar.className = 'selected-bar hidden'
  main.appendChild(selectedBar)

  const filterHost = document.createElement('section')
  filterHost.className = 'filter-section hidden'
  const filterBarEl = createFilterBar((f) => {
    filters = f
    void loadWarrants()
  }, () => savedFilterCtrl.refresh())
  filterHost.appendChild(filterBarEl)
  main.appendChild(filterHost)

  const tableHost = document.createElement('section')
  tableHost.className = 'table-section hidden'
  const tableCtrl = createWarrantTable((s) => {
    if (s.key === sort.key) {
      sort = { key: s.key, descending: !sort.descending }
    } else {
      sort = s
    }
    void loadWarrants()
  })
  tableHost.appendChild(tableCtrl.el)
  main.appendChild(tableHost)
  root.appendChild(main)

  function selectUnderlying(u: UnderlyingResult): void {
    selected = u
    selectedBar.replaceChildren()
    const label = document.createElement('span')
    label.className = 'selected-label'
    label.textContent = `標的：${u.code} ${u.name}（${u.market}）`
    selectedBar.appendChild(label)
    selectedBar.classList.remove('hidden')
    filterHost.classList.remove('hidden')
    tableHost.classList.remove('hidden')
    void loadWarrants()
  }

  async function loadWarrants(): Promise<void> {
    if (!selected) return
    tableCtrl.setLoading(true)
    tableCtrl.setError(null)
    const params = new URLSearchParams()
    params.set('underlying_code', selected.code)
    if (filters.market) params.set('market', filters.market)
    if (filters.call_put) params.set('call_put', filters.call_put)
    if (filters.warrant_type) params.set('warrant_type', filters.warrant_type)
    if (filters.issuer) params.set('issuer', filters.issuer)
    if (filters.exercise_ratio_min) params.set('exercise_ratio_min', filters.exercise_ratio_min)
    if (filters.exercise_ratio_max) params.set('exercise_ratio_max', filters.exercise_ratio_max)
    if (filters.iv_min) params.set('iv_min', filters.iv_min)
    if (filters.iv_max) params.set('iv_max', filters.iv_max)
    if (filters.moneyness_min) params.set('moneyness_min', filters.moneyness_min)
    if (filters.moneyness_max) params.set('moneyness_max', filters.moneyness_max)
    if (filters.days_min) params.set('days_min', filters.days_min)
    if (filters.days_max) params.set('days_max', filters.days_max)
    params.set('sort', sort.key)
    if (sort.descending) params.set('descending', 'true')
    try {
      const res = await listWarrants(params)
      const rows: WarrantRow[] = res.rows
      tableCtrl.setRows(rows, sort)
      restartRealtime(rows)
    } catch (err) {
      stopRealtime()
      tableCtrl.setError(err instanceof Error ? err.message : String(err))
    }
  }

  function stopRealtime(): void {
    realtimeSeq++
    if (realtimeTimer !== undefined) {
      window.clearInterval(realtimeTimer)
      realtimeTimer = undefined
    }
    tableCtrl.setRealtimeStatus(null)
  }

  function restartRealtime(rows: WarrantRow[]): void {
    stopRealtime()
    if (rows.length === 0) return
    if (selected?.market === 'OTC') {
      tableCtrl.setRealtimeStatus('OTC 無即時報價')
      return
    }
    const seq = realtimeSeq
    async function poll(): Promise<void> {
      const codes = rows.map((r) => r.code)
      try {
        const res = await realtimeQuotes(codes)
        if (seq !== realtimeSeq) return
        tableCtrl.updateRealtime(res.rows)
        tableCtrl.setRealtimeStatus(null)
      } catch {
        if (seq === realtimeSeq) tableCtrl.setRealtimeStatus('即時報價連線失敗')
      }
    }
    void poll()
    realtimeTimer = window.setInterval(() => void poll(), REALTIME_POLL_MS)
  }

  return root
}
