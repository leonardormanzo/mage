import { useState } from 'react'
import { Wifi, WifiOff } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { OBRA } from '../../data/obra'
import { ConnectivityDemoSheet } from '../connectivity/ConnectivityDemoSheet'
import styles from './TopBar.module.css'

export function TopBar() {
  const { state } = useAppState()
  const [showConnectivitySheet, setShowConnectivitySheet] = useState(false)

  return (
    <header className={`glass-surface ${styles.topBar}`}>
      <div className={styles.obraInfo}>
        <span className={styles.obraName}>{OBRA.nome}</span>
        <span className={styles.obraMeta}>
          {OBRA.codigo} · {OBRA.local}
        </span>
      </div>
      <button
        type="button"
        className={`${styles.connectivityPill} ${state.isOnlineSim ? '' : styles.offline}`}
        onClick={() => setShowConnectivitySheet(true)}
      >
        {state.isOnlineSim ? <Wifi size={14} aria-hidden="true" /> : <WifiOff size={14} aria-hidden="true" />}
        {state.isOnlineSim ? 'Online' : 'Sem internet'}
      </button>
      <ConnectivityDemoSheet isOpen={showConnectivitySheet} onClose={() => setShowConnectivitySheet(false)} />
    </header>
  )
}
