import { Hammer, BrickWall, Zap, Grid3x3, PaintRoller, Sparkles } from 'lucide-react'
import type { Category, MaterialDef, Phase, Unit } from '../types/models'

function slugify(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-+|-+$)/g, '')
}

/** Unidades medidas/contínuas aceitam casas decimais; unidades contáveis não. */
const DECIMAL_UNITS = new Set<Unit>(['m²', 'm³', 'metro', 'kg'])

export function unitAllowsDecimal(unit: Unit): boolean {
  return DECIMAL_UNITS.has(unit)
}

interface PhaseSeed {
  id: string
  name: string
  icon: Phase['icon']
  color: string
  categories: readonly string[]
  materials: ReadonlyArray<readonly [name: string, unit: Unit, category: string]>
}

/**
 * Catálogo focado em reforma de apartamento (unidade dentro de um prédio já
 * pronto) — por isso não há fases de fundação, estrutura ou cobertura, que
 * são intervenções no prédio, não na unidade.
 */
const PHASE_SEEDS: readonly PhaseSeed[] = [
  {
    id: 'demolicao',
    name: 'Demolição',
    icon: Hammer,
    color: 'var(--phase-demolicao)',
    categories: ['Retirada e descarte', 'Proteção', 'Ferramentas e consumíveis'],
    materials: [
      ['Saco para entulho', 'unidade', 'Retirada e descarte'],
      ['Caçamba', 'unidade', 'Retirada e descarte'],
      ['Lona de proteção', 'm²', 'Proteção'],
      ['Papelão para proteção de piso', 'm²', 'Proteção'],
      ['Fita crepe', 'rolo', 'Proteção'],
      ['Disco de corte', 'unidade', 'Ferramentas e consumíveis'],
      ['Ponteiro', 'unidade', 'Ferramentas e consumíveis'],
      ['Talhadeira', 'unidade', 'Ferramentas e consumíveis'],
      ['Marreta', 'unidade', 'Ferramentas e consumíveis'],
    ],
  },
  {
    id: 'alvenaria',
    name: 'Alvenaria',
    icon: BrickWall,
    color: 'var(--phase-alvenaria)',
    categories: ['Blocos', 'Drywall', 'Argamassas'],
    materials: [
      ['Bloco cerâmico', 'unidade', 'Blocos'],
      ['Bloco de concreto', 'unidade', 'Blocos'],
      ['Canaleta', 'unidade', 'Blocos'],
      ['Placa de gesso acartonado', 'unidade', 'Drywall'],
      ['Perfil metálico para drywall', 'metro', 'Drywall'],
      ['Massa para drywall', 'saco', 'Drywall'],
      ['Fita para drywall', 'rolo', 'Drywall'],
      ['Cimento', 'saco', 'Argamassas'],
      ['Areia média', 'm³', 'Argamassas'],
      ['Argamassa de assentamento', 'saco', 'Argamassas'],
      ['Espuma expansiva', 'lata', 'Argamassas'],
    ],
  },
  {
    id: 'instalacoes',
    name: 'Instalações',
    icon: Zap,
    color: 'var(--phase-instalacoes)',
    categories: ['Elétrica', 'Hidráulica'],
    materials: [
      ['Eletroduto corrugado', 'rolo', 'Elétrica'],
      ['Cabo elétrico', 'metro', 'Elétrica'],
      ['Caixa 4×2', 'unidade', 'Elétrica'],
      ['Caixa de passagem', 'unidade', 'Elétrica'],
      ['Disjuntor', 'unidade', 'Elétrica'],
      ['Quadro de distribuição', 'unidade', 'Elétrica'],
      ['Tomada', 'unidade', 'Elétrica'],
      ['Interruptor', 'unidade', 'Elétrica'],
      ['Fita isolante', 'rolo', 'Elétrica'],
      ['Tubo PVC', 'barra', 'Hidráulica'],
      ['Joelho PVC', 'unidade', 'Hidráulica'],
      ['Tê PVC', 'unidade', 'Hidráulica'],
      ['Luva PVC', 'unidade', 'Hidráulica'],
      ['Registro', 'unidade', 'Hidráulica'],
      ['Válvula', 'unidade', 'Hidráulica'],
      ['Adesivo para PVC', 'tubo', 'Hidráulica'],
      ['Fita veda-rosca', 'rolo', 'Hidráulica'],
      ['Caixa-d’água', 'unidade', 'Hidráulica'],
    ],
  },
  {
    id: 'revestimentos',
    name: 'Revestimentos',
    icon: Grid3x3,
    color: 'var(--phase-revestimentos)',
    categories: ['Pisos', 'Paredes', 'Assentamento', 'Impermeabilização'],
    materials: [
      ['Piso cerâmico', 'm²', 'Pisos'],
      ['Porcelanato', 'm²', 'Pisos'],
      ['Piso vinílico', 'm²', 'Pisos'],
      ['Manta acústica', 'm²', 'Pisos'],
      ['Nivelador de piso', 'pacote', 'Pisos'],
      ['Revestimento de parede', 'm²', 'Paredes'],
      ['Rodapé', 'metro', 'Paredes'],
      ['Argamassa colante', 'saco', 'Assentamento'],
      ['Rejunte', 'pacote', 'Assentamento'],
      ['Espaçador', 'pacote', 'Assentamento'],
      ['Manta impermeabilizante', 'rolo', 'Impermeabilização'],
      ['Impermeabilizante', 'lata', 'Impermeabilização'],
    ],
  },
  {
    id: 'pintura',
    name: 'Pintura',
    icon: PaintRoller,
    color: 'var(--phase-pintura)',
    categories: ['Preparação', 'Pintura', 'Proteção e ferramentas'],
    materials: [
      ['Massa corrida', 'lata', 'Preparação'],
      ['Massa acrílica', 'lata', 'Preparação'],
      ['Fundo preparador', 'lata', 'Preparação'],
      ['Selador', 'lata', 'Preparação'],
      ['Lixa', 'unidade', 'Preparação'],
      ['Tinta acrílica', 'lata', 'Pintura'],
      ['Esmalte', 'lata', 'Pintura'],
      ['Rolo de pintura', 'unidade', 'Proteção e ferramentas'],
      ['Pincel', 'unidade', 'Proteção e ferramentas'],
      ['Bandeja', 'unidade', 'Proteção e ferramentas'],
      ['Fita crepe', 'rolo', 'Proteção e ferramentas'],
      ['Lona de proteção', 'm²', 'Proteção e ferramentas'],
    ],
  },
  {
    id: 'acabamentos',
    name: 'Acabamentos',
    icon: Sparkles,
    color: 'var(--phase-acabamentos)',
    categories: ['Iluminação', 'Metais', 'Louças', 'Portas e ferragens', 'Acessórios'],
    materials: [
      ['Lâmpada', 'unidade', 'Iluminação'],
      ['Luminária', 'unidade', 'Iluminação'],
      ['Torneira', 'unidade', 'Metais'],
      ['Chuveiro', 'unidade', 'Metais'],
      ['Cuba', 'unidade', 'Louças'],
      ['Vaso sanitário', 'unidade', 'Louças'],
      ['Assento sanitário', 'unidade', 'Louças'],
      ['Porta', 'unidade', 'Portas e ferragens'],
      ['Fechadura', 'unidade', 'Portas e ferragens'],
      ['Maçaneta', 'unidade', 'Portas e ferragens'],
      ['Rodapé', 'metro', 'Acessórios'],
      ['Espelho', 'unidade', 'Acessórios'],
      ['Acessório de banheiro', 'unidade', 'Acessórios'],
    ],
  },
] as const

