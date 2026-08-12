import { create } from 'zustand'
import {
  deleteHabit as dbDeleteHabit,
  deleteWeeklyTodo as dbDeleteWeeklyTodo,
  getAllHabits,
  getAllLogs,
  getAllWeeklyTodos,
  putHabit,
  putLog,
  putWeeklyTodo,
} from '../lib/db'
import { currentWeekStartKey } from '../lib/dates'
import { generateId } from '../lib/id'
import type { DailyLog, Habit, HabitColor, WeeklyTodo } from '../types'

interface HabitStoreState {
  habits: Habit[]
  logs: DailyLog[]
  weeklyTodos: WeeklyTodo[]
  isLoaded: boolean
  loadAll: () => Promise<void>
  addHabit: (name: string, color: HabitColor, targetPerWeek: number) => Promise<void>
  removeHabit: (id: string) => Promise<void>
  toggleLog: (habitId: string, date: string) => Promise<void>
  addWeeklyTodo: (text: string) => Promise<void>
  toggleWeeklyTodo: (id: string) => Promise<void>
  removeWeeklyTodo: (id: string) => Promise<void>
}

export const useHabitStore = create<HabitStoreState>((set, get) => ({
  habits: [],
  logs: [],
  weeklyTodos: [],
  isLoaded: false,

  loadAll: async () => {
    try {
      const [habits, logs, weeklyTodos] = await Promise.all([
        getAllHabits(),
        getAllLogs(),
        getAllWeeklyTodos(),
      ])
      set({ habits, logs, weeklyTodos, isLoaded: true })
    } catch (error: unknown) {
      console.error('Falha ao carregar dados do IndexedDB', error)
      set({ isLoaded: true })
    }
  },

  addHabit: async (name, color, targetPerWeek) => {
    const habit: Habit = {
      id: generateId(),
      name,
      color,
      targetPerWeek,
      createdAt: new Date().toISOString(),
      archived: false,
    }
    try {
      await putHabit(habit)
      set({ habits: [...get().habits, habit] })
    } catch (error: unknown) {
      console.error('Falha ao salvar hábito', error)
    }
  },

  removeHabit: async (id) => {
    try {
      await dbDeleteHabit(id)
      set({
        habits: get().habits.filter((habit) => habit.id !== id),
        logs: get().logs.filter((log) => log.habitId !== id),
      })
    } catch (error: unknown) {
      console.error('Falha ao remover hábito', error)
    }
  },

  toggleLog: async (habitId, date) => {
    const existing = get().logs.find((log) => log.habitId === habitId && log.date === date)
    const nextLog: DailyLog = existing
      ? { ...existing, completed: !existing.completed }
      : { id: generateId(), habitId, date, completed: true }

    try {
      await putLog(nextLog)
      set({
        logs: existing
          ? get().logs.map((log) => (log.id === nextLog.id ? nextLog : log))
          : [...get().logs, nextLog],
      })
    } catch (error: unknown) {
      console.error('Falha ao marcar hábito do dia', error)
    }
  },

  addWeeklyTodo: async (text) => {
    const todo: WeeklyTodo = {
      id: generateId(),
      text,
      done: false,
      weekStart: currentWeekStartKey(),
      createdAt: new Date().toISOString(),
    }
    try {
      await putWeeklyTodo(todo)
      set({ weeklyTodos: [...get().weeklyTodos, todo] })
    } catch (error: unknown) {
      console.error('Falha ao salvar tarefa da semana', error)
    }
  },

  toggleWeeklyTodo: async (id) => {
    const existing = get().weeklyTodos.find((todo) => todo.id === id)
    if (!existing) return
    const updated: WeeklyTodo = { ...existing, done: !existing.done }
    try {
      await putWeeklyTodo(updated)
      set({
        weeklyTodos: get().weeklyTodos.map((todo) => (todo.id === id ? updated : todo)),
      })
    } catch (error: unknown) {
      console.error('Falha ao atualizar tarefa da semana', error)
    }
  },

  removeWeeklyTodo: async (id) => {
    try {
      await dbDeleteWeeklyTodo(id)
      set({ weeklyTodos: get().weeklyTodos.filter((todo) => todo.id !== id) })
    } catch (error: unknown) {
      console.error('Falha ao remover tarefa da semana', error)
    }
  },
}))
