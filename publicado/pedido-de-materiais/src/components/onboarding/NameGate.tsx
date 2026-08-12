import { useState, type FormEvent } from 'react'
import { HardHat } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { OBRA } from '../../data/obra'
import { Button } from '../ui/Button'
import { TextField } from '../ui/TextField'
import styles from './NameGate.module.css'

export function NameGate() {
  const { dispatch } = useAppState()
  const [name, setName] = useState('')
  const [error, setError] = useState<string>()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (trimmed.length < 2) {
      setError('Digite seu nome para continuar.')
      return
    }
    dispatch({ type: 'SET_WORKER_NAME', name: trimmed })
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.content}>
        <div className={styles.icon} aria-hidden="true">
          <HardHat size={36} strokeWidth={2.25} />
        </div>
        <h1 className={styles.title}>Bem-vindo à obra</h1>
        <p className={styles.subtitle}>{OBRA.nome}</p>
        <p className={styles.description}>Para começar, diga como podemos te chamar.</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <TextField
            id="worker-name"
            label="Seu nome"
            value={name}
            onChange={(event) => {
              setName(event.target.value)
              if (error) setError(undefined)
            }}
            placeholder="Ex.: Carlos"
            autoFocus
            autoComplete="given-name"
            error={error}
            required
          />
          <Button type="submit" fullWidth>
            Continuar
          </Button>
        </form>
      </div>
    </div>
  )
}
