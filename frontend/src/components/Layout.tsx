import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { useAppStore } from '@/store'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const { language, setLanguage, sidebarOpen, setSidebarOpen } = useAppStore()

  const handleLanguageChange = (newLanguage: 'en' | 'de') => {
    setLanguage(newLanguage)
    i18n.changeLanguage(newLanguage)
  }

  const navigation = [
    { name: t('navigation.dashboard'), href: '/', icon: '🏠' },
    { name: t('navigation.kiosk'), href: '/kiosk', icon: '☕' },
    { name: t('navigation.treasurer'), href: '/treasurer', icon: '💼' },
    { name: t('navigation.users'), href: '/users', icon: '👥' },
    { name: t('navigation.products'), href: '/products', icon: '📦' },
  ]

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white shadow-lg transition-all duration-300`}>
        <div className="flex h-16 items-center justify-between px-4">
          <div className={`${sidebarOpen ? 'block' : 'hidden'}`}>
            <h1 className="text-xl font-bold text-gray-900">{t('app.title')}</h1>
            <p className="text-sm text-gray-500">{t('app.subtitle')}</p>
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <span className="text-xl">{sidebarOpen ? '←' : '→'}</span>
          </button>
        </div>
        
        <nav className="mt-8 px-4">
          {navigation.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              className={`flex items-center px-4 py-2 mt-2 rounded-lg transition-colors ${
                location.pathname === item.href
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="text-xl mr-3">{item.icon}</span>
              <span className={`${sidebarOpen ? 'block' : 'hidden'}`}>
                {item.name}
              </span>
            </Link>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">
                {navigation.find((nav) => nav.href === location.pathname)?.name || t('navigation.dashboard')}
              </h2>
            </div>
            <div className="flex items-center gap-4">
              {/* Language Switcher */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => handleLanguageChange('de')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    language === 'de'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  DE
                </button>
                <button
                  onClick={() => handleLanguageChange('en')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    language === 'en'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  EN
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout