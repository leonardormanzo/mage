const PREFIX = 'pedido-materiais:v1:'

export const STORAGE_KEYS = {
  workerName: `${PREFIX}worker-name`,
  orders: `${PREFIX}orders`,
  draft: `${PREFIX}draft`,
  orderSeq: `${PREFIX}order-seq`,
  connectivity: `${PREFIX}connectivity-online`,
} as const
