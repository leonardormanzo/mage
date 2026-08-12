import { useState } from 'react'
import { Plus, Check } from 'lucide-react'
import type { MaterialDef } from '../../types/models'
import { getMaterialIcon } from '../../data/materialIcons'
import { parseQuantityInput, formatQuantity } from '../../utils/format'
import { QuantityField } from '../ui/QuantityField'
import { Button } from '../ui/Button'
import styles from './MaterialCard.module.css'

type Props = {
  material: MaterialDef
  categoryName: string
  cartQuantity?: number
  onAdd: (quantity: number) => void
}

export function MaterialCard({ material, categoryName, cartQuantity, onAdd }: Props) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string>()
  const Icon = getMaterialIcon(material.name, categoryName)
  const isInCart = cartQuantity !== undefined

  function handleAdd() {
    const parsed = parseQuantityInput(value)
    if (parsed === null) {
      setError('Digite uma quantidade válida.')
      return
    }
    if (!material.allowsDecimal && !Number.isInteger(parsed)) {
      setError(`Use um número inteiro para "${material.unit}".`)
      return
    }
    onAdd(parsed)
    setValue('')
    setError(undefined)
  }

  return (
    <div className={`${styles.card} ${isInCart ? styles.cardActive : ''}`}>
      <div className={styles.header}>
        <span className={styles.icon} aria-hidden="true">
          <Icon size={22} strokeWidth={2.25} />
        </span>
        <div className={styles.info}>
          <p className={styles.name}>{material.name}</p>
          <p className={styles.unit}>Unidade: {material.unit}</p>
        </div>
      </div>

      {isInCart && (
        <p className={styles.inCartBadge}>
          <Check size={14} strokeWidth={3} aria-hidden="true" />
          {formatQuantity(cartQuantity)} {material.unit} no pedido
        </p>
      )}

      <div className={styles.footer}>
        <QuantityField
          id={`qty-${material.id}`}
          label="Quantidade"
          unit={material.unit}
          value={value}
          onChange={(next) => {
            setValue(next)
            if (error) setError(undefined)
          }}
          allowDecimal={material.allowsDecimal}
          error={error}
        />
        <Button size="md" icon={Plus} onClick={handleAdd}>
          Adicionar
        </Button>
      </div>
    </div>
  )
}
