import type { Filters } from './filter-bar'

export interface SavedFilterPreset {
  id: string
  name: string
  filters: Filters
  saved_at: string
}

const STORAGE_KEY = 'wv-filter-presets'

export function loadPresets(): SavedFilterPreset[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr)) return []
    return arr.filter(
      (p) => p && typeof p.id === 'string' && typeof p.name === 'string' && p.filters && typeof p.filters === 'object',
    )
  } catch {
    return []
  }
}

function writePresets(list: SavedFilterPreset[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch {
    /* storage unavailable: presets just won't persist */
  }
}

export function savePreset(name: string, filters: Filters): SavedFilterPreset {
  const p: SavedFilterPreset = {
    id: Date.now().toString(36),
    name,
    filters: { ...filters },
    saved_at: new Date().toISOString(),
  }
  writePresets([...loadPresets(), p])
  return p
}

export function deletePreset(id: string): void {
  writePresets(loadPresets().filter((p) => p.id !== id))
}

export interface SavedFilterController {
  el: HTMLElement
  refresh(): void
}

export function createSavedFilterSelect(onApply: (f: Filters) => void): SavedFilterController {
  const wrap = document.createElement('div')
  wrap.className = 'saved-filters'

  const field = document.createElement('label')
  field.className = 'sf-field'
  const label = document.createElement('span')
  label.textContent = '已儲存條件'
  field.appendChild(label)
  wrap.appendChild(field)

  const dropdown = document.createElement('div')
  dropdown.className = 'sf-dropdown'
  const trigger = document.createElement('button')
  trigger.type = 'button'
  trigger.className = 'sf-trigger'
  trigger.textContent = '選擇已儲存條件…'
  dropdown.appendChild(trigger)
  const menu = document.createElement('ul')
  menu.className = 'sf-menu hidden'
  dropdown.appendChild(menu)
  wrap.appendChild(dropdown)

  function render(): void {
    menu.replaceChildren()
    const presets = loadPresets()
    for (const p of presets) {
      const li = document.createElement('li')
      li.className = 'sf-item'
      const name = document.createElement('span')
      name.className = 'sf-name'
      name.textContent = p.name
      name.title = p.name
      const del = document.createElement('button')
      del.type = 'button'
      del.className = 'sf-del'
      del.textContent = '×'
      del.title = '刪除此條件'
      del.addEventListener('click', (e) => {
        e.stopPropagation()
        deletePreset(p.id)
        render()
      })
      name.addEventListener('click', (e) => {
        e.stopPropagation()
        onApply(p.filters)
        trigger.textContent = '選擇已儲存條件…'
        menu.classList.add('hidden')
      })
      li.append(name, del)
      menu.appendChild(li)
    }
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation()
    menu.classList.toggle('hidden')
    if (!menu.classList.contains('hidden')) render()
  })

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target as Node)) menu.classList.add('hidden')
  })

  function refresh(): void {
    render()
  }

  render()
  return { el: wrap, refresh }
}
