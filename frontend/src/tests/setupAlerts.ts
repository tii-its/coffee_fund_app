// Global test setup: mock window.alert to avoid jsdom not implemented errors.
// This file is imported via Vitest setupFiles configuration.

if (!window.alert) {
  // @ts-ignore
  window.alert = (msg?: any) => { /* swallow alert in tests */ }
} else {
  // @ts-ignore
  window.alert = vi.fn()
}
