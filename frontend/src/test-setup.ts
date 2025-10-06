import { expect, vi } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

// Mock window.alert globally to silence jsdom not implemented errors during tests
// Use a jest-style spy (vitest) so tests can assert calls if needed.
// Always stub to a spy for consistency
// @ts-ignore
window.alert = vi.fn()