// Forma que devolverá `GET /users/me` (Identity, Sprint 3); hasta entonces, datos de ejemplo.
export type User = {
  name: string
  email: string
}

export const mockUser: User = { name: 'Elias Lazo', email: 'elias@example.com' }
