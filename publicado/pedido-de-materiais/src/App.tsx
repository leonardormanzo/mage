import { AppStateProvider } from './state/AppStateContext'
import { ToastProvider } from './state/ToastContext'
import { Shell } from './components/layout/Shell'
import { ToastViewport } from './components/ui/ToastViewport'

function App() {
  return (
    <AppStateProvider>
      <ToastProvider>
        <Shell />
        <ToastViewport />
      </ToastProvider>
    </AppStateProvider>
  )
}

export default App
