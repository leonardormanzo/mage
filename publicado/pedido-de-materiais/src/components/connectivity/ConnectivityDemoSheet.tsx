import { useEffect, useRef, useState } from 'react'
import { Wifi, WifiOff, RefreshCw, CloudCheck, Info } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { useToast } from '../../state/ToastContext'
import { Sheet } from '../ui/Sheet'
import { Switch } from '../ui/Switch'
import styles from './ConnectivityDemoSheet.module.css'

const SYNC_DELAY_MS = 1100

type Props = {
  isOpen: boolean
  onClose: () => void
}

export function ConnectivityDemoSheet({ isOpen, onClose }: Props) {
  const { state, dispatch } = useAppState()
  const { showToast } = useToast()
  const [isSyncing, setIsSyncing] = useState(false)
  const timerRef = useRef<number | null>(null)

  const pendingCount = state.orders.filter((order) => order.pendingSync).length

  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [])

  function handleToggle(nextOnline: boolean) {
    if (!nextOnline) {
      dispatch({ type: 'SET_ONLINE_SIM', isOnline: false })
      showToast('Modo offline ativado (simulação).', { icon: WifiOff })
      return
    }

    if (pendingCount === 0) {
      dispatch({ type: 'SET_ONLINE_SIM', isOnline: true })
      showToast('Conectado novamente (simulação).', { icon: Wifi, tone: 'success' })
      return
    }

    setIsSyncing(true)
    showToast('Sincronizando pedidos salvos no aparelho…', { icon: RefreshCw })
    timerRef.current = window.setTimeout(() => {
      dispatch({ type: 'SET_ONLINE_SIM', isOnline: true })
      setIsSyncing(false)
      showToast(`${pendingCount} pedido(s) sincronizado(s) (simulação).`, { icon: CloudCheck, tone: 'success' })
    }, SYNC_DELAY_MS)
  }

  return (
    <Sheet isOpen={isOpen} onClose={onClose} title="Modo offline (demonstração)">
      <div className={styles.wrapper}>
        <Switch
          id="connectivity-toggle"
          label={state.isOnlineSim ? 'Conectado' : 'Sem internet'}
          checked={state.isOnlineSim}
          onChange={handleToggle}
        />

        {isSyncing && (
          <p className={styles.syncing}>
            <RefreshCw size={16} className={styles.spinIcon} aria-hidden="true" />
            Sincronizando pedidos…
          </p>
        )}

        {!state.isOnlineSim && !isSyncing && (
          <p className={styles.hint}>
            Agora, ao confirmar um pedido, ele fica marcado como <strong>“Aguardando sincronização”</strong> em
            “Meus pedidos” até você voltar para o modo conectado.
          </p>
        )}

        {state.isOnlineSim && pendingCount > 0 && !isSyncing && (
          <p className={styles.hint}>{pendingCount} pedido(s) ainda aguardando sincronização.</p>
        )}

        <div className={styles.disclaimer}>
          <Info size={16} aria-hidden="true" />
          <p>
            Isto é uma <strong>simulação visual</strong> de como o app vai se comportar sem internet no futuro. O
            salvamento neste aparelho (localStorage) já funciona de verdade — não existe sincronização real com
            nenhum servidor nesta versão.
          </p>
        </div>
      </div>
    </Sheet>
  )
}
