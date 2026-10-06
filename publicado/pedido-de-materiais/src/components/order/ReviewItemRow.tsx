import { Pencil, Trash2 } from 'lucide-react'
import type { OrderItem } from '../../types/models'
import { formatQuantity } from '../../utils/format'
import styles from './ReviewItemRow.module.css'

type Props = {
  item: OrderItem
  onEdit: () => void
  onRemove: () => void
}

export function ReviewItemRow({ item, onEdit, onRemove }: Props) {
  return (
    <div className={styles.row}>
      <div className={styles.info}>
        <p className={styles.name}>
          {item.name}
          {item.isCustom && <span className={styles.customTag}>manual</span>}
        </p>
        <p className={styles.meta}>
          {formatQuantity(item.quantity)} {item.unit}
          {item.categoryName ? ` · ${item.categoryName}` : ''}
        </p>
        {item.note && <p className={styles.note}>{item.note}</p>}
      </div>
      <div className={styles.actions}>
        <button type="button" className={styles.actionButton} onClick={onEdit} aria-label={`Editar quantidade de ${item.name}`}>
          <Pencil size={17} strokeWidth={2.25} aria-hidden="true" />
        </button>
        <button
          type="button"
          className={`${styles.actionButton} ${styles.remove}`}
          onClick={onRemove}
          aria-label={`Remover ${item.name} do pedido`}
        >
          <Trash2 size={17} strokeWidth={2.25} aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
