import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '@/store'
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import TreasurerRoute from '@/components/TreasurerRoute'
import Dashboard from '@/pages/Dashboard'
import Kiosk from '@/pages/Kiosk'
import Treasurer from '@/pages/Treasurer'
import Users from '@/pages/Users'
import Products from '@/pages/Products'
import TreasurerRoute from '@/components/TreasurerRoute'

function App() {
  const { i18n } = useTranslation()
  const { language } = useAppStore()

  useEffect(() => {
    i18n.changeLanguage(language)
  }, [language, i18n])

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kiosk" element={<Kiosk />} />
          <Route path="/treasurer" element={
            <ProtectedRoute requirePin={true}>
              <Treasurer />
            </ProtectedRoute>
          } />
          <Route path="/users" element={<Users />} />
          <Route path="/products" element={
            <TreasurerRoute>
              <Products />
            </TreasurerRoute>
          } />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App