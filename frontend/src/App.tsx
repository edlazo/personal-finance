import { Navigate, Route, Routes } from 'react-router'

import { RequireAuth } from '@/components/auth/RequireAuth'
import { DashboardLayout } from '@/layouts/DashboardLayout'
import { AuthProvider } from '@/lib/AuthProvider'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <DashboardLayout />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
