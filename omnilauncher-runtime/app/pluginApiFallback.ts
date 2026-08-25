import { kFlights } from '~/infra'
import { kOmniSessionAuthorization, OmniLauncherAccountService } from '~/omnilauncherAccount/OmniLauncherAccountService'
import type { LauncherAppPlugin } from './LauncherAppPlugin'
import type { Handler } from './LauncherProtocolHandler'
import { resolveOmniLauncherApiEndpoints } from './omnilauncherApiBaseUrl'

function setHeader(headers: Record<string, any>, name: string, value?: string) {
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === name.toLowerCase()) delete headers[key]
  }
  if (value) headers[name] = value
}

export const pluginApiFallback: LauncherAppPlugin = (app) => {
  const handler: Handler = async ({ request }) => {
    const flights = await app.registry.get(kFlights).catch((): Record<string, any> => ({}))
    const signalingOrigin = resolveOmniLauncherApiEndpoints(flights.omnilauncherApiBaseUrl).signaling
    const isAuthenticatedSignalingPath =
      request.url.pathname === '/v1/rtc/official' ||
      request.url.pathname.startsWith('/v1/multiplayer/')
    if (request.url.origin === signalingOrigin && isAuthenticatedSignalingPath) {
      setHeader(request.headers, 'Authorization')
      setHeader(request.headers, 'DPoP')
      const authorization = await app.registry
        .get(OmniLauncherAccountService)
        .then((service) =>
          service[kOmniSessionAuthorization]({
            method: request.method,
            url: request.url,
          }),
        )
        .catch(() => undefined)
      if (authorization) {
        const tokenType = authorization.tokenType === 'DPoP' ? 'DPoP' : 'Bearer'
        setHeader(
          request.headers,
          'Authorization',
          `${tokenType} ${authorization.accessToken}`,
        )
        setHeader(request.headers, 'DPoP', authorization.dpopProof)
      }
    } else if (request.url.host === 'api.curseforge.com') {
      request.headers['x-api-key'] = process.env.CURSEFORGE_API_KEY || ''
    }
  }
  app.protocol.registerHandler('https', handler)
}
