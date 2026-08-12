import type { Order, OrderDraft, OrderItem, UrgencyLevel } from '../types/models'
import { createEmptyDraft } from '../types/models'
import type { ScreenState } from './screens'
import { STORAGE_KEYS } from './storageKeys'
import { readJson } from '../utils/storage'
import { buildSeedOrders, SEED_ORDER_COUNT } from '../data/seedOrders'
import { formatOrderNumber } from '../utils/format'

export interface AppState {
  workerName: string | null
  orders: Order[]
  draft: OrderDraft
  orderSeq: number
  isOnlineSim: boolean
  history: ScreenState[]
}

export type Action =
  | { type: 'SET_WORKER_NAME'; name: string }
  | { type: 'NAVIGATE'; screen: ScreenState }
  | { type: 'GO_BACK' }
  | { type: 'SWITCH_TAB'; screen: ScreenState }
  | { type: 'ADD_ITEM'; item: OrderItem }
  | { type: 'UPDATE_ITEM_QUANTITY'; itemId: string; quantity: number }
  | { type: 'REMOVE_ITEM'; itemId: string }
  | {
      type: 'UPDATE_DRAFT_DETAILS'
      details: Partial<{ neededDate: string; location: string; urgency: UrgencyLevel; notes: string }>
    }
  | { type: 'CONFIRM_ORDER'; orderId: string; createdAt: string }
  | { type: 'DISCARD_DRAFT' }
  | { type: 'SET_ONLINE_SIM'; isOnline: boolean }

export function currentScreen(state: AppState): ScreenState {
  return state.history[state.history.length - 1]
}

export function cartItemCount(draft: OrderDraft): number {
  return draft.items.length
}

function sameScreen(a: ScreenState, b: ScreenState): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

function pushScreen(history: ScreenState[], screen: ScreenState): ScreenState[] {
  if (sameScreen(history[history.length - 1], screen)) return history
  return [...history, screen]
}

export function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_WORKER_NAME': {
      const name = action.name.trim()
      if (!name) return state
      const alreadyPastOnboarding = state.history.some((screen) => screen.name !== 'onboarding')
      return {
        ...state,
        workerName: name,
        history: alreadyPastOnboarding ? state.history : [{ name: 'home' }],
      }
    }

    case 'NAVIGATE':
      return { ...state, history: pushScreen(state.history, action.screen) }

    case 'GO_BACK':
      return state.history.length > 1 ? { ...state, history: state.history.slice(0, -1) } : state

    case 'SWITCH_TAB':
      return { ...state, history: [action.screen] }

    case 'ADD_ITEM': {
      const incoming = action.item
      const existingIndex =
        incoming.materialId === null
          ? -1
          : state.draft.items.findIndex((existing) => existing.materialId === incoming.materialId)

      const items =
        existingIndex === -1
          ? [...state.draft.items, incoming]
          : state.draft.items.map((existing, index) =>
              index === existingIndex
                ? { ...existing, quantity: existing.quantity + incoming.quantity }
                : existing,
            )

      return { ...state, draft: { ...state.draft, items } }
    }

    case 'UPDATE_ITEM_QUANTITY':
      return {
        ...state,
        draft: {
          ...state.draft,
          items: state.draft.items.map((item) =>
            item.id === action.itemId ? { ...item, quantity: action.quantity } : item,
          ),
        },
      }

    case 'REMOVE_ITEM':
      return {
        ...state,
        draft: { ...state.draft, items: state.draft.items.filter((item) => item.id !== action.itemId) },
      }

    case 'UPDATE_DRAFT_DETAILS':
      return { ...state, draft: { ...state.draft, ...action.details } }

    case 'CONFIRM_ORDER': {
      if (state.draft.items.length === 0 || !state.workerName) return state
      const order: Order = {
        id: action.orderId,
        number: formatOrderNumber(state.orderSeq + 1),
        createdAt: action.createdAt,
        requesterName: state.workerName,
        items: state.draft.items,
        neededDate: state.draft.neededDate,
        location: state.draft.location,
        urgency: state.draft.urgency,
        notes: state.draft.notes,
        status: 'solicitado',
        pendingSync: !state.isOnlineSim,
      }
      return {
        ...state,
        orders: [order, ...state.orders],
        orderSeq: state.orderSeq + 1,
        draft: createEmptyDraft(),
        history: [{ name: 'success', orderId: order.id }],
      }
    }

    case 'DISCARD_DRAFT':
      return { ...state, draft: createEmptyDraft() }

    case 'SET_ONLINE_SIM': {
      if (!action.isOnline) return { ...state, isOnlineSim: false }
      return {
        ...state,
        isOnlineSim: true,
        orders: state.orders.map((order) => (order.pendingSync ? { ...order, pendingSync: false } : order)),
      }
    }

    default:
      return state
  }
}

export function initAppState(): AppState {
  const workerName = readJson<string | null>(STORAGE_KEYS.workerName, null)
  const storedOrders = readJson<Order[] | null>(STORAGE_KEYS.orders, null)
  const orders = storedOrders ?? buildSeedOrders()
  const orderSeq = readJson<number>(STORAGE_KEYS.orderSeq, SEED_ORDER_COUNT)
  const draft = readJson<OrderDraft>(STORAGE_KEYS.draft, createEmptyDraft())
  const isOnlineSim = readJson<boolean>(STORAGE_KEYS.connectivity, true)
  const rootScreen: ScreenState = workerName ? { name: 'home' } : { name: 'onboarding' }

  return {
    workerName,
    orders,
    draft,
    orderSeq,
    isOnlineSim,
    history: [rootScreen],
  }
}
