import { useEffect, useRef } from 'react'
import { Enums, metaData, RenderingEngine, type Types } from '@cornerstonejs/core'
import { useAppContext } from '../../context/AppContext'
import { getInstanceFileUrl } from '../../api/instances'
import styles from './DicomViewer.module.css'

const RENDERING_ENGINE_ID = 'medpacs-engine'
const VIEWPORT_ID = 'medpacs-viewport'

export default function DicomViewer() {
  const { currentInstanceId } = useAppContext()
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = elementRef.current
    if (!element || currentInstanceId === null) return

    let cancelled = false
    let renderingEngine: RenderingEngine | null = null
    const imageId = `wadouri:${getInstanceFileUrl(currentInstanceId)}`

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
        // Phase 1 — probe: load image so Cornerstone's metaData provider can
        // answer rows/columns. The engine binds its internal scene state to
        // the container's pre-layout size at this point; in-place resize /
        // resetCamera / second setStack alone can't fully refit it later
        // (verified in PROGRESS §4.4 Fix-1 / Fix-2 / Fix-3).
        let { engine, viewport } = createEngineAndViewport()
        renderingEngine = engine
        await viewport.setStack([imageId])
        if (cancelled) return

        // Read DICOM dimensions for diagnostic / future use. We intentionally
        // do NOT set `element.style.aspectRatio` here — codex's 2026-05-16
        // investigation showed it conflicts with the grid/height-100% chain
        // and squashes the viewport (see PROGRESS §4.4 Fix-J / commit fb656c6).
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

        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
        if (cancelled) return

        // Phase 2 — rebuild against the now-laid-out container. DICOM is in
        // Cornerstone's image cache so this is a cache hit, not a refetch.
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
  }, [currentInstanceId])

  if (currentInstanceId === null) {
    return (
      <div className={styles.viewer}>
        <div className={styles.empty}>No instance selected.</div>
      </div>
    )
  }

  return (
    <div className={styles.viewer}>
      <div ref={elementRef} className={styles.viewport} />
    </div>
  )
}
