import type { HabitColor } from '../types'

export const HABIT_COLORS: HabitColor[] = ['green', 'amber', 'blue', 'pink', 'purple']

interface ColorTokens {
  dot: string
  fill: string
  ring: string
  text: string
}

const COLOR_MAP: Record<HabitColor, ColorTokens> = {
  green: { dot: 'bg-emerald-500', fill: '#22c55e', ring: 'ring-emerald-500', text: 'text-emerald-400' },
  amber: { dot: 'bg-amber-500', fill: '#f59e0b', ring: 'ring-amber-500', text: 'text-amber-400' },
  blue: { dot: 'bg-sky-500', fill: '#0ea5e9', ring: 'ring-sky-500', text: 'text-sky-400' },
  pink: { dot: 'bg-pink-500', fill: '#ec4899', ring: 'ring-pink-500', text: 'text-pink-400' },
  purple: { dot: 'bg-violet-500', fill: '#8b5cf6', ring: 'ring-violet-500', text: 'text-violet-400' },
}

export function colorTokens(color: HabitColor): ColorTokens {
  return COLOR_MAP[color]
}
