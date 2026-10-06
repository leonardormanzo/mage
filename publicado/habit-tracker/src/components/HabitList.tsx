import { useState, type FormEvent } from 'react'
import { useHabitStore } from '../store/useHabitStore'
import { colorTokens, HABIT_COLORS } from '../lib/colors'
import { currentStreak } from '../lib/stats'
import { todayKey } from '../lib/dates'
import type { HabitColor } from '../types'

export function HabitList() {
  const habits = useHabitStore((state) => state.habits)
  const logs = useHabitStore((state) => state.logs)
  const addHabit = useHabitStore((state) => state.addHabit)
  const removeHabit = useHabitStore((state) => state.removeHabit)
  const toggleLog = useHabitStore((state) => state.toggleLog)

  const [name, setName] = useState('')
  const [color, setColor] = useState<HabitColor>('green')
  const [isFormOpen, setIsFormOpen] = useState(false)

  const today = todayKey()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    void addHabit(trimmed, color, 7)
    setName('')
    setColor('green')
    setIsFormOpen(false)
  }

  return (
    <section className="bg-surface border border-border rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-lg font-semibold">Hábitos</h2>
        <button
          type="button"
          onClick={() => setIsFormOpen((open) => !open)}
          className="cursor-pointer text-sm px-3 py-1.5 rounded-lg bg-accent-soft text-emerald-400 hover:bg-accent/20 transition-colors duration-150"
        >
          {isFormOpen ? 'Cancelar' : '+ Novo hábito'}
        </button>
      </div>

      {isFormOpen ? (
        <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3">
          <input
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Nome do hábito"
            className="bg-bg border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent"
          />
          <div className="flex items-center gap-2">
            {HABIT_COLORS.map((option) => (
              <button
                key={option}
                type="button"
                aria-label={`Cor ${option}`}
                onClick={() => setColor(option)}
                className={`cursor-pointer size-9 rounded-full ${colorTokens(option).dot} ${
                  color === option ? 'ring-2 ring-offset-2 ring-offset-surface ' + colorTokens(option).ring : ''
                }`}
              />
            ))}
          </div>
          <button
            type="submit"
            className="cursor-pointer self-start text-sm px-3 py-1.5 rounded-lg bg-accent text-bg font-medium hover:opacity-90 transition-opacity duration-150"
          >
            Adicionar
          </button>
        </form>
      ) : null}

      {habits.length === 0 ? (
        <p className="text-sm text-text-muted">Nenhum hábito ainda. Crie o primeiro acima.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {habits.map((habit) => {
            const tokens = colorTokens(habit.color)
            const streak = currentStreak(habit.id, logs)
            const isDoneToday = logs.some(
              (log) => log.habitId === habit.id && log.date === today && log.completed,
            )

            return (
              <li
                key={habit.id}
                className="flex items-center gap-3 rounded-xl border border-border px-3 py-2.5 hover:bg-surface-hover transition-colors duration-150"
              >
                <button
                  type="button"
                  onClick={() => void toggleLog(habit.id, today)}
                  aria-pressed={isDoneToday}
                  aria-label={`Marcar ${habit.name} como concluído hoje`}
                  className={`cursor-pointer size-10 rounded-full border-2 shrink-0 transition-colors duration-150 ${
                    isDoneToday ? `${tokens.dot} border-transparent` : 'border-border'
                  }`}
                />
                <span className={`size-2 rounded-full shrink-0 ${tokens.dot}`} />
                <span className="flex-1 text-sm truncate">{habit.name}</span>
                {streak > 0 ? (
                  <span className="text-xs text-streak font-medium whitespace-nowrap">🔥 {streak}d</span>
                ) : null}
                <button
                  type="button"
                  onClick={() => void removeHabit(habit.id)}
                  aria-label={`Remover ${habit.name}`}
                  className="cursor-pointer text-text-muted hover:text-danger transition-colors duration-150 text-xs px-2 py-2"
                >
                  remover
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
