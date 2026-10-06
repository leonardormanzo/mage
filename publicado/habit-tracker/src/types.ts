export type HabitColor = 'green' | 'amber' | 'blue' | 'pink' | 'purple'

export type Habit = {
  id: string
  name: string
  color: HabitColor
  targetPerWeek: number
  createdAt: string
  archived: boolean
}

export type DailyLog = {
  id: string
  habitId: string
  date: string
  completed: boolean
}

export type WeeklyTodo = {
  id: string
  text: string
  done: boolean
  weekStart: string
  createdAt: string
}
