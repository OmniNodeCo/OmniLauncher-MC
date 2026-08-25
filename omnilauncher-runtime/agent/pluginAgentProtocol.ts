import type { LauncherAppPlugin } from '~/app'
import { kOmniSessionAuthorization, OmniLauncherAccountService } from '~/omnilauncherAccount'
import { AgentService, kResolvedAgentProvider } from './AgentService'
import {
  createAgentProtocolHandler,
  type AgentXmclAuthorizationRequest,
} from './providerProtocol'

export const pluginAgentProtocol: LauncherAppPlugin = (app) => {
  app.protocol.registerHandler('https', createAgentProtocolHandler(
    async () => {
      const service = await app.registry.getOrCreate(AgentService)
      return service[kResolvedAgentProvider]()
    },
    async (request?: AgentXmclAuthorizationRequest) => {
      const service = await app.registry.getOrCreate(OmniLauncherAccountService)
      return service[kOmniSessionAuthorization](request)
    },
  ))
}