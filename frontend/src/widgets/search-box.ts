import { searchUnderlying } from '../shared/api'
import type { UnderlyingResult } from '../shared/types'

export interface SearchBoxOptions {
  onSelect: (u: UnderlyingResult) => void
}

export function createSearchBox(opts: SearchBoxOptions): HTMLElement {
  const root = document.createElement('div')
  root.className = 'search-box'

  const input = document.createElement('input')
  input.type = 'search'
  input.className = 'search-input'
  input.placeholder = '輸入標的代碼或名稱（如 2330、台積電）'
  root.appendChild(input)

  const results = document.createElement('ul')
  results.className = 'search-results hidden'
  root.appendChild(results)

  let timer: number | undefined

  async function run(q: string): Promise<void> {
    if (!q.trim()) {
      results.classList.add('hidden')
      results.replaceChildren()
      return
    }
    try {
      const list = await searchUnderlying(q.trim())
      results.replaceChildren()
      for (const u of list) {
        const li = document.createElement('li')
        li.textContent = `${u.code} ${u.name}（${u.market}）`
        li.addEventListener('click', () => {
          input.value = `${u.code} ${u.name}`
          results.classList.add('hidden')
          opts.onSelect(u)
        })
        results.appendChild(li)
      }
      results.classList.toggle('hidden', list.length === 0)
    } catch {
      results.replaceChildren()
      results.classList.add('hidden')
    }
  }

  input.addEventListener('input', () => {
    window.clearTimeout(timer)
    timer = window.setTimeout(() => { void run(input.value) }, 300)
  })
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      window.clearTimeout(timer)
      void run(input.value)
    } else if (e.key === 'Escape') {
      results.classList.add('hidden')
    }
  })
  return root
}
