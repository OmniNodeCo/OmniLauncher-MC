export function createOfferLauncherUrl(description: string) {
  return `omni://peer/offer/${description}`
}

export function createAnswerLauncherUrl(description: string) {
  return `omni://peer/answer/${description}`
}

export function createOfferAppUrl(description: string, inviter: string) {
  return `https://github.com/OmniNodeCo/OmniLauncher-MC/peer?description=${description}?type=offer?inviter=${inviter}`
}

export function createAnswerAppUrl(description: string, inviter: string) {
  return `https://github.com/OmniNodeCo/OmniLauncher-MC/peer?description=${description}?type=answer?inviter=${inviter}`
}
