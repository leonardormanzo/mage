import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useHabitStore } from '../store/useHabitStore'
import { ProgressRing } from './ProgressRing'
import { colorTokens } from '../lib/colors'
import { currentStreak, longestStreak, completionRate, todayCompletionRate } from '../lib/stats'
import { lastNDays, shortLabel } from '../lib/dates'

const WINDOW_DAYS = 7

export function Analytics() {
  const habits = useHabitStore((state) => state.habits)
  const logs = useHabitStore((state) => state.logs)

  const days = lastNDays(WINDOW_DAYS)
  const chartData = days.map((day) => ({
    day: shortLabel(day),
    concluidos: logs.filter((log) => log.date === day && log.completed).length,
  }))

  const overallToday = todayCompletionRate(
    habits.map((habit) => habit.id),
    logs,
  )

  return (
    <section className="bg-surface border border-border rounded-2xl p-5 flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold">Analytics</h2>
        <ProgressRing progress={overallToday} size={64} strokeWidth={6} label="hoje" />
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
            <XAxis
              dataKey="day"
              stroke="#94a3b8"
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis allowDecimals={false} stroke="#94a3b8" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.04)' }}
              contentStyle={{
                background: '#0e1223',
                border: '1px solid #263047',
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: '#f8fafc' }}
            />
            <Bar dataKey="concluidos" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {habits.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {habits.map((habit) => {
            const tokens = colorTokens(habit.color)
            const rate = completionRate(habit.id, logs, WINDOW_DAYS)
            return (
              <li key={habit.id} className="flex items-center gap-3">
                <span className={`size-2 rounded-full shrink-0 ${tokens.dot}`} />
                <span className="flex-1 text-sm truncate">{habit.name}</span>
                <span className="text-xs text-text-muted whitespace-nowrap">
                  streak {currentStreak(habit.id, logs)}d · recorde {longestStreak(habit.id, logs)}d
                </span>
                <span className="text-xs font-medium w-10 text-right">{Math.round(rate * 100)}%</span>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="text-sm text-text-muted">Estatísticas aparecem assim que você tiver hábitos.</p>
      )}
    </section>
  )
}
