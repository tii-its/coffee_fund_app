import { describe, it, expect, vi } from 'vitest'
import axios from 'axios'
import api from '@/api/client'

// We rely on axios interceptors; test they inject headers when actor set.

describe('Actor headers per action (no implicit injection)', () => {
  it('makes request without actor headers by default', async () => {
    const spy = vi.spyOn(axios.Axios.prototype, 'request').mockImplementation((config: any) => Promise.resolve({ data: {}, config }))
    await api.get('/test')
    const calledConfig = spy.mock.calls[0][0]
    expect(calledConfig.headers?.['x-actor-id']).toBeUndefined()
    expect(calledConfig.headers?.['x-actor-pin']).toBeUndefined()
    spy.mockRestore()
  })
})
