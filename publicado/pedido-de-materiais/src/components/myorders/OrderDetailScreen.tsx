import {
  Calendar,
  MapPin,
  AlertTriangle,
  CalendarCheck,
  MessageSquare,
  CloudOff,
  User,
  Building2,
  FileQuestion,
} from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { OBRA } from '../../data/obra'
import { formatDateBR, formatDateTimeBR, formatQuantity } from '../../utils/format'
import { StatusBadge } from '../ui/StatusBadge'
import { EmptyState } from '../ui/EmptyState'
import { ORDER_STATUS_META } from '../../data/orderStatus'
import styles from './OrderDetailScreen.module.css'

type Props = {
  orderId: string
}

export function OrderDetailScreen({ orderId }: Props) {
  const { state } = useAppState()
  const order = state.orders.find((candidate) => candidate.id === orderId)

  if (!order) {
    return (
      <div className={styles.page}>
        <EmptyState icon={FileQuestion} title="Pedido não encontrado" description="Esse pedido pode ter sido removido." />
      </div>
    )
  }

  const statusMeta = ORDER_STATUS_META[order.status]

  return (
    <div className={styles.page}>
      <div className={styles.headerCard}>
        <div className={styles.headerTop}>
          <span className={styles.number}>Pedido {order.number}</span>
          <StatusBadge status={order.status} />
        </div>
        <p className={styles.statusDescription}>{statusMeta.description}</p>
        <p className={styles.createdAt}>Solicitado em {formatDateTimeBR(order.createdAt)}</p>
        {order.pendingSync && (
          <p className={styles.pendingNotice}>
            <CloudOff size={14} strokeWidth={2.5} aria-hidden="true" />
            Aguardando sincronização (simulação de modo offline)
          </p>
        )}
      </div>

      <section className={styles.section}>
        <div className={styles.infoRow}>
          <Building2 size={18} strokeWidth={2.25} aria-hidden="true" />
          <span>
            {OBRA.nome} · {OBRA.codigo}
          </span>
        </div>
        <div className={styles.infoRow}>
          <User size={18} strokeWidth={2.25} aria-hidden="true" />
          <span>{order.requesterName}</span>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Materiais ({order.items.length})</h2>
        <div className={styles.itemList}>
          {order.items.map((item) => (
            <div key={item.id} className={styles.itemRow}>
              <span className={styles.itemName}>{item.name}</span>
              <span className={styles.itemQty}>
                {formatQuantity(item.quantity)} {item.unit}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Dados do pedido</h2>
        <div className={styles.detailsCard}>
          <div className={styles.infoRow}>
            <Calendar size={18} strokeWidth={2.25} aria-hidden="true" />
            <span>Necessário em {formatDateBR(order.neededDate)}</span>
          </div>
          <div className={styles.infoRow}>
            <MapPin size={18} strokeWidth={2.25} aria-hidden="true" />
            <span>{order.location}</span>
          </div>
          <div className={styles.infoRow}>
            {order.urgency === 'urgente' ? (
              <AlertTriangle size={18} strokeWidth={2.25} aria-hidden="true" />
            ) : (
              <CalendarCheck size={18} strokeWidth={2.25} aria-hidden="true" />
            )}
            <span>{order.urgency === 'urgente' ? 'Urgente' : 'Normal'}</span>
          </div>
          {order.notes && (
            <div className={styles.infoRow}>
              <MessageSquare size={18} strokeWidth={2.25} aria-hidden="true" />
              <span>{order.notes}</span>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
