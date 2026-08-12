import { ClipboardList } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { EmptyState } from '../ui/EmptyState'
import { OrderCard } from './OrderCard'
import styles from './MyOrdersScreen.module.css'

export function MyOrdersScreen() {
  const { state, dispatch } = useAppState()
  const orders = [...state.orders].sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Meus pedidos</h1>

      {orders.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="Nenhum pedido ainda"
          description="Os pedidos que você fizer vão aparecer aqui."
        />
      ) : (
        <div className={styles.list}>
          {orders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onView={() => dispatch({ type: 'NAVIGATE', screen: { name: 'order-detail', orderId: order.id } })}
            />
          ))}
        </div>
      )}
    </div>
  )
}
