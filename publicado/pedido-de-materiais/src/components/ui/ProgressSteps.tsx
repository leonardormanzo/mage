import styles from './ProgressSteps.module.css'

type Props = {
  currentIndex: number
  totalSteps: number
}

export function ProgressSteps({ currentIndex, totalSteps }: Props) {
  const stepNumber = Math.min(currentIndex + 1, totalSteps)
  const percent = (stepNumber / totalSteps) * 100

  return (
    <div className={styles.wrapper}>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={stepNumber}
        aria-valuemin={1}
        aria-valuemax={totalSteps}
        aria-label={`Passo ${stepNumber} de ${totalSteps}`}
      >
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
      <span className={styles.label} aria-hidden="true">
        Passo {stepNumber} de {totalSteps}
      </span>
    </div>
  )
}