export const PHASES: Phase[] = PHASE_SEEDS.map((seed) => ({
  id: seed.id,
  name: seed.name,
  icon: seed.icon,
  color: seed.color,
}))

export const CATEGORIES: Category[] = PHASE_SEEDS.flatMap((seed) =>
  seed.categories.map((name) => ({
    id: `${seed.id}__${slugify(name)}`,
    phaseId: seed.id,
    name,
  })),
)

export const MATERIALS: MaterialDef[] = PHASE_SEEDS.flatMap((seed) =>
  seed.materials.map(([name, unit, categoryName]) => ({
    id: `${seed.id}__${slugify(categoryName)}__${slugify(name)}`,
    phaseId: seed.id,
    categoryId: `${seed.id}__${slugify(categoryName)}`,
    name,
    unit,
    allowsDecimal: unitAllowsDecimal(unit),
  })),
)

export function getPhase(phaseId: string): Phase | undefined {
  return PHASES.find((phase) => phase.id === phaseId)
}

export function getCategoriesForPhase(phaseId: string): Category[] {
  return CATEGORIES.filter((category) => category.phaseId === phaseId)
}

export function getMaterialsForPhase(phaseId: string): MaterialDef[] {
  return MATERIALS.filter((material) => material.phaseId === phaseId)
}

export function searchMaterials(phaseId: string, query: string, categoryId?: string): MaterialDef[] {
  const normalized = slugify(query)
  return getMaterialsForPhase(phaseId).filter((material) => {
    const matchesCategory = !categoryId || material.categoryId === categoryId
    const matchesQuery = !normalized || slugify(material.name).includes(normalized)
    return matchesCategory && matchesQuery
  })
}
