import { init as csInit } from '@cornerstonejs/core'
import { init as dicomImageLoaderInit } from '@cornerstonejs/dicom-image-loader'

let initialized = false
let initPromise: Promise<void> | null = null

export async function initCornerstone(): Promise<void> {
  if (initialized) return
  if (initPromise) return initPromise

  initPromise = (async () => {
    await csInit()
    await dicomImageLoaderInit({
      maxWebWorkers: navigator.hardwareConcurrency || 1,
    })
    initialized = true
  })()

  try {
    await initPromise
  } finally {
    initPromise = null
  }
}

export function isCornerstoneInitialized(): boolean {
  return initialized
}
