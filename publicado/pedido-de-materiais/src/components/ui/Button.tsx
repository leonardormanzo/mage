import type { ButtonHTMLAttributes, ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import styles from './Button.module.css'

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
type Size = 'md' | 'lg'

type Props = {
  children: ReactNode
  variant?: Variant
  size?: Size
  icon?: LucideIcon
  iconPosition?: 'left' | 'right'
  fullWidth?: boolean
  isLoading?: boolean
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'>

export function Button({
  children,
  variant = 'primary',
  size = 'lg',
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  isLoading = false,
  disabled,
  type = 'button',
  ...rest
}: Props) {
  const classNames = [styles.button, styles[variant], styles[size], fullWidth ? styles.fullWidth : '']
    .filter(Boolean)
    .join(' ')

  return (
    <button type={type} className={classNames} disabled={disabled || isLoading} aria-busy={isLoading || undefined} {...rest}>
      {isLoading && <span className={styles.spinner} aria-hidden="true" />}
      {!isLoading && Icon && iconPosition === 'left' && <Icon size={20} strokeWidth={2.25} aria-hidden="true" />}
      <span className={styles.label}>{children}</span>
      {!isLoading && Icon && iconPosition === 'right' && <Icon size={20} strokeWidth={2.25} aria-hidden="true" />}
    </button>
  )
}
