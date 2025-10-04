import { describe, it, expect, vi, beforeEach } from 'vitest'
import api, { productsApi } from '@/api/client'

describe('Negative PIN path behavior', () => {
  let postSpy: any

  beforeEach(() => {
    vi.restoreAllMocks()
    postSpy = vi.spyOn(api, 'post')
  })

  it('fails when backend returns 401 for missing headers', async () => {
    postSpy.mockRejectedValueOnce({ response: { status: 401, data: { detail: 'Unauthorized' } } })
    await expect(productsApi.create({ name: 'X', price_cents: 100 }, undefined as any)).rejects.toMatchObject({ response: { status: 401 } })
    const call = postSpy.mock.calls[0]
    const config = call[2]
    expect(config.headers?.['x-actor-id']).toBeUndefined()
    expect(config.headers?.['x-actor-pin']).toBeUndefined()
  })

  it('succeeds when headers present', async () => {
    postSpy.mockResolvedValueOnce({ data: { id: 'p1', name: 'X', price_cents: 100, is_active: true, created_at: '' } })
    const result = await productsApi.create({ name: 'X', price_cents: 100 }, { actorId: 'u1', pin: '9999' })
    expect(result.data.id).toBe('p1')
    const call = postSpy.mock.calls[0]
    const config = call[2]
    expect(config.headers['x-actor-id']).toBe('u1')
    expect(config.headers['x-actor-pin']).toBe('9999')
  })
})
