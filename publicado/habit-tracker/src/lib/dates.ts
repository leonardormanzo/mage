import { addDays, format, startOfWeek, subDays } from 'date-fns'

export const DATE_FORMAT = 'yyyy-MM-dd'

export function toDateKey(date: Date): string {
  return format(date, DATE_FORMAT)
}

export function todayKey(): string {
  return toDateKey(new Date())
}

export function currentWeekStartKey(): string {
  return toDateKey(startOfWeek(new Date(), { weekStartsOn: 1 }))
}

export function lastNDays(n: number, endDate: Date = new Date()): string[] {
  const days: string[] = []
  for (let i = n - 1; i >= 0; i -= 1) {
    days.push(toDateKey(subDays(endDate, i)))
  }
  return days
}

export function currentWeekDays(): string[] {
  const start = startOfWeek(new Date(), { weekStartsOn: 1 })
  return Array.from({ length: 7 }, (_, i) => toDateKey(addDays(start, i)))
}

export function weekdayLabel(dateKey: string): string {
  return format(new Date(`${dateKey}T00:00:00`), 'EEEEE')
}

export function shortLabel(dateKey: string): string {
  return format(new Date(`${dateKey}T00:00:00`), 'dd/MM')
}
