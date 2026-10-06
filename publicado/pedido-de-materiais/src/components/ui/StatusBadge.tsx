import { ORDER_STATUS_META } from '../../data/orderStatus'
import type { OrderStatus } from '../../types/models'
import styles from './StatusBadge.module.css'

type Props = {
  status: OrderStatus
  size?: 'sm' | 'md'
}

export function StatusBadge({ status, size = 'md' }: Props) {
  const meta = ORDER_STATUS_META[status]
  const Icon = meta.icon

  return (
    <span
      className={`${styles.badge} ${styles[size]}`}
      style={{ color: meta.color, background: meta.softColor }}
    >
      <Icon size={size === 'sm' ? 14 : 16} strokeWidth={2.5} aria-hidden="true" />
      {meta.label}
    </span>
  )
}
