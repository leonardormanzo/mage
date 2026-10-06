import { useState, type FormEvent } from 'react'
import type { OrderItem } from '../../types/models'
import { COMMON_UNITS } from '../../types/models'
import { unitAllowsDecimal } from '../../data/catalog'
import { parseQuantityInput } from '../../utils/format'
import { generateId } from '../../utils/id'
import { Sheet } from '../ui/Sheet'
import { TextField } from '../ui/TextField'
import { TextAreaField } from '../ui/TextAreaField'
import { QuantityField } from '../ui/QuantityField'
import { ChipSelect } from '../ui/ChipSelect'
import { Button } from '../ui/Button'
import styles from './CustomMaterialSheet.module.css'

type Props = {
  isOpen: boolean
  onClose: () => void
  phaseId: string
  phaseName: string
  onAdd: (item: OrderItem) => void
}

const UNIT_OPTIONS = COMMON_UNITS.map((unit) => ({ value: unit, label: unit }))

export function CustomMaterialSheet({ isOpen, onClose, phaseId, phaseName, onAdd }: Props) {
  const [name, setName] = useState('')
  const [unit, setUnit] = useState<string>('unidade')
  const [quantity, setQuantity] = useState('')
  const [category, setCategory] = useState('')
  const [note, setNote] = useState('')
  const [errors, setErrors] = useState<{ name?: string; quantity?: string }>({})

  function resetForm() {
    setName('')
    setUnit('unidade')
    setQuantity('')
    setCategory('')
    setNote('')
    setErrors({})
  }

  function handleClose() {
    resetForm()
    onClose()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const allowsDecimal = unitAllowsDecimal(unit)
    const parsedQuantity = parseQuantityInput(quantity)

    const nextErrors: typeof errors = {}
    if (name.trim().length < 2) nextErrors.name = 'Digite o nome do material.'
    if (parsedQuantity === null) nextErrors.quantity = 'Digite uma quantidade válida.'
    else if (!allowsDecimal && !Number.isInteger(parsedQuantity)) {
      nextErrors.quantity = `Use um número inteiro para "${unit}".`
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }

    const item: OrderItem = {
      id: generateId(),
      materialId: null,
      name: name.trim(),
      unit,
      quantity: parsedQuantity as number,
      isCustom: true,
      phaseId,
      categoryName: category.trim() || undefined,
      note: note.trim() || undefined,
    }

    onAdd(item)
    resetForm()
    onClose()
  }

  return (
    <Sheet isOpen={isOpen} onClose={handleClose} title="Escrever outro material">
      <form className={styles.form} onSubmit={handleSubmit}>
        <p className={styles.phaseTag}>Fase: {phaseName}</p>

        <TextField
          id="custom-material-name"
          label="Nome do material"
          value={name}
          onChange={(event) => {
            setName(event.target.value)
            if (errors.name) setErrors((current) => ({ ...current, name: undefined }))
          }}
          placeholder="Ex.: Parafuso especial"
          autoFocus
          error={errors.name}
          required
        />

        <div className={styles.field}>
          <span className={styles.label}>Unidade</span>
          <ChipSelect options={UNIT_OPTIONS} value={unit} onChange={setUnit} ariaLabel="Unidade do material" scrollable />
        </div>

        <QuantityField
          id="custom-material-quantity"
          label="Quantidade"
          unit={unit}
          value={quantity}
          onChange={(next) => {
            setQuantity(next)
            if (errors.quantity) setErrors((current) => ({ ...current, quantity: undefined }))
          }}
          allowDecimal={unitAllowsDecimal(unit)}
          error={errors.quantity}
        />

        <TextField
          id="custom-material-category"
          label="Categoria (opcional)"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          placeholder="Ex.: Ferragens"
        />

        <TextAreaField
          id="custom-material-note"
          label="Observação (opcional)"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Alguma informação extra sobre esse material?"
        />

        <Button type="submit" fullWidth>
          Adicionar material
        </Button>
      </form>
    </Sheet>
  )
}
