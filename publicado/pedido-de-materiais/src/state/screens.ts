export type ScreenState =
  | { name: 'onboarding' }
  | { name: 'home' }
  | { name: 'phase-select' }
  | { name: 'materials'; phaseId: string }
  | { name: 'order-details' }
  | { name: 'review' }
  | { name: 'success'; orderId: string }
  | { name: 'my-orders' }
  | { name: 'order-detail'; orderId: string }

export type TabName = 'home' | 'order' | 'my-orders'

export function screenTab(screen: ScreenState): TabName {
  switch (screen.name) {
    case 'home':
    case 'onboarding':
      return 'home'
    case 'my-orders':
    case 'order-detail':
      return 'my-orders'
    default:
      return 'order'
  }
}

const BACK_HEADER_TITLES: Partial<Record<ScreenState['name'], string>> = {
  materials: 'Escolha os materiais',
  'order-details': 'Dados do pedido',
  review: 'Revise seu pedido',
  'order-detail': 'Detalhes do pedido',
}

/** Telas com cabeçalho de "voltar + título" (em vez do topo padrão com nav inferior). */
export function backHeaderTitle(screen: ScreenState): string | null {
  return BACK_HEADER_TITLES[screen.name] ?? null
}

/** Só as etapas do fluxo "Pedir material" contam para a barra de progresso. */
export const WIZARD_STEP_ORDER: ReadonlyArray<ScreenState['name']> = ['materials', 'order-details', 'review']

export function wizardStepIndex(screen: ScreenState): number {
  return WIZARD_STEP_ORDER.indexOf(screen.name)
}

/** Raiz das 3 abas (Início / Pedir material / Meus pedidos) — mantém a nav inferior. */
export function hasBottomNav(screen: ScreenState): boolean {
  return screen.name === 'home' || screen.name === 'phase-select' || screen.name === 'my-orders'
}
