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
  Share2,
  Printer,
  Copy,
  Trash2,
  CheckCircle,
} from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { useToast } from '../../state/ToastContext'
import { OBRA } from '../../data/obra'
import { formatDateBR, formatDateTimeBR, formatQuantity } from '../../utils/format'
import { StatusBadge } from '../ui/StatusBadge'
import { EmptyState } from '../ui/EmptyState'
import { ORDER_STATUS_META } from '../../data/orderStatus'
import type { OrderStatus } from '../../types/models'
import styles from './OrderDetailScreen.module.css'

type Props = {
  orderId: string
}

export function OrderDetailScreen({ orderId }: Props) {
  const { state, dispatch } = useAppState()
  const { showToast } = useToast()
  const order = state.orders.find((candidate) => candidate.id === orderId)

  if (!order) {
    return (
      <div className={styles.page}>
        <EmptyState icon={FileQuestion} title="Pedido não encontrado" description="Esse pedido pode ter sido removido." />
      </div>
    )
  }

  const statusMeta = ORDER_STATUS_META[order.status]

  function formatTextSummary(): string {
    if (!order) return ''
    const itemsList = order.items
      .map((item, idx) => `${idx + 1}. *${item.name}*: ${formatQuantity(item.quantity)} ${item.unit}`)
      .join('\n')

    return `📦 *SOLICITAÇÃO DE MATERIAIS* - ${order.number}
🏗️ *Obra:* ${OBRA.nome} (${OBRA.codigo})
👤 *Solicitante:* ${order.requesterName}
📅 *Data da Solicitacao:* ${formatDateTimeBR(order.createdAt)}
⏰ *Prazo Necessario:* ${formatDateBR(order.neededDate)}
📍 *Local na Obra:* ${order.location}
⚡ *Prioridade:* ${order.urgency === 'urgente' ? 'URGENTE' : 'Normal'}
📊 *Status Atual:* ${statusMeta.label}

📝 *MATERIAIS:*
${itemsList}

${order.notes ? `💬 *Observacoes:* ${order.notes}` : ''}`
  }

  function handleShareWhatsApp() {
    const text = formatTextSummary()
    const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`
    window.open(url, '_blank')
    showToast('Redirecionando para o WhatsApp...', { tone: 'success', icon: Share2 })
  }

  function handleCopySummary() {
    const text = formatTextSummary()
    navigator.clipboard.writeText(text).then(
      () => showToast('Resumo copiado para a área de transferência!', { tone: 'success', icon: Copy }),
      () => showToast('Falha ao copiar texto.', { tone: 'error' }),
    )
  }

  const currentOrder = order

  function handlePrint() {
    window.print()
  }

  function handleStatusChange(newStatus: OrderStatus) {
    dispatch({ type: 'UPDATE_ORDER_STATUS', orderId: currentOrder.id, status: newStatus })
    showToast(`Status atualizado para "${ORDER_STATUS_META[newStatus].label}"`, {
      tone: 'success',
      icon: CheckCircle,
    })
  }

  function handleDelete() {
    if (confirm(`Tem certeza que deseja cancelar/excluir o pedido ${currentOrder.number}?`)) {
      dispatch({ type: 'DELETE_ORDER', orderId: currentOrder.id })
      dispatch({ type: 'NAVIGATE', screen: { name: 'my-orders' } })
      showToast(`Pedido ${currentOrder.number} excluído.`, { tone: 'neutral', icon: Trash2 })
    }
  }

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

      <div className={styles.actionGrid}>
        <button type="button" onClick={handleShareWhatsApp} className={`${styles.btnAction} ${styles.btnPrimaryAction}`}>
          <Share2 size={16} strokeWidth={2.25} />
          WhatsApp
        </button>
        <button type="button" onClick={handleCopySummary} className={styles.btnAction}>
          <Copy size={16} strokeWidth={2.25} />
          Copiar
        </button>
        <button type="button" onClick={handlePrint} className={styles.btnAction}>
          <Printer size={16} strokeWidth={2.25} />
          Imprimir PDF
        </button>
        <button type="button" onClick={handleDelete} className={`${styles.btnAction} ${styles.btnDanger}`}>
          <Trash2 size={16} strokeWidth={2.25} />
          Excluir
        </button>
      </div>

      <div className={styles.statusSelectorRow}>
        <label htmlFor="status-select" style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>
          Alterar Status:
        </label>
        <select
          id="status-select"
          className={styles.statusSelect}
          value={order.status}
          onChange={(e) => handleStatusChange(e.target.value as OrderStatus)}
        >
          <option value="solicitado">Solicitado</option>
          <option value="em_aprovacao">Em Aprovação</option>
          <option value="comprado">Comprado</option>
          <option value="entregue">Entregue</option>
          <option value="cancelado">Cancelado</option>
        </select>
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
