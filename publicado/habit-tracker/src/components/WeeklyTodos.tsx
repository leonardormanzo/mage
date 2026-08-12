import { useState, type FormEvent } from 'react'
import { useHabitStore } from '../store/useHabitStore'
import { currentWeekStartKey } from '../lib/dates'

export function WeeklyTodos() {
  const weeklyTodos = useHabitStore((state) => state.weeklyTodos)
  const addWeeklyTodo = useHabitStore((state) => state.addWeeklyTodo)
  const toggleWeeklyTodo = useHabitStore((state) => state.toggleWeeklyTodo)
  const removeWeeklyTodo = useHabitStore((state) => state.removeWeeklyTodo)

  const [text, setText] = useState('')

  const weekStart = currentWeekStartKey()
  const thisWeekTodos = weeklyTodos.filter((todo) => todo.weekStart === weekStart)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    void addWeeklyTodo(trimmed)
    setText('')
  }

  return (
    <section className="bg-surface border border-border rounded-2xl p-5">
      <h2 className="font-heading text-lg font-semibold mb-4">Tarefas da semana</h2>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Nova tarefa"
          className="flex-1 bg-bg border border-border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent"
        />
        <button
          type="submit"
          className="cursor-pointer px-3 py-2 rounded-lg bg-accent text-bg text-sm font-medium hover:opacity-90 transition-opacity duration-150"
        >
          Adicionar
        </button>
      </form>

      {thisWeekTodos.length === 0 ? (
        <p className="text-sm text-text-muted">Nenhuma tarefa para esta semana.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {thisWeekTodos.map((todo) => (
            <li
              key={todo.id}
              className="flex items-center gap-3 rounded-xl border border-border px-3 py-2 hover:bg-surface-hover transition-colors duration-150"
            >
              <button
                type="button"
                onClick={() => void toggleWeeklyTodo(todo.id)}
                aria-pressed={todo.done}
                aria-label={`Marcar tarefa ${todo.text} como concluída`}
                className={`cursor-pointer size-8 rounded-md border-2 shrink-0 transition-colors duration-150 ${
                  todo.done ? 'bg-accent border-transparent' : 'border-border'
                }`}
              />
              <span className={`flex-1 text-sm ${todo.done ? 'line-through text-text-muted' : ''}`}>
                {todo.text}
              </span>
              <button
                type="button"
                onClick={() => void removeWeeklyTodo(todo.id)}
                aria-label={`Remover tarefa ${todo.text}`}
                className="cursor-pointer text-text-muted hover:text-danger transition-colors duration-150 text-xs px-2 py-2"
              >
                remover
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
