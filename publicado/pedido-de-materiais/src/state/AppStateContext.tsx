import { createContext, useContext, useEffect, useReducer, type Dispatch, type ReactNode } from 'react'
import { appReducer, initAppState, currentScreen, type AppState, type Action } from './appReducer'
import type { ScreenState } from './screens'
import { STORAGE_KEYS } from './storageKeys'
import { writeJson } from '../utils/storage'

interface AppContextValue {
  state: AppState
  dispatch: Dispatch<Action>
}

const AppStateContext = createContext<AppContextValue | null>(null)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, undefined, initAppState)

  useEffect(() => {
    if (!state.workerName) return
    writeJson(STORAGE_KEYS.workerName, state.workerName)
  }, [state.workerName])

  useEffect(() => {
    writeJson(STORAGE_KEYS.orders, state.orders)
  }, [state.orders])

  useEffect(() => {
    writeJson(STORAGE_KEYS.draft, state.draft)
  }, [state.draft])

  useEffect(() => {
    writeJson(STORAGE_KEYS.orderSeq, state.orderSeq)
  }, [state.orderSeq])

  useEffect(() => {
    writeJson(STORAGE_KEYS.connectivity, state.isOnlineSim)
  }, [state.isOnlineSim])

  useEffect(() => {
    const hasUnsavedOrder = state.draft.items.length > 0
    if (!hasUnsavedOrder) return

    function handleBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault()
      event.returnValue = ''
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [state.draft.items.length])

  return <AppStateContext.Provider value={{ state, dispatch }}>{children}</AppStateContext.Provider>
}

export function useAppState(): AppContextValue {
  const context = useContext(AppStateContext)
  if (!context) throw new Error('useAppState precisa ser usado dentro de <AppStateProvider>')
  return context
}

export function useScreen(): ScreenState {
  const { state } = useAppState()
  return currentScreen(state)
}
