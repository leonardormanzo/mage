import { useState } from 'react'
import { Check, PackagePlus, SearchX } from 'lucide-react'
import { useAppState } from '../../state/AppStateContext'
import { useToast } from '../../state/ToastContext'
import { getPhase, getCategoriesForPhase, searchMaterials } from '../../data/catalog'
import type { MaterialDef, OrderItem } from '../../types/models'
import { generateId } from '../../utils/id'
import { SearchInput } from '../ui/SearchInput'
import { ChipSelect } from '../ui/ChipSelect'
import { EmptyState } from '../ui/EmptyState'
import { Button } from '../ui/Button'
import { MaterialCard } from './MaterialCard'
import { CustomMaterialSheet } from './CustomMaterialSheet'
import { CartFab } from './CartFab'
import styles from './MaterialsScreen.module.css'

type Props = {
  phaseId: string
}

export function MaterialsScreen({ phaseId }: Props) {
  const { state, dispatch } = useAppState()
  const { showToast } = useToast()
  const [query, setQuery] = useState('')
  const [categoryId, setCategoryId] = useState('all')
  const [showCustomSheet, setShowCustomSheet] = useState(false)

  const phase = getPhase(phaseId)
  const categories = getCategoriesForPhase(phaseId)

  if (!phase) return null

  const PhaseIcon = phase.icon
  const results = searchMaterials(phaseId, query, categoryId === 'all' ? undefined : categoryId)
  const categoryOptions = [{ value: 'all', label: 'Todas' }, ...categories.map((c) => ({ value: c.id, label: c.name }))]

  function cartQuantityFor(materialId: string): number | undefined {
    return state.draft.items.find((item) => item.materialId === materialId)?.quantity
  }

  function handleAddMaterial(material: MaterialDef, quantity: number) {
    const alreadyInCart = state.draft.items.some((item) => item.materialId === material.id)
    const category = categories.find((c) => c.id === material.categoryId)
    dispatch({
      type: 'ADD_ITEM',
      item: {
        id: generateId(),
        materialId: material.id,
        name: material.name,
        unit: material.unit,
        quantity,
        isCustom: false,
        phaseId,
        categoryName: category?.name,
      },
    })
    showToast(
      alreadyInCart ? `${material.name}: quantidade atualizada no pedido.` : `${material.name} adicionado ao pedido.`,
      { tone: 'success', icon: Check },
    )
  }

  function handleAddCustom(item: OrderItem) {
    dispatch({ type: 'ADD_ITEM', item })
    showToast(`${item.name} adicionado ao pedido.`, { tone: 'success', icon: Check })
  }

  return (
    <div className={styles.page}>
      <div className={styles.phaseHeading}>
        <span className={styles.phaseIcon} style={{ background: phase.color }} aria-hidden="true">
          <PhaseIcon size={20} strokeWidth={2.25} />
        </span>
        <h1 className={styles.title}>{phase.name}</h1>
      </div>

      <SearchInput value={query} onChange={setQuery} ariaLabel={`Buscar material em ${phase.name}`} placeholder="Buscar material…" />

      <ChipSelect options={categoryOptions} value={categoryId} onChange={setCategoryId} ariaLabel="Filtrar por categoria" scrollable />

      <button type="button" className={styles.customCta} onClick={() => setShowCustomSheet(true)}>
        <PackagePlus size={18} strokeWidth={2.25} aria-hidden="true" />
        Não encontrou? Escrever outro material
      </button>

      {results.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="Nenhum material encontrado"
          description={query ? `Não encontramos nada para "${query}" nessa categoria.` : 'Nada por aqui nessa categoria.'}
          action={
            <Button variant="secondary" onClick={() => setShowCustomSheet(true)}>
              Escrever outro material
            </Button>
          }
        />
      ) : (
        <div className={styles.list}>
          {results.map((material) => (
            <MaterialCard
              key={material.id}
              material={material}
              categoryName={categories.find((c) => c.id === material.categoryId)?.name ?? ''}
              cartQuantity={cartQuantityFor(material.id)}
              onAdd={(quantity) => handleAddMaterial(material, quantity)}
            />
          ))}
        </div>
      )}

      <CustomMaterialSheet
        isOpen={showCustomSheet}
        onClose={() => setShowCustomSheet(false)}
        phaseId={phaseId}
        phaseName={phase.name}
        onAdd={handleAddCustom}
      />
      <CartFab hasNavBelow={false} />
    </div>
  )
}
