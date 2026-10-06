import { useEffect } from 'react'
import { useHabitStore } from './store/useHabitStore'
import { HabitList } from './components/HabitList'
import { DailyGrid } from './components/DailyGrid'
import { Analytics } from './components/Analytics'
import { WeeklyTodos } from './components/WeeklyTodos'

function App() {
  const isLoaded = useHabitStore((state) => state.isLoaded)
  const loadAll = useHabitStore((state) => state.loadAll)

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const today = new Date().toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })

  return (
    <div className="min-h-screen bg-bg text-text">
      <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col gap-6">
        <header>
          <p className="text-sm text-text-muted capitalize">{today}</p>
          <h1 className="font-heading text-2xl font-bold">Habit Tracker</h1>
        </header>

        {!isLoaded ? (
          <p className="text-sm text-text-muted">Carregando dados locais…</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            <div className="flex flex-col gap-6">
              <HabitList />
              <DailyGrid />
            </div>
            <div className="flex flex-col gap-6">
              <Analytics />
              <WeeklyTodos />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
