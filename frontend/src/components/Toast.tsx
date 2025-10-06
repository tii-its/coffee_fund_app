import React, { createContext, useContext, useState, useCallback } from 'react'

interface ToastMessage { id: string; type?: 'success' | 'error' | 'info'; text: string; timeout?: number }
interface ToastContextValue { notify: (msg: Omit<ToastMessage, 'id'>) => void }
const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  const notify = useCallback((msg: Omit<ToastMessage, 'id'>) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    const timeout = msg.timeout ?? 3000
    const full: ToastMessage = { id, ...msg, timeout }
    setMessages((prev: ToastMessage[]) => [...prev, full])
    if (timeout > 0) {
      setTimeout(() => {
        setMessages((prev: ToastMessage[]) => prev.filter((m: ToastMessage) => m.id !== id))
      }, timeout)
    }
  }, [])

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
  {messages.map((m: ToastMessage) => (
          <div
            key={m.id}
            className={`px-4 py-2 rounded shadow text-white text-sm transition-opacity bg-${m.type === 'error' ? 'red' : m.type === 'success' ? 'green' : 'gray'}-600`}
          >
            {m.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
