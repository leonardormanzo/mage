import { Package, Calendar, AlertTriangle, CloudOff, ChevronRight } from 'lucide-react'
import type { Order } from '../../types/models'
import { formatDateBR, formatDateTimeBR } from '../../utils/format'
import { StatusBadge } from '../ui/StatusBadge'
import styles from './OrderCard.module.css'

type Props = {
  order: Order
  onView: () => void
}

export function OrderCard({ order, onView }: Props) {
  return (
    <button type="button" className={styles.card} onClick={onView}>
      <div className={styles.headerRow}>
        <span className={styles.number}>Pedido {order.number}</span>
        <StatusBadge status={order.status} />
      </div>

      <p className={styles.date}>{formatDateTimeBR(order.createdAt)}</p>

      <div className={styles.metaRow}>
        <span className={styles.metaItem}>
          <Package size={14} strokeWidth={2.25} aria-hidden="true" />
          {order.items.length} {order.items.length === 1 ? 'item' : 'itens'}
        </span>
        <span className={styles.metaItem}>
          <Calendar size={14} strokeWidth={2.25} aria-hidden="true" />
          Necessário: {formatDateBR(order.neededDate)}
        </span>
      </div>

      {(order.urgency === 'urgente' || order.pendingSync) && (
        <div className={styles.tagRow}>
          {order.urgency === 'urgente' && (
            <span className={styles.urgentTag}>
              <AlertTriangle size={13} strokeWidth={2.5} aria-hidden="true" />
              Urgente
            </span>
          )}
          {order.pendingSync && (
            <span className={styles.pendingTag}>
              <CloudOff size={13} strokeWidth={2.5} aria-hidden="true" />
              Aguardando sincronização
            </span>
          )}
        </div>
      )}

      <span className={styles.viewLink}>
        Ver detalhes
        <ChevronRight size={16} aria-hidden="true" />
      </span>
    </button>
  )
}
