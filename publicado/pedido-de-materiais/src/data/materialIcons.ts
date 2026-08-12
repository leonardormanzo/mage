import {
  Truck,
  PackagePlus,
  Package,
  Component,
  Layers3,
  Droplet,
  Umbrella,
  BrickWall,
  Wrench,
  Ribbon,
  Container,
  Box,
  Zap,
  Plug,
  Cable,
  Droplets,
  Grid3x3,
  Wallpaper,
  Frame,
  PaintBucket,
  PaintRoller,
  Brush,
  Square,
  Lightbulb,
  Lamp,
  ShowerHead,
  Bath,
  Toilet,
  DoorClosed,
  KeyRound,
  Hammer,
  Trash2,
  Shield,
  Sparkles,
  type LucideIcon,
} from 'lucide-react'

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
}

/** [palavras-chave (já normalizadas), ícone] — a primeira combinação vence. */
const MATERIAL_KEYWORD_ICONS: ReadonlyArray<readonly [string[], LucideIcon]> = [
  [['concreto usinado'], Truck],
  [['cimento', 'argamassa', 'nivelador'], PackagePlus],
  [['areia', 'brita'], Package],
  [['lona de protecao', 'papelao', 'placa de gesso', 'manta acustica'], Layers3],
  [['imperme'], Umbrella],
  [['bloco', 'tijolo', 'canaleta'], BrickWall],
  [['perfil metalico', 'espacador'], Component],
  [['massa para drywall'], PaintBucket],
  [['adesivo'], Droplet],
  [['fita'], Ribbon],
  [['caixa-d'], Container],
  [['caixa'], Box],
  [['disjuntor', 'quadro de distribuicao'], Zap],
  [['tomada', 'interruptor'], Plug],
  [['eletroduto', 'cabo eletrico'], Cable],
  [['tubo', 'joelho', 'luva pvc', 'te pvc', 'registro', 'valvula'], Droplets],
  [['ceramico', 'porcelanato', 'vinilico', 'rejunte'], Grid3x3],
  [['revestimento de parede'], Wallpaper],
  [['rodape', 'espelho'], Frame],
  [['massa corrida', 'massa acrilica', 'fundo preparador', 'selador', 'lixa'], PaintBucket],
  [['tinta', 'esmalte'], PaintBucket],
  [['rolo de pintura'], PaintRoller],
  [['pincel'], Brush],
  [['bandeja'], Square],
  [['lampada'], Lightbulb],
  [['luminaria'], Lamp],
  [['torneira'], Droplets],
  [['chuveiro'], ShowerHead],
  [['cuba'], Bath],
  [['vaso sanitario', 'assento sanitario'], Toilet],
  [['porta'], DoorClosed],
  [['fechadura', 'macaneta'], KeyRound],
  [['acessorio de banheiro'], Bath],
  [['disco de corte', 'ponteiro', 'talhadeira', 'marreta'], Hammer],
  [['saco para entulho'], Trash2],
  [['cacamba'], Container],
]

const CATEGORY_KEYWORD_ICONS: ReadonlyArray<readonly [string[], LucideIcon]> = [
  [['retirada e descarte'], Trash2],
  [['protecao'], Shield],
  [['ferramentas'], Wrench],
  [['blocos'], BrickWall],
  [['drywall'], Layers3],
  [['argamassas'], PackagePlus],
  [['impermeabilizacao'], Umbrella],
  [['eletrica'], Zap],
  [['hidraulica'], Droplets],
  [['pisos'], Grid3x3],
  [['paredes'], Wallpaper],
  [['assentamento'], PackagePlus],
  [['preparacao'], PaintBucket],
  [['pintura'], PaintRoller],
  [['iluminacao'], Lightbulb],
  [['metais'], Droplets],
  [['loucas'], Bath],
  [['portas e ferragens'], DoorClosed],
  [['acessorios'], Sparkles],
]

export function getMaterialIcon(materialName: string, categoryName?: string, fallback?: LucideIcon): LucideIcon {
  const normalizedName = normalize(materialName)
  for (const [keywords, icon] of MATERIAL_KEYWORD_ICONS) {
    if (keywords.some((keyword) => normalizedName.includes(keyword))) return icon
  }
  if (categoryName) {
    const icon = getCategoryIcon(categoryName)
    if (icon) return icon
  }
  return fallback ?? Package
}

export function getCategoryIcon(categoryName: string): LucideIcon | undefined {
  const normalizedCategory = normalize(categoryName)
  for (const [keywords, icon] of CATEGORY_KEYWORD_ICONS) {
    if (keywords.some((keyword) => normalizedCategory.includes(keyword))) return icon
  }
  return undefined
}
