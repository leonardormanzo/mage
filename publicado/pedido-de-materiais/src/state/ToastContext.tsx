import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { generateId } from '../utils/id'

export type ToastTone = 'neutral' | 'success' | 'error'

export interface ToastItem {
  id: string
  message: string
  tone: ToastTone
  icon?: LucideIcon
}

interface ShowToastOptions {
  tone?: ToastTone
  icon?: LucideIcon
  durationMs?: number
}

interface ToastContextValue {
  toasts: ToastItem[]
  showToast: (message: string, options?: ShowToastOptions) => void
  dismissToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const DEFAULT_DURATION_MS = 2800

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>>())

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
    const timer = timers.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timers.current.delete(id)
    }
  }, [])

  const showToast = useCallback(
    (message: string, options?: ShowToastOptions) => {
      const id = generateId()
      const toast: ToastItem = { id, message, tone: options?.tone ?? 'neutral', icon: options?.icon }
      setToasts((current) => [...current, toast])
      const timer = setTimeout(() => dismissToast(id), options?.durationMs ?? DEFAULT_DURATION_MS)
      timers.current.set(id, timer)
    },
    [dismissToast],
  )

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>{children}</ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast precisa ser usado dentro de <ToastProvider>')
  return context
}
