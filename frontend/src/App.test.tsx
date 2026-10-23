import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import App from './App'

test('renderiza el título y el botón', () => {
  render(<App />)

  expect(screen.getByRole('heading', { name: 'Personal Finance' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Empezar' })).toBeInTheDocument()
})
