import '@testing-library/jest-dom/vitest'
import { cleanup, configure } from '@testing-library/react'
import { afterEach } from 'vitest'

// Sin `globals` de Vitest, Testing Library no desmonta solo entre tests.
afterEach(cleanup)

// En el CI el primer render del dashboard completo puede pasar el segundo que findBy espera por
// defecto (PF-98); 3 s sigue por debajo de los 5 s que Vitest le da a cada test.
configure({ asyncUtilTimeout: 3000 })

// jsdom no tiene ResizeObserver y el ResponsiveContainer de Recharts lo necesita.
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
