import { Home, HardHat, ClipboardList } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import type { TabName } from '../../state/screens'
import styles from './BottomNav.module.css'

type Props = {
  activeTab: TabName
}

export function BottomNav({ activeTab }: Props) {
  const { dispatch } = useAppState()

  return (
    <nav className={`glass-surface ${styles.nav}`} aria-label="Navegação principal">
      <button
        type="button"
        className={`${styles.tab} ${activeTab === 'home' ? styles.tabActive : ''}`}
        aria-current={activeTab === 'home' ? 'page' : undefined}
        onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'home' } })}
      >
        <Home size={22} strokeWidth={2.25} aria-hidden="true" />
        <span>Início</span>
      </button>

      <button type="button" className={styles.primaryTab} onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'phase-select' } })}>
        <span className={`${styles.primaryCircle} ${activeTab === 'order' ? styles.primaryCircleActive : ''}`}>
          <HardHat size={26} strokeWidth={2.25} aria-hidden="true" />
        </span>
        <span className={activeTab === 'order' ? styles.primaryLabelActive : ''}>Pedir material</span>
      </button>

      <button
        type="button"
        className={`${styles.tab} ${activeTab === 'my-orders' ? styles.tabActive : ''}`}
        aria-current={activeTab === 'my-orders' ? 'page' : undefined}
        onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'my-orders' } })}
      >
        <ClipboardList size={22} strokeWidth={2.25} aria-hidden="true" />
        <span>Meus pedidos</span>
      </button>
    </nav>
  )
}
