import { Search, X } from 'lucide-react'
import styles from './SearchInput.module.css'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  ariaLabel: string
}

export function SearchInput({ value, onChange, placeholder = 'Buscar material', ariaLabel }: Props) {
  return (
    <div className={styles.wrapper}>
      <Search size={20} className={styles.icon} aria-hidden="true" />
      <input
        type="search"
        inputMode="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={ariaLabel}
        className={styles.input}
      />
      {value && (
        <button type="button" className={styles.clear} onClick={() => onChange('')} aria-label="Limpar busca">
          <X size={18} aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
