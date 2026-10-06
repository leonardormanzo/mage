import styles from './QuantityField.module.css'

type Props = {
  id: string
  label: string
  unit: string
  value: string
  onChange: (value: string) => void
  allowDecimal: boolean
  error?: string
  autoFocus?: boolean
}

export function QuantityField({ id, label, unit, value, onChange, allowDecimal, error, autoFocus }: Props) {
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <div className={`${styles.inputRow} ${error ? styles.inputRowError : ''}`}>
        <input
          id={id}
          type="text"
          inputMode={allowDecimal ? 'decimal' : 'numeric'}
          autoFocus={autoFocus}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={styles.input}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          placeholder="0"
        />
        <span className={styles.unit}>{unit}</span>
      </div>
      {error && (
        <p id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
