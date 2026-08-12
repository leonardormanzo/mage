import { useHabitStore } from '../store/useHabitStore'
import { colorTokens } from '../lib/colors'
import { currentWeekDays, todayKey, weekdayLabel } from '../lib/dates'

export function DailyGrid() {
  const habits = useHabitStore((state) => state.habits)
  const logs = useHabitStore((state) => state.logs)
  const toggleLog = useHabitStore((state) => state.toggleLog)

  const days = currentWeekDays()
  const today = todayKey()

  if (habits.length === 0) {
    return (
      <section className="bg-surface border border-border rounded-2xl p-5">
        <h2 className="font-heading text-lg font-semibold mb-2">Semana</h2>
        <p className="text-sm text-text-muted">Adicione hábitos para ver a grade semanal.</p>
      </section>
    )
  }

  return (
    <section className="bg-surface border border-border rounded-2xl p-5 overflow-x-auto">
      <h2 className="font-heading text-lg font-semibold mb-4">Semana</h2>
      <table className="w-full min-w-[460px] border-separate border-spacing-y-2">
        <thead>
          <tr>
            <th className="text-left text-xs font-medium text-text-muted pb-1">Hábito</th>
            {days.map((day) => (
              <th
                key={day}
                className={`text-xs font-medium pb-1 w-11 ${day === today ? 'text-accent' : 'text-text-muted'}`}
              >
                {weekdayLabel(day)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {habits.map((habit) => {
            const tokens = colorTokens(habit.color)
            return (
              <tr key={habit.id}>
                <td className="text-sm pr-3 py-1 truncate max-w-[140px]">{habit.name}</td>
                {days.map((day) => {
                  const isCompleted = logs.some(
                    (log) => log.habitId === habit.id && log.date === day && log.completed,
                  )
                  return (
                    <td key={day} className="text-center">
                      <button
                        type="button"
                        onClick={() => void toggleLog(habit.id, day)}
                        aria-pressed={isCompleted}
                        aria-label={`${habit.name} em ${day}`}
                        className={`cursor-pointer size-10 rounded-md border transition-colors duration-150 ${
                          isCompleted
                            ? `${tokens.dot} border-transparent`
                            : 'bg-bg border-border hover:border-text-muted'
                        } ${day === today ? 'ring-1 ring-offset-1 ring-offset-surface ring-text-muted' : ''}`}
                      />
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}
