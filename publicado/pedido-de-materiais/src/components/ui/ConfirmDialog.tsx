import { AlertTriangle } from 'lucide-react'
import { Sheet } from './Sheet'
import { Button } from './Button'
import styles from './ConfirmDialog.module.css'

type Props = {
  isOpen: boolean
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'default' | 'danger'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  tone = 'default',
  onConfirm,
  onCancel,
}: Props) {
  return (
    <Sheet isOpen={isOpen} onClose={onCancel}>
      <div className={styles.wrapper}>
        <div className={`${styles.icon} ${tone === 'danger' ? styles.iconDanger : ''}`} aria-hidden="true">
          <AlertTriangle size={26} strokeWidth={2.25} />
        </div>
        <h2 className={styles.title}>{title}</h2>
        {description && <p className={styles.description}>{description}</p>}
        <div className={styles.actions}>
          <Button variant={tone === 'danger' ? 'danger' : 'primary'} fullWidth onClick={onConfirm}>
            {confirmLabel}
          </Button>
          <Button variant="ghost" fullWidth onClick={onCancel}>
            {cancelLabel}
          </Button>
        </div>
      </div>
    </Sheet>
  )
}
