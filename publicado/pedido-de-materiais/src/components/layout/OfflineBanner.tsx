import { WifiOff } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import styles from './OfflineBanner.module.css'

export function OfflineBanner() {
  const { state } = useAppState()
  if (state.isOnlineSim) return null

  return (
    <div className={styles.banner} role="status">
      <WifiOff size={16} strokeWidth={2.5} aria-hidden="true" />
      <span>
        Sem internet — pedidos ficam salvos neste aparelho. <strong>Simulação.</strong>
      </span>
    </div>
  )
}
