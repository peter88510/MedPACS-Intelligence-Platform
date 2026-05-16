import { useEffect, useRef } from 'react'
import { Enums, metaData, RenderingEngine, type Types } from '@cornerstonejs/core'
import styles from './DicomViewer.module.css'

const API_BASE_URL = 'http://localhost:8000'
const RENDERING_ENGINE_ID = 'medpacs-engine'
const VIEWPORT_ID = 'medpacs-viewport'

interface DicomViewerProps {
  instanceId: number
}

export default function DicomViewer({ instanceId }: DicomViewerProps) {
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    let cancelled = false
    let renderingEngine: RenderingEngine | null = null
    const imageId = `wadouri:${API_BASE_URL}/instances/${instanceId}/file`

    const createEngineAndViewport = () => {
      const engine = new RenderingEngine(RENDERING_ENGINE_ID)
      engine.enableElement({
        viewportId: VIEWPORT_ID,
        type: Enums.ViewportType.STACK,
        element,
      })
      return {
        engine,
        viewport: engine.getViewport(VIEWPORT_ID) as Types.IStackViewport,
      }
    }

    ;(async () => {
      try {
        // Phase 1 — probe: load the image so Cornerstone's metaData provider
        // can answer rows/columns. The engine binds its internal scene state
        // (offscreen render window, camera intrinsics, VTK mapper bounds) to
        // the container's CSS-fallback aspect-ratio at this point; in-place
        // resize / resetCamera / second setStack can't fully refit it later
        // (verified in PROGRESS §4.4 Fix-1 / Fix-2 / Fix-3).
        let { engine, viewport } = createEngineAndViewport()
        renderingEngine = engine
        await viewport.setStack([imageId])
        if (cancelled) return

        let aspectRatio: string | null = null
        try {
          const planeModule = metaData.get('imagePlaneModule', imageId) as
            | { rows?: number; columns?: number }
            | undefined
          if (planeModule?.rows && planeModule?.columns) {
            aspectRatio = `${planeModule.columns} / ${planeModule.rows}`
          }
        } catch (e) {
          console.warn('[DicomViewer] imagePlaneModule fetch failed:', e)
        }
        if (!aspectRatio) {
          const imageData = viewport.getImageData?.()
          const dims = imageData?.dimensions
          if (dims && dims[0] > 0 && dims[1] > 0) {
            aspectRatio = `${dims[0]} / ${dims[1]}`
          }
        }
        if (aspectRatio) {
          element.style.aspectRatio = aspectRatio
        } else {
          console.warn(
            '[DicomViewer] Could not determine image dimensions, falling back to CSS default'
          )
        }

        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
        if (cancelled) return

        // Phase 2 — rebuild against the now-correctly-sized container. DICOM
        // is in Cornerstone's image cache so this is a cache hit, not a
        // network refetch.
        engine.destroy()
        renderingEngine = null
        const fresh = createEngineAndViewport()
        engine = fresh.engine
        viewport = fresh.viewport
        renderingEngine = engine

        await viewport.setStack([imageId])
        if (cancelled) return

        viewport.render()
      } catch (err) {
        if (cancelled) return
        console.error('[DicomViewer] setStack / render failed:', err)
      }
    })()

    return () => {
      cancelled = true
      renderingEngine?.destroy()
    }
  }, [instanceId])

  return <div ref={elementRef} className={styles.viewport} />
}
