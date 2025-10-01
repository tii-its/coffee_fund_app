import React from 'react'
import PerActionPinModal from '@/components/PerActionPinModal'

export function usePerActionPin() {
  const [open, setOpen] = React.useState(false)
  const resolverRef = React.useRef<((value: { actorId: string; pin: string } | PromiseLike<{ actorId: string; pin: string }>) => void) | null>(null)

  const requestPin = React.useCallback(() => {
    setOpen(true)
    return new Promise<{ actorId: string; pin: string }>((resolve) => {
      resolverRef.current = resolve
    })
  }, [])

  const handleSubmit = (actorId: string, pin: string) => {
    resolverRef.current?.({ actorId, pin })
    resolverRef.current = null
  }

  const modal = (
    <PerActionPinModal
      isOpen={open}
      onClose={() => { setOpen(false); if (resolverRef.current) { resolverRef.current({ actorId: '', pin: '' }) } }}
      onSubmit={(actorId, pin) => { handleSubmit(actorId, pin); setOpen(false) }}
    />
  )

  return { requestPin, pinModal: modal }
}
