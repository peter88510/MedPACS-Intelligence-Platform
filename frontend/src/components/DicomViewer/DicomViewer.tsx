import { useEffect, useRef, useState } from 'react'
import { Enums, metaData, RenderingEngine, type Types } from '@cornerstonejs/core'
import { useAppContext } from '../../context/AppContext'
import { getInstanceFileUrl } from '../../api/instances'
import styles from './DicomViewer.module.css'

const RENDERING_ENGINE_ID = 'medpacs-engine'
const VIEWPORT_ID = 'medpacs-viewport'

// 一組量測在 canvas 座標下的 crest / trough 位置（CSS px，相對 viewport 左上）。
interface Marker {
  idx: number
  cx: number
  cy: number
  tx: number
  ty: number
}

export default function DicomViewer() {
  const { currentInstanceId, aiResult, aiOverlayVisible, aiOverlayOpacity } = useAppContext()
  const elementRef = useRef<HTMLDivElement>(null)
  // 渲染就緒的 viewport，供 overlay effect 做座標映射（indexToWorld → worldToCanvas）。
  const viewportRef = useRef<Types.IStackViewport | null>(null)
  // viewport 每次重建（切 instance / Phase 2 rebuild）後 +1，觸發 overlay 重新計算。
  const [viewportEpoch, setViewportEpoch] = useState(0)
  const [markers, setMarkers] = useState<Marker[]>([])

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

        // 公開 viewport 供 overlay effect 使用；bump epoch 觸發 marker 計算。
        viewportRef.current = viewport
        setViewportEpoch((e) => e + 1)
      } catch (err) {
        if (cancelled) return
        console.error('[DicomViewer] setStack / render failed:', err)
      }
    })()

    return () => {
      cancelled = true
      viewportRef.current = null
      renderingEngine?.destroy()
    }
  }, [currentInstanceId])

  // Overlay：把 measurements[].crest/trough（完整原圖像素座標）映射到 canvas 座標，
  // 畫向量 marker（peak/trough 圓點 + excursion 連線）。對齊 AI/visualization 的
  // excursion_info_display 語義（每組都畫）；不動原 DICOM、不用 mask PNG（HANDOFF §3.3.1）。
  // 隨 viewport 重建 / aiResult 變動 / 開關切換重算；camera/resize 時即時跟隨。
  //
  // ⚠️ 座標映射用 vtkImageData.indexToWorld（像素 index → world）→ worldToCanvas，
  // **不用** utilities.imageToWorldCoords —— 後者硬依賴 ImageOrientationPatient /
  // ImagePositionPatient，US DICOM 沒這兩個 tag（loader 回 rowCosines/columnCosines=null、
  // origin=undefined）會直接拋 TypeError、overlay 整片消失。indexToWorld 走 viewport
  // actor 的幾何（US 用預設平面：origin 0 / 單位 spacing），對 US 安全。
  useEffect(() => {
    const viewport = viewportRef.current
    const element = elementRef.current
    const measurements = aiResult?.result?.measurements ?? []

    if (!viewport || !element || !aiOverlayVisible || measurements.length === 0) {
      setMarkers([])
      return
    }

    const compute = () => {
      try {
        const imageData = viewport.getImageData()?.imageData
        const indexToWorld = imageData?.indexToWorld?.bind(imageData)
        if (!indexToWorld) {
          setMarkers([])
          return
        }
        // crest/trough 為 [x, y] = [column, row]；vtk index 為 [i, j, k]=[col, row, slice]。
        const toCanvas = (col: number, row: number) =>
          viewport.worldToCanvas(indexToWorld([col, row, 0]) as Types.Point3)
        const next: Marker[] = []
        for (const m of measurements) {
          const c = toCanvas(m.crest[0], m.crest[1])
          const t = toCanvas(m.trough[0], m.trough[1])
          next.push({ idx: m.batch_index, cx: c[0], cy: c[1], tx: t[0], ty: t[1] })
        }
        setMarkers(next)
      } catch (e) {
        console.warn('[DicomViewer] overlay compute failed:', e)
        setMarkers([])
      }
    }

    compute()
    const onChange = () => compute()
    element.addEventListener(Enums.Events.IMAGE_RENDERED, onChange)
    element.addEventListener(Enums.Events.CAMERA_MODIFIED, onChange)
    const ro = new ResizeObserver(() => compute())
    ro.observe(element)
    return () => {
      element.removeEventListener(Enums.Events.IMAGE_RENDERED, onChange)
      element.removeEventListener(Enums.Events.CAMERA_MODIFIED, onChange)
      ro.disconnect()
    }
  }, [viewportEpoch, aiResult, aiOverlayVisible])

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
      {markers.length > 0 && (
        <svg className={styles.overlay} style={{ opacity: aiOverlayOpacity }}>
          {markers.map((m, i) => (
            <g key={i}>
              <line x1={m.cx} y1={m.cy} x2={m.tx} y2={m.ty} className={styles.exLine} />
              <circle cx={m.cx} cy={m.cy} r={4} className={styles.crest} />
              <circle cx={m.tx} cy={m.ty} r={4} className={styles.trough} />
            </g>
          ))}
        </svg>
      )}
    </div>
  )
}
