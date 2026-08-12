import type { LucideIcon } from 'lucide-react'
import styles from './ChipSelect.module.css'

export type ChipOption = {
  value: string
  label: string
  icon?: LucideIcon
}

type Props = {
  options: ChipOption[]
  value: string
  onChange: (value: string) => void
  ariaLabel: string
  scrollable?: boolean
}

export function ChipSelect({ options, value, onChange, ariaLabel, scrollable = false }: Props) {
  return (
    <div className={`${styles.row} ${scrollable ? 'scroll-x' : styles.wrap}`} role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const isSelected = option.value === value
        const Icon = option.icon
        return (
          <button
            key={option.value}
            type="button"
            className={`${styles.chip} ${isSelected ? styles.chipSelected : ''}`}
            aria-pressed={isSelected}
            onClick={() => onChange(option.value)}
          >
            {Icon && <Icon size={16} strokeWidth={2.5} aria-hidden="true" />}
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
