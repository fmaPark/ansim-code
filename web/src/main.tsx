import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@seed-design/css/base.css'
import './styles.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
