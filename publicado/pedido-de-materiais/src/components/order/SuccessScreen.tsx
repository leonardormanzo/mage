import { CheckCircle2, Info } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { Button } from '../ui/Button'
import styles from './SuccessScreen.module.css'

type Props = {
  orderId: string
}

export function SuccessScreen({ orderId }: Props) {
  const { state, dispatch } = useAppState()
  const order = state.orders.find((candidate) => candidate.id === orderId)

  function handleViewOrder() {
    dispatch({ type: 'SWITCH_TAB', screen: { name: 'my-orders' } })
    dispatch({ type: 'NAVIGATE', screen: { name: 'order-detail', orderId } })
  }

  return (
    <div className={styles.page}>
      <div className={styles.iconWrap} aria-hidden="true">
        <CheckCircle2 size={48} strokeWidth={2} />
      </div>
      <h1 className={styles.title}>Pedido enviado!</h1>
      {order && <p className={styles.orderNumber}>Pedido {order.number}</p>}
      <p className={styles.message}>Pedido registrado neste protótipo.</p>

      <div className={styles.disclaimer}>
        <Info size={16} aria-hidden="true" />
        <p>Integração com o sistema do escritório: simulada nesta versão.</p>
      </div>

      <div className={styles.actions}>
        <Button fullWidth onClick={handleViewOrder}>
          Ver meu pedido
        </Button>
        <Button
          variant="secondary"
          fullWidth
          onClick={() => dispatch({ type: 'SWITCH_TAB', screen: { name: 'home' } })}
        >
          Voltar ao início
        </Button>
      </div>
    </div>
  )
}
