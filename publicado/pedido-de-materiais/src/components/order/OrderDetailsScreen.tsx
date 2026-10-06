import { useState, type FormEvent } from 'react'
import { CalendarCheck, AlertTriangle } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { DELIVERY_LOCATION_SUGGESTIONS } from '../../data/obra'
import type { UrgencyLevel } from '../../types/models'
import { todayIso } from '../../utils/format'
import { TextField } from '../ui/TextField'
import { TextAreaField } from '../ui/TextAreaField'
import { ChipSelect } from '../ui/ChipSelect'
import { Button } from '../ui/Button'
import styles from './OrderDetailsScreen.module.css'

const LOCATION_OPTIONS = DELIVERY_LOCATION_SUGGESTIONS.map((label) => ({ value: label, label }))

export function OrderDetailsScreen() {
  const { state, dispatch } = useAppState()
  const [neededDate, setNeededDate] = useState(state.draft.neededDate)
  const [location, setLocation] = useState(state.draft.location)
  const [urgency, setUrgency] = useState<UrgencyLevel>(state.draft.urgency)
  const [notes, setNotes] = useState(state.draft.notes)
  const [errors, setErrors] = useState<{ neededDate?: string; location?: string }>({})

  const today = todayIso()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nextErrors: typeof errors = {}
    if (!neededDate) nextErrors.neededDate = 'Escolha a data em que o material é necessário.'
    else if (neededDate < today) nextErrors.neededDate = 'A data não pode ser anterior a hoje.'
    if (!location.trim()) nextErrors.location = 'Informe onde o material deve ser entregue.'

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }

    dispatch({
      type: 'UPDATE_DRAFT_DETAILS',
      details: { neededDate, location: location.trim(), urgency, notes: notes.trim() },
    })
    dispatch({ type: 'NAVIGATE', screen: { name: 'review' } })
  }

  return (
    <form className={styles.page} onSubmit={handleSubmit}>
      <TextField
        id="needed-date"
        label="Data em que o material é necessário"
        type="date"
        min={today}
        value={neededDate}
        onChange={(event) => {
          setNeededDate(event.target.value)
          if (errors.neededDate) setErrors((current) => ({ ...current, neededDate: undefined }))
        }}
        error={errors.neededDate}
        required
      />

      <div className={styles.field}>
        <TextField
          id="delivery-location"
          label="Local de entrega na obra"
          value={location}
          onChange={(event) => {
            setLocation(event.target.value)
            if (errors.location) setErrors((current) => ({ ...current, location: undefined }))
          }}
          placeholder="Ex.: Almoxarifado"
          error={errors.location}
          required
        />
        <ChipSelect
          options={LOCATION_OPTIONS}
          value={LOCATION_OPTIONS.some((option) => option.value === location) ? location : ''}
          onChange={setLocation}
          ariaLabel="Sugestões de local de entrega"
          scrollable
        />
      </div>

      <div className={styles.field}>
        <span className={styles.label}>Urgência</span>
        <div className={styles.urgencyGrid}>
          <button
            type="button"
            className={`${styles.urgencyOption} ${urgency === 'normal' ? styles.urgencyOptionActive : ''}`}
            aria-pressed={urgency === 'normal'}
            onClick={() => setUrgency('normal')}
          >
            <CalendarCheck size={26} strokeWidth={2.25} aria-hidden="true" />
            Normal
          </button>
          <button
            type="button"
            className={`${styles.urgencyOption} ${styles.urgencyOptionDanger} ${urgency === 'urgente' ? styles.urgencyOptionActive : ''}`}
            aria-pressed={urgency === 'urgente'}
            onClick={() => setUrgency('urgente')}
          >
            <AlertTriangle size={26} strokeWidth={2.25} aria-hidden="true" />
            Urgente
          </button>
        </div>
      </div>

      <TextAreaField
        id="order-notes"
        label="Observações (opcional)"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
        placeholder="Alguma informação extra para o escritório?"
      />

      <Button type="submit" fullWidth>
        Continuar para revisão
      </Button>
    </form>
  )
}
