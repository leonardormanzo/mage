import { useState, type FormEvent } from 'react'
import { useAppState } from '../../state/AppStateContext'
import { Sheet } from '../ui/Sheet'
import { TextField } from '../ui/TextField'
import { Button } from '../ui/Button'
import styles from './RenameSheet.module.css'

type Props = {
  isOpen: boolean
  onClose: () => void
}

export function RenameSheet({ isOpen, onClose }: Props) {
  const { state, dispatch } = useAppState()
  const [name, setName] = useState(state.workerName ?? '')
  const [error, setError] = useState<string>()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (trimmed.length < 2) {
      setError('Digite um nome válido.')
      return
    }
    dispatch({ type: 'SET_WORKER_NAME', name: trimmed })
    onClose()
  }

  return (
    <Sheet isOpen={isOpen} onClose={onClose} title="Trocar nome">
      <form className={styles.form} onSubmit={handleSubmit}>
        <TextField
          id="rename-worker"
          label="Seu nome"
          value={name}
          onChange={(event) => {
            setName(event.target.value)
            if (error) setError(undefined)
          }}
          autoFocus
          error={error}
          required
        />
        <Button type="submit" fullWidth>
          Salvar
        </Button>
      </form>
    </Sheet>
  )
}
