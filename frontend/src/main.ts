import './style.css'
import { createSearchPage } from './pages/search'

const app = document.getElementById('app')
if (!app) throw new Error('missing #app element')
app.appendChild(createSearchPage())
