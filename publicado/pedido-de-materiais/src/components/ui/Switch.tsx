import styles from './Switch.module.css'

type Props = {
  id: string
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
}

export function Switch({ id, checked, onChange, label }: Props) {
  return (
    <label htmlFor={id} className={styles.wrapper}>
      <span className={styles.label}>{label}</span>
      <span className={styles.track}>
        <input
          id={id}
          type="checkbox"
          role="switch"
          className={styles.input}
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span className={`${styles.pill} ${checked ? styles.pillOn : ''}`} aria-hidden="true">
          <span className={styles.thumb} />
        </span>
      </span>
    </label>
  )
}
