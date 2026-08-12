import { createPortal } from 'react-dom'
import { CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { useToast } from '../../state/ToastContext'
import styles from './ToastViewport.module.css'

export function ToastViewport() {
  const { toasts, dismissToast } = useToast()
  if (toasts.length === 0) return null

  return createPortal(
    <div className={styles.viewport} role="status" aria-live="polite">
      {toasts.map((toast) => {
        const Icon =
          toast.icon ?? (toast.tone === 'success' ? CheckCircle2 : toast.tone === 'error' ? AlertCircle : Info)
        return (
          <button
            key={toast.id}
            type="button"
            className={`${styles.toast} ${styles[toast.tone]}`}
            onClick={() => dismissToast(toast.id)}
          >
            <Icon size={20} aria-hidden="true" />
            <span>{toast.message}</span>
          </button>
        )
      })}
    </div>,
    document.body,
  )
}
