import type { Logger } from '~/infra'
import {
  DEFAULT_OMNI_AI_API_BASE_URL,
  DEFAULT_OMNI_API_BASE_URL,
  DEFAULT_OMNI_SIGNALING_API_BASE_URL,
  resolveOmniLauncherApiEndpoints,
} from '@xmcl/runtime-api'

export const OMNI_API_BASE_URL_FLIGHT = 'omnilauncherApiBaseUrl'

/**
 * Backwards-compatible common-origin resolver for main-process consumers.
 */
export function resolveXmclApiBaseUrl(override: unknown, logger?: Pick<Logger, 'warn'>): string {
  return resolveOmniLauncherApiEndpoints(override, () => {
    logger?.warn('Ignoring invalid xmclApiUrl flight; using default OmniLauncher-MC API origins.')
  }).common
}

export {
  DEFAULT_OMNI_AI_API_BASE_URL,
  DEFAULT_OMNI_API_BASE_URL,
  DEFAULT_OMNI_SIGNALING_API_BASE_URL,
  resolveOmniLauncherApiEndpoints,
}
