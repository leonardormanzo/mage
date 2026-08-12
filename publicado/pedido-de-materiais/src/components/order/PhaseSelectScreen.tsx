import { useAppState } from '../../state/AppStateContext'
import { PHASES } from '../../data/catalog'
import { PhaseCard } from './PhaseCard'
import { CartFab } from './CartFab'
import styles from './PhaseSelectScreen.module.css'

export function PhaseSelectScreen() {
  const { dispatch } = useAppState()

  return (
    <div className={styles.page}>
      <div className={styles.intro}>
        <h1 className={styles.title}>Qual fase da obra?</h1>
        <p className={styles.subtitle}>Escolha para ver os materiais dessa etapa</p>
      </div>

      <div className={styles.grid}>
        {PHASES.map((phase) => (
          <PhaseCard
            key={phase.id}
            phase={phase}
            onSelect={() => dispatch({ type: 'NAVIGATE', screen: { name: 'materials', phaseId: phase.id } })}
          />
        ))}
      </div>

      <CartFab hasNavBelow />
    </div>
  )
}
