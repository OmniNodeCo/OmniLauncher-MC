/* eslint-disable no-template-curly-in-string */
import { config as dotenv } from 'dotenv'
import type { Configuration } from 'electron-builder'

dotenv()

export const config = {
  productName: 'OmniLauncher-MC',
  appId: 'com.omninodeco.omnilaunchermc',
  directories: {
    output: 'build/output',
    buildResources: 'build',
    app: '.',
  },
  protocols: {
    name: 'OmniLauncher-MC',
    schemes: ['omnilauncher'],
  },
  // assign publish for auto-updater
  publish: [{
    provider: 'github',
    owner: 'OmniNodeCo',
    repo: 'OmniLauncher-MC',
  }],
  files: [{
    from: 'dist',
    to: '.',
    filter: ['**/*.js', '**/*.ico', '**/*.png', '**/*.webp', '**/*.svg', '*.node', '*.dll', '**/*.html', '**/*.css', '**/*.woff2', '**/*.wasm'],
  }, {
    from: '.',
    to: '.',
    filter: 'package.json',
  }],
  extraResources: [{
    from: 'main/agent-documents',
    to: 'agent-documents',
    filter: ['**/*.md'],
  }],
  artifactName: 'OmniLauncher-MC-${version}-${platform}-${arch}.${ext}',
  appx: {
    displayName: 'OmniLauncher-MC',
    applicationId: 'OmniLauncherMC',
    identityName: 'OmniLauncherMC',
    backgroundColor: 'transparent',
    publisher: process.env.PUBLISHER,
    publisherDisplayName: 'OmniNodeCo',
    setBuildNumber: true,
  },
  dmg: {
    artifactName: 'OmniLauncher-MC-${version}-${arch}.${ext}',
    contents: [
      {
        x: 410,
        y: 150,
        type: 'link',
        path: '/Applications',
      },
      {
        x: 130,
        y: 150,
        type: 'file',
      },
    ],
  },
  mac: {
    icon: 'icons/dark@256x256.png',
    darkModeSupport: true,
    target: [
      {
        target: 'dmg',
        arch: ['arm64', 'x64'],
      },
    ],
    extendInfo: {
      NSMicrophoneUsageDescription: 'A Minecraft mod wants to access your microphone.',
      NSCameraUsageDescription: 'Please give us access to your camera',
      'com.apple.security.device.audio-input': true,
      'com.apple.security.device.camera': true,
    },
  },
  win: {
    certificateFile: undefined as string | undefined,
    publisherName: 'OmniNodeCo',
    icon: 'icons/dark.ico',
    electronLanguages: ['en-US'],
    target: [
      {
        target: 'zip',
        arch: [
          'x64',
          'ia32',
        ],
      },
      'appx',
    ],
  },
  linux: {
    executableName: 'omnilauncher-mc',
    maintainer: 'OmniNodeCo <179980294+OmniNodeCo@users.noreply.github.com>',
    vendor: 'OmniNodeCo',
    electronLanguages: ['en-US'],
    desktop: {
      MimeType: 'x-scheme-handler/omnilauncher',
      StartupWMClass: 'omnilauncher-mc',
    },
    category: 'Game',
    icon: 'icons/dark@256x256.png',
    artifactName: 'OmniLauncher-MC-${version}-${arch}.${ext}',
    target: [
      { target: 'deb', arch: ['x64', 'arm64'] },
      { target: 'rpm', arch: ['x64', 'arm64'] },
      { target: 'AppImage', arch: ['x64', 'arm64'] },
      { target: 'tar.xz', arch: ['x64', 'arm64'] },
      { target: 'pacman', arch: ['x64', 'arm64'] },
    ],
  },
  snap: {
    publish: [
      'github',
    ],
  },
} satisfies Configuration
