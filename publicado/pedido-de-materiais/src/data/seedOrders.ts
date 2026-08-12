import type { Order, OrderItem, OrderStatus, UrgencyLevel } from '../types/models'
import { MATERIALS, CATEGORIES } from './catalog'
import { generateId } from '../utils/id'
import { formatOrderNumber } from '../utils/format'

function addDays(days: number): Date {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date
}

function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function isoDateTime(date: Date): string {
  return date.toISOString()
}

function item(materialName: string, phaseId: string, quantity: number): OrderItem {
  const material = MATERIALS.find((m) => m.phaseId === phaseId && m.name === materialName)
  if (!material) throw new Error(`Material de demonstração não encontrado: ${materialName}`)
  const category = CATEGORIES.find((c) => c.id === material.categoryId)
  return {
    id: generateId(),
    materialId: material.id,
    name: material.name,
    unit: material.unit,
    quantity,
    isCustom: false,
    phaseId: material.phaseId,
    categoryName: category?.name,
  }
}

interface SeedSpec {
  sequence: number
  requesterName: string
  createdDaysAgo: number
  neededInDays: number
  location: string
  urgency: UrgencyLevel
  notes: string
  status: OrderStatus
  pendingSync: boolean
  items: OrderItem[]
}

const SEED_SPECS: SeedSpec[] = [
  {
    sequence: 1,
    requesterName: 'Carlos Silva',
    createdDaysAgo: 1,
    neededInDays: 5,
    location: 'Almoxarifado',
    urgency: 'normal',
    notes: '',
    status: 'solicitado',
    pendingSync: false,
    items: [item('Bloco cerâmico', 'alvenaria', 500), item('Cimento', 'alvenaria', 40)],
  },
  {
    sequence: 2,
    requesterName: 'Edimilson Souza',
    createdDaysAgo: 2,
    neededInDays: 3,
    location: 'Pavimento 2',
    urgency: 'urgente',
    notes: 'Time elétrico já está na obra aguardando o material.',
    status: 'em_aprovacao',
    pendingSync: false,
    items: [item('Cabo elétrico', 'instalacoes', 120), item('Disjuntor', 'instalacoes', 6)],
  },
  {
    sequence: 3,
    requesterName: 'Marcos Pereira',
    createdDaysAgo: 5,
    neededInDays: 1,
    location: 'Frente da obra',
    urgency: 'normal',
    notes: '',
    status: 'comprado',
    pendingSync: false,
    items: [item('Porcelanato', 'revestimentos', 38), item('Piso vinílico', 'revestimentos', 14)],
  },
  {
    sequence: 4,
    requesterName: 'José Ferreira',
    createdDaysAgo: 12,
    neededInDays: -7,
    location: 'Térreo',
    urgency: 'normal',
    notes: '',
    status: 'entregue',
    pendingSync: false,
    items: [item('Vaso sanitário', 'acabamentos', 2), item('Torneira', 'acabamentos', 3)],
  },
  {
    sequence: 5,
    requesterName: 'Antônio Rocha',
    createdDaysAgo: 8,
    neededInDays: -4,
    location: 'Pavimento 1',
    urgency: 'urgente',
    notes: 'Pedido duplicado — já havia sido solicitado por outro encarregado.',
    status: 'cancelado',
    pendingSync: false,
    items: [item('Tinta acrílica', 'pintura', 15), item('Rolo de pintura', 'pintura', 10)],
  },
]

export const SEED_ORDER_COUNT = SEED_SPECS.length

export function buildSeedOrders(): Order[] {
  return SEED_SPECS.map((spec) => ({
    id: generateId(),
    number: formatOrderNumber(spec.sequence),
    createdAt: isoDateTime(addDays(-spec.createdDaysAgo)),
    requesterName: spec.requesterName,
    items: spec.items,
    neededDate: isoDate(addDays(spec.neededInDays)),
    location: spec.location,
    urgency: spec.urgency,
    notes: spec.notes,
    status: spec.status,
    pendingSync: spec.pendingSync,
  }))
}
