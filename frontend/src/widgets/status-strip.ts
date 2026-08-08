import { dataStatus } from '../shared/api'
import type { CollectLogEntry, MarketStatus } from '../shared/types'

function marketChip(m: MarketStatus): HTMLElement {
  const chip = document.createElement('span')
  chip.className = `status-chip chip-${m.market.toLowerCase()}`
  chip.textContent = `${m.market} ${m.last_date ?? '—'}（${m.codes} 檔）`
  return chip
}

function logText(log: CollectLogEntry): string {
  return `${log.market} ${log.date} ${log.status}：${log.message}`
}

export function createStatusStrip(): HTMLElement {
  const root = document.createElement('div')
  root.className = 'status-strip'
  root.setAttribute('role', 'status')

  const refresh = document.createElement('button')
  refresh.type = 'button'
  refresh.className = 'status-refresh'
  refresh.textContent = '重新整理'

  async function load(): Promise<void> {
    root.replaceChildren(refresh)
    try {
      const s = await dataStatus()
      const line = document.createElement('div')
      line.className = 'status-line'
      const date = document.createElement('span')
      date.textContent = `資料日期：${s.data_date ?? '—'}`
      line.appendChild(date)
      for (const m of s.markets) line.appendChild(marketChip(m))
      root.appendChild(line)

      const recent = s.collect_log.slice(0, 2)
      if (recent.length > 0) {
        const logLine = document.createElement('div')
        logLine.className = 'status-log'
        logLine.textContent = recent.map(logText).join(' ｜ ')
        root.appendChild(logLine)
      }
    } catch (err) {
      const msg = document.createElement('span')
      msg.className = 'status-error'
      msg.textContent = `後端無法連線：${err instanceof Error ? err.message : String(err)}`
      root.appendChild(msg)
    }
  }

  refresh.addEventListener('click', () => { void load() })
  void load()
  return root
}
