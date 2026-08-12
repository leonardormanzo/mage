import sharp from 'sharp'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const dir = path.dirname(fileURLToPath(import.meta.url))
const publicDir = path.join(dir, '..', 'public')

const anySvg = readFileSync(path.join(dir, 'icon-source.svg'))
const maskableSvg = readFileSync(path.join(dir, 'icon-source-maskable.svg'))

async function render(svgBuffer, size, outFile) {
  await sharp(svgBuffer).resize(size, size).png().toFile(path.join(publicDir, outFile))
  console.log('wrote', outFile)
}

await render(anySvg, 192, 'pwa-192.png')
await render(anySvg, 512, 'pwa-512.png')
await render(maskableSvg, 512, 'pwa-maskable-512.png')
await render(anySvg, 180, 'apple-touch-icon.png')
await render(anySvg, 32, 'favicon-32.png')
