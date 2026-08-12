import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// Só o subconjunto "latin" — cobre os acentos do português e evita baixar
// (ou, no build single-file, embutir em base64) glifos cirílicos/gregos/etc.
// que este app nunca usa.
import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-500.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import '@fontsource/plus-jakarta-sans/latin-600.css'
import '@fontsource/plus-jakarta-sans/latin-700.css'
import '@fontsource/plus-jakarta-sans/latin-800.css'

import './styles/tokens.css'
import './styles/global.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
