import type { ScreenState } from '../../state/screens'
import { HomeScreen } from '../home/HomeScreen'
import { PhaseSelectScreen } from '../order/PhaseSelectScreen'
import { MaterialsScreen } from '../order/MaterialsScreen'
import { OrderDetailsScreen } from '../order/OrderDetailsScreen'
import { ReviewScreen } from '../order/ReviewScreen'
import { SuccessScreen } from '../order/SuccessScreen'
import { MyOrdersScreen } from '../myorders/MyOrdersScreen'
import { OrderDetailScreen } from '../myorders/OrderDetailScreen'

type Props = {
  screen: ScreenState
}

export function ScreenRouter({ screen }: Props) {
  switch (screen.name) {
    case 'home':
      return <HomeScreen />
    case 'phase-select':
      return <PhaseSelectScreen />
    case 'materials':
      return <MaterialsScreen phaseId={screen.phaseId} />
    case 'order-details':
      return <OrderDetailsScreen />
    case 'review':
      return <ReviewScreen />
    case 'success':
      return <SuccessScreen orderId={screen.orderId} />
    case 'my-orders':
      return <MyOrdersScreen />
    case 'order-detail':
      return <OrderDetailScreen orderId={screen.orderId} />
    case 'onboarding':
      return null
    default:
      return null
  }
}
