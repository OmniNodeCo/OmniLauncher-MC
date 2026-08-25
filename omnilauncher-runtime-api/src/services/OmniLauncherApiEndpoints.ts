export const DEFAULT_OMNI_API_BASE_URL = 'https://api.xmcl.app'
export const DEFAULT_OMNI_AI_API_BASE_URL = 'https://ai.xmcl.app'
export const DEFAULT_OMNI_SIGNALING_API_BASE_URL = 'https://signaling.xmcl.app'

export interface OmniLauncherApiEndpoints {
  common: string
  ai: string
  signaling: string
}

export function resolveOmniLauncherApiEndpoints(
  override: unknown,
  onInvalid?: () => void,
): OmniLauncherApiEndpoints {
  const custom = validOrigin(override)
  if (custom) {
    return {
      common: custom,
      ai: custom,
      signaling: custom,
    }
  }
  if (typeof override === 'string' && override.trim()) onInvalid?.()
  return {
    common: DEFAULT_OMNI_API_BASE_URL,
    ai: DEFAULT_OMNI_AI_API_BASE_URL,
    signaling: DEFAULT_OMNI_SIGNALING_API_BASE_URL,
  }
}

function validOrigin(value: unknown): string | undefined {
  if (typeof value !== 'string' || !value.trim()) return undefined
  try {
    const url = new URL(value.trim())
    if (
      url.protocol !== 'https:' ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.pathname.replace(/\/+$/, '') !== ''
    ) return undefined
    return url.origin
  } catch {
    return undefined
  }
}
