import type { CSSProperties } from 'react'
import type { Phase } from '../../types/models'
import styles from './PhaseCard.module.css'

type Props = {
  phase: Phase
  onSelect: () => void
}

export function PhaseCard({ phase, onSelect }: Props) {
  const Icon = phase.icon

  return (
    <button
      type="button"
      className={styles.card}
      style={{ '--phase-color': phase.color } as CSSProperties}
      onClick={onSelect}
    >
      <span className={styles.iconWrap} aria-hidden="true">
        <Icon size={30} strokeWidth={2.25} />
      </span>
      <span className={styles.name}>{phase.name}</span>
    </button>
  )
}
