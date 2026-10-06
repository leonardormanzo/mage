import { useAppState, useScreen } from '../../state/AppStateContext'
import { screenTab, backHeaderTitle, hasBottomNav, wizardStepIndex, WIZARD_STEP_ORDER } from '../../state/screens'
import { NameGate } from '../onboarding/NameGate'
import { TopBar } from './TopBar'
import { ScreenHeader } from './ScreenHeader'
import { BottomNav } from './BottomNav'
import { OfflineBanner } from './OfflineBanner'
import { ScreenRouter } from './ScreenRouter'
import styles from './Shell.module.css'

export function Shell() {
  const { dispatch } = useAppState()
  const screen = useScreen()

  if (screen.name === 'onboarding') return <NameGate />

  const title = backHeaderTitle(screen)
  const stepIndex = wizardStepIndex(screen)

  return (
    <div className="app-shell">
      {title ? (
        <ScreenHeader
          title={title}
          onBack={() => dispatch({ type: 'GO_BACK' })}
          progress={stepIndex >= 0 ? { currentIndex: stepIndex, totalSteps: WIZARD_STEP_ORDER.length } : undefined}
        />
      ) : (
        <TopBar />
      )}
      <OfflineBanner />
      <main className={styles.main}>
        <ScreenRouter screen={screen} />
      </main>
      {hasBottomNav(screen) && <BottomNav activeTab={screenTab(screen)} />}
    </div>
  )
}
