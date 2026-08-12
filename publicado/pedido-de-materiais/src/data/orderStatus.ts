import { Send, Hourglass, ShoppingCart, PackageCheck, PackageX } from 'lucide-react'
import type { OrderStatus, OrderStatusMeta } from '../types/models'

export const ORDER_STATUS_META: Record<OrderStatus, OrderStatusMeta> = {
  solicitado: {
    label: 'Solicitado',
    icon: Send,
    color: 'var(--color-neutral)',
    softColor: 'var(--color-neutral-soft)',
    description: 'Pedido enviado, aguardando análise do escritório.',
  },
  em_aprovacao: {
    label: 'Em aprovação',
    icon: Hourglass,
    color: 'var(--color-warning)',
    softColor: 'var(--color-warning-soft)',
    description: 'O escritório está avaliando o pedido.',
  },
  comprado: {
    label: 'Comprado',
    icon: ShoppingCart,
    color: 'var(--color-info)',
    softColor: 'var(--color-info-soft)',
    description: 'Compra feita — aguardando entrega na obra.',
  },
  entregue: {
    label: 'Entregue',
    icon: PackageCheck,
    color: 'var(--color-success)',
    softColor: 'var(--color-success-soft)',
    description: 'Material entregue na obra.',
  },
  cancelado: {
    label: 'Cancelado',
    icon: PackageX,
    color: 'var(--color-danger)',
    softColor: 'var(--color-danger-soft)',
    description: 'Pedido cancelado — não será comprado.',
  },
}

export const ORDER_STATUS_ORDER: OrderStatus[] = [
  'solicitado',
  'em_aprovacao',
  'comprado',
  'entregue',
  'cancelado',
]
