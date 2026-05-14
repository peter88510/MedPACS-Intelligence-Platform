import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initCornerstone } from './cornerstone/setup.ts'

async function bootstrap() {
  await initCornerstone()
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

bootstrap().catch((err) => {
  console.error('[bootstrap] failed to initialize application:', err)
})
