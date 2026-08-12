import { useState } from 'react'
import { HardHat, ChevronRight, Pencil, WifiOff, ClipboardList, Trash2 } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { ConnectivityDemoSheet } from '../connectivity/ConnectivityDemoSheet'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { RenameSheet } from './RenameSheet'
import styles from './HomeScreen.module.css'

export function HomeScreen() {
  const { state, dispatch } = useAppState()
  const [showRename, setShowRename] = useState(false)
  const [showConnectivity, setShowConnectivity] = useState(false)
  const [showDiscardConfirm, setShowDiscardConfirm] = useState(false)

  const openOrdersCount = state.orders.filter(
    (order) => order.status !== 'entregue' && order.status !== 'cancelado',
  ).length
  const draftCount = state.draft.items.length

  return (
    <div className={styles.page}>
      <div className={styles.greetingRow}>
        <div>
          <h1 className={styles.greeting}>Olá, {state.workerName}</h1>
          <p className={styles.subtitle}>O que você precisa hoje?</p>
        </div>
        <button type="button" className={styles.renameButton} onClick={() => setShowRename(true)} aria-label="Trocar nome">
          <Pencil size={18} strokeWidth={2.25} aria-hidden="true" />
        </button>
      </div>

      <button
        type="button"
        className={styles.primaryCta}
        onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'phase-select' } })}
      >
        <span className={styles.primaryCtaIcon} aria-hidden="true">
          <HardHat size={30} strokeWidth={2.25} />
        </span>
        <span className={styles.primaryCtaText}>
          <span className={styles.primaryCtaTitle}>Pedir material</span>
          <span className={styles.primaryCtaSubtitle}>Escolha a fase da obra e monte seu pedido</span>
        </span>
        <ChevronRight size={22} aria-hidden="true" />
      </button>

      {draftCount > 0 && (
        <div className={styles.draftCard}>
          <div className={styles.draftInfo}>
            <p className={styles.draftTitle}>Pedido em andamento</p>
            <p className={styles.draftSubtitle}>
              {draftCount} {draftCount === 1 ? 'item adicionado' : 'itens adicionados'}
            </p>
          </div>
          <div className={styles.draftActions}>
            <button
              type="button"
              className={styles.draftDiscard}
              onClick={() => setShowDiscardConfirm(true)}
              aria-label="Descartar pedido em andamento"
            >
              <Trash2 size={18} aria-hidden="true" />
            </button>
            <button
              type="button"
              className={styles.draftContinue}
              onClick={() => dispatch({ type: 'NAVIGATE', screen: { name: 'review' } })}
            >
              Continuar
            </button>
          </div>
        </div>
      )}

      <button
        type="button"
        className={styles.statCard}
        onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'my-orders' } })}
      >
        <span className={styles.statIcon} aria-hidden="true">
          <ClipboardList size={22} strokeWidth={2.25} />
        </span>
        <span className={styles.statText}>
          <span className={styles.statValue}>{openOrdersCount}</span>
          <span className={styles.statLabel}>{openOrdersCount === 1 ? 'pedido em aberto' : 'pedidos em aberto'}</span>
        </span>
        <ChevronRight size={20} aria-hidden="true" />
      </button>

      <button type="button" className={styles.demoLink} onClick={() => setShowConnectivity(true)}>
        <WifiOff size={16} aria-hidden="true" />
        Ver simulação de modo offline
      </button>

      <RenameSheet isOpen={showRename} onClose={() => setShowRename(false)} />
      <ConnectivityDemoSheet isOpen={showConnectivity} onClose={() => setShowConnectivity(false)} />
      <ConfirmDialog
        isOpen={showDiscardConfirm}
        title="Descartar pedido em andamento?"
        description="Os itens que você já adicionou serão apagados. Essa ação não pode ser desfeita."
        confirmLabel="Descartar"
        cancelLabel="Manter pedido"
        tone="danger"
        onConfirm={() => {
          dispatch({ type: 'DISCARD_DRAFT' })
          setShowDiscardConfirm(false)
        }}
        onCancel={() => setShowDiscardConfirm(false)}
      />
    </div>
  )
}
