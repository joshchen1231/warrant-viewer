import { savePreset } from './saved-filters'

export interface Filters {
  market: string
  call_put: string
  warrant_type: string
  issuer: string
  exercise_ratio_min: string
  exercise_ratio_max: string
  iv_min: string
  iv_max: string
  moneyness_min: string
  moneyness_max: string
  days_min: string
  days_max: string
  sort: string
  descending: boolean
}

export const SORT_OPTIONS: Array<[string, string]> = [
  ['code', '代碼'],
  ['close', '收盤價'],
  ['exercise_ratio', '行使比例'],
  ['iv_close', '隱含波動率'],
  ['moneyness', '價內程度'],
  ['days_to_maturity', '剩餘天數'],
  ['premium', '溢價'],
  ['leverage', '槓桿'],
]

export function defaultFilters(): Filters {
  return {
    market: '',
    call_put: '',
    warrant_type: '',
    issuer: '',
    exercise_ratio_min: '',
    exercise_ratio_max: '',
    iv_min: '',
    iv_max: '',
    moneyness_min: '',
    moneyness_max: '',
    days_min: '',
    days_max: '',
    sort: 'code',
    descending: false,
  }
}

export function loadSavedFilters(): Filters {
  return loadSaved()
}

export function saveFiltersToStorage(f: Filters): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(f))
  } catch {
    /* ignore */
  }
}

export function applyFilters(root: HTMLElement, f: Filters): void {
  applyToControls(root, f)
  saveFiltersToStorage(f)
}

const STORAGE_KEY = 'wv-filters'

function readFilters(root: HTMLElement): Filters {
  const f = defaultFilters()
  const strF = f as unknown as Record<string, string>
  for (const key of Object.keys(strF)) {
    const el = root.querySelector<HTMLInputElement | HTMLSelectElement>(`[data-f="${key}"]`)
    if (!el) continue
    if (key === 'descending') {
      f.descending = (el as HTMLInputElement).checked
    } else {
      strF[key] = el.value
    }
  }
  return f
}

function loadSaved(): Filters {
  const f = defaultFilters()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return f
    const saved = JSON.parse(raw) as Partial<Filters>
    for (const key of Object.keys(f)) {
      const v = saved[key as keyof Filters]
      if (v !== undefined && v !== null && v !== '') (f as unknown as Record<string, unknown>)[key] = v
    }
  } catch {
    /* corrupted storage: fall back to defaults */
  }
  return f
}

function applyToControls(root: HTMLElement, f: Filters): void {
  root.querySelectorAll<HTMLSelectElement | HTMLInputElement>('[data-f]').forEach((el) => {
    const key = el.dataset.f
    if (!key) return
    if (key === 'descending') {
      ;(el as HTMLInputElement).checked = (f as unknown as Record<string, boolean>)[key]
    } else {
      el.value = (f as unknown as Record<string, string>)[key] ?? ''
    }
  })
}

function labeled(label: string, control: HTMLElement): HTMLElement {
  const wrap = document.createElement('label')
  wrap.className = 'fb-field'
  const span = document.createElement('span')
  span.textContent = label
  wrap.append(span, control)
  return wrap
}

function select(name: string, options: Array<[string, string]>, value: string): HTMLSelectElement {
  const el = document.createElement('select')
  el.dataset.f = name
  for (const [v, text] of options) {
    const opt = document.createElement('option')
    opt.value = v
    opt.textContent = text
    el.appendChild(opt)
  }
  el.value = value
  return el
}

function numberInput(name: string, placeholder: string): HTMLInputElement {
  const el = document.createElement('input')
  el.type = 'number'
  el.step = 'any'
  el.min = '0'
  el.placeholder = placeholder
  el.dataset.f = name
  return el
}

export function createFilterBar(
  onChange: (f: Filters) => void,
  onSaved?: () => void,
): HTMLElement {
  const root = document.createElement('div')
  root.className = 'filter-bar'
  const f = loadSaved()

  root.appendChild(labeled('市場', select('market', [['', '全部'], ['TSE', '上市'], ['OTC', '上櫃']], f.market)))
  root.appendChild(labeled('認購/售', select('call_put', [['', '全部'], ['CALL', '認購'], ['PUT', '認售']], f.call_put)))
  root.appendChild(labeled('類型', select('warrant_type', [
    ['', '全部'], ['GENERAL', '一般'], ['LIMIT', '上限型'], ['RESET', '重設型'], ['BULLBEAR', '牛熊證'],
  ], f.warrant_type)))
  root.appendChild(labeled('發行商', (() => {
    const el = document.createElement('input')
    el.type = 'text'
    el.maxLength = 30
    el.dataset.f = 'issuer'
    el.placeholder = '關鍵字'
    return el
  })()))

  root.appendChild(labeled('行使比例 ≥', numberInput('exercise_ratio_min', '0.02')))
  root.appendChild(labeled('行使比例 ≤', numberInput('exercise_ratio_max', '1.00')))
  root.appendChild(labeled('IV ≥', numberInput('iv_min', '0.10')))
  root.appendChild(labeled('IV ≤', numberInput('iv_max', '3.00')))
  root.appendChild(labeled('價內 ≥', numberInput('moneyness_min', '0.80')))
  root.appendChild(labeled('價內 ≤', numberInput('moneyness_max', '1.20')))
  root.appendChild(labeled('剩餘天數 ≥', numberInput('days_min', '30')))
  root.appendChild(labeled('剩餘天數 ≤', numberInput('days_max', '365')))

  root.appendChild(labeled('排序', select('sort', SORT_OPTIONS, f.sort)))

  const descLabel = document.createElement('label')
  descLabel.className = 'fb-field fb-desc'
  const descSpan = document.createElement('span')
  descSpan.textContent = '遞減'
  const desc = document.createElement('input')
  desc.type = 'checkbox'
  desc.dataset.f = 'descending'
  descLabel.append(descSpan, desc)
  root.appendChild(descLabel)

  const reset = document.createElement('button')
  reset.type = 'button'
  reset.className = 'fb-reset'
  reset.textContent = '重設'
  root.appendChild(reset)

  const save = document.createElement('button')
  save.type = 'button'
  save.className = 'fb-save'
  save.textContent = '儲存條件'
  save.addEventListener('click', () => {
    const name = window.prompt('為目前的條件命名', new Date().toISOString().slice(0, 10))
    if (name === null) return
    const trimmed = name.trim()
    if (!trimmed) return
    savePreset(trimmed, readFilters(root))
    onSaved?.()
  })
  root.appendChild(save)

  const emit = (): void => {
    const next = readFilters(root)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch {
      /* storage unavailable: filters just won't persist */
    }
    onChange(next)
  }

  root.addEventListener('change', emit)
  reset.addEventListener('click', () => {
    root.querySelectorAll<HTMLSelectElement | HTMLInputElement>('[data-f]').forEach((el) => {
      if (el.dataset.f === 'descending') {
        ;(el as HTMLInputElement).checked = false
      } else {
        el.value = ''
      }
    })
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
    emit()
  })
  applyToControls(root, f)
  return root
}
