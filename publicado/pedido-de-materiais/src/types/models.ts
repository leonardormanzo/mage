import type { LucideIcon } from 'lucide-react'

/** Unidades comuns oferecidas ao cadastrar um material manual (fora do catálogo). */
export const COMMON_UNITS = [
  'unidade',
  'saco',
  'peça',
  'metro',
  'm²',
  'm³',
  'kg',
  'lata',
  'rolo',
  'caixa',
  'pacote',
  'barra',
  'chapa',
] as const

export type CommonUnit = (typeof COMMON_UNITS)[number]

/**
 * Unidade de um material do catálogo. O catálogo usa algumas unidades fora da
 * lista comum (ex.: "painel", "tubo") — por isso é string livre, não um enum
 * fechado. O enum fechado (CommonUnit) vale só para o formulário de material manual.
 */
export type Unit = string

export interface Phase {
  id: string
  name: string
  icon: LucideIcon
  /** Token de cor CSS (ex.: "var(--phase-demolicao)") usado como identificação visual. */
  color: string
}

export interface Category {
  id: string
  phaseId: string
  name: string
}

export interface MaterialDef {
  id: string
  phaseId: string
  categoryId: string
  name: string
  unit: Unit
  /** m², m³, metro e kg aceitam casas decimais; unidades contáveis, não. */
  allowsDecimal: boolean
}

export type UrgencyLevel = 'normal' | 'urgente'

export interface OrderItem {
  id: string
  materialId: string | null
  name: string
  unit: Unit
  quantity: number
  isCustom: boolean
  /** Preenchido quando o item veio do catálogo. */
  phaseId?: string
  categoryName?: string
  /** Observação livre — usada principalmente em materiais manuais. */
  note?: string
}

export type OrderStatus = 'solicitado' | 'em_aprovacao' | 'comprado' | 'entregue' | 'cancelado'

export interface OrderStatusMeta {
  label: string
  icon: LucideIcon
  color: string
  softColor: string
  description: string
}

export interface OrderDraft {
  items: OrderItem[]
  neededDate: string
  location: string
  urgency: UrgencyLevel
  notes: string
}

export interface Order {
  id: string
  number: string
  createdAt: string
  requesterName: string
  items: OrderItem[]
  neededDate: string
  location: string
  urgency: UrgencyLevel
  notes: string
  status: OrderStatus
  /** Simulação visual de sincronização offline — nunca reflete rede real. */
  pendingSync: boolean
}

export function createEmptyDraft(): OrderDraft {
  return {
    items: [],
    neededDate: '',
    location: '',
    urgency: 'normal',
    notes: '',
  }
}
