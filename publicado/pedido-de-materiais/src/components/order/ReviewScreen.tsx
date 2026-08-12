import { useState } from 'react'
import { Building2, User, Calendar, MapPin, AlertTriangle, CalendarCheck, MessageSquare, PackagePlus, ClipboardX } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { useToast } from '../../state/ToastContext'
import { OBRA } from '../../data/obra'
import type { OrderItem } from '../../types/models'
import { generateId } from '../../utils/id'
import { formatDateBR } from '../../utils/format'
import { Button } from '../ui/Button'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { EmptyState } from '../ui/EmptyState'
import { ReviewItemRow } from './ReviewItemRow'
import { EditQuantitySheet } from './EditQuantitySheet'
import styles from './ReviewScreen.module.css'

export function ReviewScreen() {
  const { state, dispatch } = useAppState()
  const { showToast } = useToast()
  const [editingItem, setEditingItem] = useState<OrderItem | null>(null)
  const [removingItem, setRemovingItem] = useState<OrderItem | null>(null)

  const { draft, workerName } = state
  const hasItems = draft.items.length > 0

  function handleConfirm() {
    dispatch({ type: 'CONFIRM_ORDER', orderId: generateId(), createdAt: new Date().toISOString() })
  }

  return (
    <div className={styles.page}>
      <section className={styles.summaryCard}>
        <div className={styles.summaryRow}>
          <Building2 size={18} strokeWidth={2.25} aria-hidden="true" />
          <div>
            <p className={styles.summaryLabel}>Obra</p>
            <p className={styles.summaryValue}>
              {OBRA.nome} · {OBRA.codigo}
            </p>
          </div>
        </div>
        <div className={styles.summaryRow}>
          <User size={18} strokeWidth={2.25} aria-hidden="true" />
          <div>
            <p className={styles.summaryLabel}>Solicitante</p>
            <p className={styles.summaryValue}>{workerName}</p>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Materiais</h2>
          <button
            type="button"
            className={styles.addMoreLink}
            onClick={() => dispatch({ type: 'NAVIGATE', screen: { name: 'phase-select' } })}
          >
            <PackagePlus size={16} strokeWidth={2.25} aria-hidden="true" />
            Adicionar mais
          </button>
        </div>

        {hasItems ? (
          <div className={styles.itemList}>
            {draft.items.map((item) => (
              <ReviewItemRow
                key={item.id}
                item={item}
                onEdit={() => setEditingItem(item)}
                onRemove={() => setRemovingItem(item)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ClipboardX}
            title="Nenhum material no pedido"
            description="Volte e escolha uma fase para adicionar materiais antes de confirmar."
            action={
              <Button variant="secondary" onClick={() => dispatch({ type: 'NAVIGATE', screen: { name: 'phase-select' } })}>
                Adicionar materiais
              </Button>
            }
          />
        )}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Dados do pedido</h2>
          <button
            type="button"
            className={styles.addMoreLink}
            onClick={() => dispatch({ type: 'NAVIGATE', screen: { name: 'order-details' } })}
          >
            Editar
          </button>
        </div>

        <div className={styles.detailsCard}>
          <div className={styles.detailRow}>
            <Calendar size={18} strokeWidth={2.25} aria-hidden="true" />
            <span>{draft.neededDate ? formatDateBR(draft.neededDate) : 'Data não definida'}</span>
          </div>
          <div className={styles.detailRow}>
            <MapPin size={18} strokeWidth={2.25} aria-hidden="true" />
            <span>{draft.location || 'Local não definido'}</span>
          </div>
          <div className={styles.detailRow}>
            {draft.urgency === 'urgente' ? (
              <AlertTriangle size={18} strokeWidth={2.25} aria-hidden="true" />
            ) : (
              <CalendarCheck size={18} strokeWidth={2.25} aria-hidden="true" />
            )}
            <span>{draft.urgency === 'urgente' ? 'Urgente' : 'Normal'}</span>
          </div>
          {draft.notes && (
            <div className={styles.detailRow}>
              <MessageSquare size={18} strokeWidth={2.25} aria-hidden="true" />
              <span>{draft.notes}</span>
            </div>
          )}
        </div>
      </section>

      <Button fullWidth disabled={!hasItems} onClick={handleConfirm}>
        Confirmar pedido
      </Button>

      <EditQuantitySheet
        item={editingItem}
        onClose={() => setEditingItem(null)}
        onSave={(quantity) => {
          if (!editingItem) return
          dispatch({ type: 'UPDATE_ITEM_QUANTITY', itemId: editingItem.id, quantity })
          showToast(`${editingItem.name}: quantidade atualizada.`, { tone: 'success' })
          setEditingItem(null)
        }}
      />

      <ConfirmDialog
        isOpen={removingItem !== null}
        title={removingItem ? `Remover ${removingItem.name}?` : ''}
        description="Esse item será retirado do pedido."
        confirmLabel="Remover"
        cancelLabel="Manter"
        tone="danger"
        onConfirm={() => {
          if (!removingItem) return
          dispatch({ type: 'REMOVE_ITEM', itemId: removingItem.id })
          showToast(`${removingItem.name} removido do pedido.`)
          setRemovingItem(null)
        }}
        onCancel={() => setRemovingItem(null)}
      />
    </div>
  )
}
