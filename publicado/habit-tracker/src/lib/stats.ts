import { subDays } from 'date-fns'
import type { DailyLog } from '../types'
import { lastNDays, toDateKey, todayKey } from './dates'

function completedDateSet(habitId: string, logs: DailyLog[]): Set<string> {
  const set = new Set<string>()
  for (const log of logs) {
    if (log.habitId === habitId && log.completed) {
      set.add(log.date)
    }
  }
  return set
}

export function currentStreak(habitId: string, logs: DailyLog[]): number {
  const completed = completedDateSet(habitId, logs)
  const today = todayKey()
  let cursor = completed.has(today) ? new Date() : subDays(new Date(), 1)
  let streak = 0

  while (completed.has(toDateKey(cursor))) {
    streak += 1
    cursor = subDays(cursor, 1)
  }

  return streak
}

export function longestStreak(habitId: string, logs: DailyLog[]): number {
  const completed = completedDateSet(habitId, logs)
  if (completed.size === 0) return 0

  const sortedDates = [...completed].sort()
  let longest = 1
  let running = 1

  for (let i = 1; i < sortedDates.length; i += 1) {
    const prev = new Date(`${sortedDates[i - 1]}T00:00:00`)
    const curr = new Date(`${sortedDates[i]}T00:00:00`)
    const diffDays = Math.round((curr.getTime() - prev.getTime()) / 86_400_000)
    running = diffDays === 1 ? running + 1 : 1
    longest = Math.max(longest, running)
  }

  return longest
}

export function completionRate(habitId: string, logs: DailyLog[], days: number): number {
  const window = new Set(lastNDays(days))
  const completed = completedDateSet(habitId, logs)
  let hits = 0
  for (const day of window) {
    if (completed.has(day)) hits += 1
  }
  return hits / days
}

export function todayCompletionRate(habitIds: string[], logs: DailyLog[]): number {
  if (habitIds.length === 0) return 0
  const today = todayKey()
  const doneToday = logs.filter((log) => log.date === today && log.completed)
  const doneHabitIds = new Set(doneToday.map((log) => log.habitId))
  const hits = habitIds.filter((id) => doneHabitIds.has(id)).length
  return hits / habitIds.length
}
