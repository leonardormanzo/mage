import { useEffect, useState } from 'react'
import type { OrderItem } from '../../types/models'
import { unitAllowsDecimal } from '../../data/catalog'
import { parseQuantityInput, formatQuantity } from '../../utils/format'
import { Sheet } from '../ui/Sheet'
import { QuantityField } from '../ui/QuantityField'
import { Button } from '../ui/Button'
import styles from './EditQuantitySheet.module.css'

type Props = {
  item: OrderItem | null
  onClose: () => void
  onSave: (quantity: number) => void
}

export function EditQuantitySheet({ item, onClose, onSave }: Props) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string>()

  useEffect(() => {
    if (item) {
      setValue(formatQuantity(item.quantity))
      setError(undefined)
    }
  }, [item])

  function handleSave() {
    if (!item) return
    const parsed = parseQuantityInput(value)
    if (parsed === null) {
      setError('Digite uma quantidade válida.')
      return
    }
    if (!unitAllowsDecimal(item.unit) && !Number.isInteger(parsed)) {
      setError(`Use um número inteiro para "${item.unit}".`)
      return
    }
    onSave(parsed)
  }

  return (
    <Sheet isOpen={item !== null} onClose={onClose} title={item ? `Editar ${item.name}` : undefined}>
      {item && (
        <div className={styles.wrapper}>
          <QuantityField
            id="edit-item-quantity"
            label="Quantidade"
            unit={item.unit}
            value={value}
            onChange={(next) => {
              setValue(next)
              if (error) setError(undefined)
            }}
            allowDecimal={unitAllowsDecimal(item.unit)}
            error={error}
            autoFocus
          />
          <Button fullWidth onClick={handleSave}>
            Salvar alteração
          </Button>
        </div>
      )}
    </Sheet>
  )
}
