import { ClipboardList } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import type { ScreenState } from '../../state/screens'
import styles from './CartFab.module.css'

type Props = {
  /** true quando a nav inferior também está visível nesta tela (ex.: seleção de fase). */
  hasNavBelow: boolean
}

export function CartFab({ hasNavBelow }: Props) {
  const { state, dispatch } = useAppState()
  const count = state.draft.items.length
  if (count === 0) return null

  const nextScreen: ScreenState = state.draft.neededDate ? { name: 'review' } : { name: 'order-details' }

  return (
    <button
      type="button"
      className={`${styles.fab} ${hasNavBelow ? styles.withNav : ''}`}
      onClick={() => dispatch({ type: 'NAVIGATE', screen: nextScreen })}
    >
      <ClipboardList size={20} strokeWidth={2.25} aria-hidden="true" />
      Ver pedido — {count} {count === 1 ? 'item' : 'itens'}
    </button>
  )
}
