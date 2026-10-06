import { ArrowLeft } from 'lucide-react'
import { ProgressSteps } from '../ui/ProgressSteps'
import styles from './ScreenHeader.module.css'

type Props = {
  title: string
  onBack: () => void
  progress?: { currentIndex: number; totalSteps: number }
}

export function ScreenHeader({ title, onBack, progress }: Props) {
  return (
    <header className={`glass-surface ${styles.header}`}>
      <div className={styles.row}>
        <button type="button" className={styles.backButton} onClick={onBack} aria-label="Voltar">
          <ArrowLeft size={22} strokeWidth={2.25} aria-hidden="true" />
        </button>
        <h1 className={styles.title}>{title}</h1>
        <span className={styles.spacer} aria-hidden="true" />
      </div>
      {progress && (
        <div className={styles.progressWrap}>
          <ProgressSteps currentIndex={progress.currentIndex} totalSteps={progress.totalSteps} />
        </div>
      )}
    </header>
  )
}
