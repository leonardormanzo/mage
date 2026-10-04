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
  materials: ReadonlyArray<
    readonly [name: string, unit: Unit, category: string, brands?: readonly [string, string]]
  >
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
      ['Placa de gesso acartonado', 'unidade', 'Drywall', ['Placo', 'Knauf']],
      ['Perfil metálico para drywall', 'metro', 'Drywall', ['Placo', 'Knauf']],
      ['Massa para drywall', 'saco', 'Drywall', ['Placo', 'Knauf']],
      ['Fita para drywall', 'rolo', 'Drywall'],
      ['Cimento', 'saco', 'Argamassas', ['Votorantim', 'Cauê']],
      ['Areia média', 'm³', 'Argamassas'],
      ['Argamassa de assentamento', 'saco', 'Argamassas', ['Quartzolit', 'Votorantim']],
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
      ['Cabo elétrico', 'metro', 'Elétrica', ['Sil', 'Prysmian']],
      ['Caixa 4×2', 'unidade', 'Elétrica'],
      ['Caixa de passagem', 'unidade', 'Elétrica'],
      ['Disjuntor', 'unidade', 'Elétrica', ['Siemens', 'WEG']],
      ['Quadro de distribuição', 'unidade', 'Elétrica', ['Siemens', 'WEG']],
      ['Tomada', 'unidade', 'Elétrica', ['Pial', 'Tramontina']],
      ['Interruptor', 'unidade', 'Elétrica', ['Pial', 'Tramontina']],
      ['Fita isolante', 'rolo', 'Elétrica'],
      ['Tubo PVC', 'barra', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Joelho PVC', 'unidade', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Tê PVC', 'unidade', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Luva PVC', 'unidade', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Registro', 'unidade', 'Hidráulica', ['Deca', 'Docol']],
      ['Válvula', 'unidade', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Adesivo para PVC', 'tubo', 'Hidráulica', ['Tigre', 'Amanco']],
      ['Fita veda-rosca', 'rolo', 'Hidráulica'],
      ['Caixa-d’água', 'unidade', 'Hidráulica', ['Fortlev', 'Tigre']],
    ],
  },
  {
    id: 'revestimentos',
    name: 'Revestimentos',
    icon: Grid3x3,
    color: 'var(--phase-revestimentos)',
    categories: ['Pisos', 'Paredes', 'Assentamento', 'Impermeabilização'],
    materials: [
      ['Piso cerâmico', 'm²', 'Pisos', ['Portobello', 'Eliane']],
      ['Porcelanato', 'm²', 'Pisos', ['Portobello', 'Eliane']],
      ['Piso vinílico', 'm²', 'Pisos', ['Tarkett', 'Durafloor']],
      ['Manta acústica', 'm²', 'Pisos'],
      ['Nivelador de piso', 'pacote', 'Pisos'],
      ['Revestimento de parede', 'm²', 'Paredes', ['Portobello', 'Eliane']],
      ['Rodapé', 'metro', 'Paredes'],
      ['Argamassa colante', 'saco', 'Assentamento', ['Quartzolit', 'Votorantim']],
      ['Rejunte', 'pacote', 'Assentamento', ['Quartzolit', 'Fortaleza']],
      ['Espaçador', 'pacote', 'Assentamento'],
      ['Manta impermeabilizante', 'rolo', 'Impermeabilização', ['Vedacit', 'Sika']],
      ['Impermeabilizante', 'lata', 'Impermeabilização', ['Vedacit', 'Sika']],
    ],
  },
  {
    id: 'pintura',
    name: 'Pintura',
    icon: PaintRoller,
    color: 'var(--phase-pintura)',
    categories: ['Preparação', 'Pintura', 'Proteção e ferramentas'],
    materials: [
      ['Massa corrida', 'lata', 'Preparação', ['Suvinil', 'Coral']],
      ['Massa acrílica', 'lata', 'Preparação', ['Suvinil', 'Coral']],
      ['Fundo preparador', 'lata', 'Preparação', ['Suvinil', 'Coral']],
      ['Selador', 'lata', 'Preparação', ['Suvinil', 'Coral']],
      ['Lixa', 'unidade', 'Preparação'],
      ['Tinta acrílica', 'lata', 'Pintura', ['Suvinil', 'Coral']],
      ['Esmalte', 'lata', 'Pintura', ['Suvinil', 'Coral']],
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
      ['Lâmpada', 'unidade', 'Iluminação', ['Philips', 'Avant']],
      ['Luminária', 'unidade', 'Iluminação', ['Taschibra', 'Avant']],
      ['Torneira', 'unidade', 'Metais', ['Deca', 'Docol']],
      ['Chuveiro', 'unidade', 'Metais', ['Lorenzetti', 'Fabrimar']],
      ['Cuba', 'unidade', 'Louças', ['Deca', 'Celite']],
      ['Vaso sanitário', 'unidade', 'Louças', ['Deca', 'Celite']],
      ['Assento sanitário', 'unidade', 'Louças', ['Deca', 'Celite']],
      ['Porta', 'unidade', 'Portas e ferragens'],
      ['Fechadura', 'unidade', 'Portas e ferragens', ['Papaiz', 'La Fonte']],
      ['Maçaneta', 'unidade', 'Portas e ferragens', ['Papaiz', 'La Fonte']],
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
  seed.materials.map(([name, unit, categoryName, brands]) => ({
    id: `${seed.id}__${slugify(categoryName)}__${slugify(name)}`,
    phaseId: seed.id,
    categoryId: `${seed.id}__${slugify(categoryName)}`,
    name,
    unit,
    allowsDecimal: unitAllowsDecimal(unit),
    brands,
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
