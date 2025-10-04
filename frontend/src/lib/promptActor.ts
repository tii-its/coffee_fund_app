// Centralized per-action actor credential prompt.
// Returns { actorId, pin } or throws if missing.
export interface ActorPromptResult { actorId: string; pin: string }

export function promptForActor(actionLabel: string): ActorPromptResult {
  const actorId = window.prompt(`Enter your user ID for ${actionLabel}`) || ''
  const pin = window.prompt(`Enter PIN to ${actionLabel}`) || ''
  if (!actorId || !pin) {
    throw new Error('PIN required')
  }
  return { actorId, pin }
}
