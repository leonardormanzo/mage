import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// Build normal (`npm run build`) gera assets separados em dist/, prontos para
// hospedagem estática. Build single-file (`npm run build:singlefile`) gera um
// único index.html autocontido (CSS + JS inline), sem nenhuma chamada externa —
// pensado para abrir direto no navegador ou publicar como demo compartilhável.
const isSingleFile = process.env.VITE_SINGLEFILE === 'true'

export default defineConfig({
  base: './',
  plugins: [react(), ...(isSingleFile ? [viteSingleFile()] : [])],
  build: {
    outDir: isSingleFile ? 'dist-singlefile' : 'dist',
    assetsInlineLimit: isSingleFile ? Number.MAX_SAFE_INTEGER : 4096,
    cssCodeSplit: !isSingleFile,
  },
})
