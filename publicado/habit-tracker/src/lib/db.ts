import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { Habit, DailyLog, WeeklyTodo } from '../types'

interface HabitTrackerDB extends DBSchema {
  habits: {
    key: string
    value: Habit
  }
  logs: {
    key: string
    value: DailyLog
    indexes: { 'by-habit': string; 'by-date': string }
  }
  weeklyTodos: {
    key: string
    value: WeeklyTodo
    indexes: { 'by-week': string }
  }
}

const DB_NAME = 'habit-tracker'
const DB_VERSION = 1

let dbPromise: Promise<IDBPDatabase<HabitTrackerDB>> | undefined

function getDb(): Promise<IDBPDatabase<HabitTrackerDB>> {
  if (!dbPromise) {
    dbPromise = openDB<HabitTrackerDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        db.createObjectStore('habits', { keyPath: 'id' })

        const logs = db.createObjectStore('logs', { keyPath: 'id' })
        logs.createIndex('by-habit', 'habitId')
        logs.createIndex('by-date', 'date')

        const todos = db.createObjectStore('weeklyTodos', { keyPath: 'id' })
        todos.createIndex('by-week', 'weekStart')
      },
    })
  }
  return dbPromise
}

export async function getAllHabits(): Promise<Habit[]> {
  const db = await getDb()
  return db.getAll('habits')
}

export async function putHabit(habit: Habit): Promise<void> {
  const db = await getDb()
  await db.put('habits', habit)
}

export async function deleteHabit(id: string): Promise<void> {
  const db = await getDb()
  const tx = db.transaction(['habits', 'logs'], 'readwrite')
  await tx.objectStore('habits').delete(id)
  const logIndex = tx.objectStore('logs').index('by-habit')
  let cursor = await logIndex.openCursor(id)
  while (cursor) {
    await cursor.delete()
    cursor = await cursor.continue()
  }
  await tx.done
}

export async function getAllLogs(): Promise<DailyLog[]> {
  const db = await getDb()
  return db.getAll('logs')
}

export async function putLog(log: DailyLog): Promise<void> {
  const db = await getDb()
  await db.put('logs', log)
}

export async function getAllWeeklyTodos(): Promise<WeeklyTodo[]> {
  const db = await getDb()
  return db.getAll('weeklyTodos')
}

export async function putWeeklyTodo(todo: WeeklyTodo): Promise<void> {
  const db = await getDb()
  await db.put('weeklyTodos', todo)
}

export async function deleteWeeklyTodo(id: string): Promise<void> {
  const db = await getDb()
  await db.delete('weeklyTodos', id)
}
