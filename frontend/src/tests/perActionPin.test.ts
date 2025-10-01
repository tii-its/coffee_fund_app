import { describe, it, expect, vi, beforeEach } from 'vitest'
import api, { productsApi } from '@/api/client'

describe('per-action PIN headers', () => {
  let postSpy: any

  beforeEach(() => {
    // restore previous spies between tests
    vi.restoreAllMocks()
    postSpy = vi.spyOn(api, 'post')
  })

  it('injects headers when actor provided', async () => {
    postSpy.mockResolvedValue({ data: { id: 'p1', name: 'Coffee', price_cents: 100, is_active: true, created_at: '' } })
    await productsApi.create({ name: 'Coffee', price_cents: 100 }, { actorId: 'u1', pin: '1234' })
    expect(postSpy).toHaveBeenCalledTimes(1)
    const call = postSpy.mock.calls[0]
    expect(call[0]).toBe('/products/')
    const config = call[2]
    expect(config.headers['x-actor-id']).toBe('u1')
    expect(config.headers['x-actor-pin']).toBe('1234')
  })

  it('omits headers when actor not supplied', async () => {
    postSpy.mockResolvedValue({ data: { id: 'p2', name: 'Tea', price_cents: 90, is_active: true, created_at: '' } })
    // @ts-expect-error intentional missing actor param to see absence
    await productsApi.create({ name: 'Tea', price_cents: 90 }, undefined)
    const call = postSpy.mock.calls[0]
    const config = call[2]
    expect(config.headers?.['x-actor-id']).toBeUndefined()
    expect(config.headers?.['x-actor-pin']).toBeUndefined()
  })
})
