import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { listSeriesForStudy, listStudies } from '../api/studies'
import { listInstancesForSeries } from '../api/series'
import { getResult, triggerSegmentation } from '../api/ai'
import type { AIResultResponse, Instance, Series, Study } from '../api/types'

interface AppContextValue {
  studies: Study[]
  currentStudyId: number | null
  currentSeriesId: number | null
  currentInstanceId: number | null
  aiResult: AIResultResponse | null

  // Series/instances cache populated on study/series selection so child
  // components (e.g. StudyList) don't refetch on every render.
  seriesByStudy: Record<number, Series[]>
  instancesBySeries: Record<number, Instance[]>

  selectStudy: (studyId: number) => Promise<void>
  selectSeries: (seriesId: number) => Promise<void>
  selectInstance: (instanceId: number) => void
  runAi: () => Promise<void>

  loadingStudies: boolean
  error: string | null
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppContextProvider({ children }: { children: ReactNode }) {
  const [studies, setStudies] = useState<Study[]>([])
  const [seriesByStudy, setSeriesByStudy] = useState<Record<number, Series[]>>({})
  const [instancesBySeries, setInstancesBySeries] = useState<Record<number, Instance[]>>({})
  const [currentStudyId, setCurrentStudyId] = useState<number | null>(null)
  const [currentSeriesId, setCurrentSeriesId] = useState<number | null>(null)
  const [currentInstanceId, setCurrentInstanceId] = useState<number | null>(null)
  // AI 結果依 instanceId 快取：切走再切回會還原、in-flight 推論結果落到正確那筆
  // （不會汙染當下顯示的其他 instance）。aiResult 由 currentInstanceId 推導。
  const [aiResultByInstance, setAiResultByInstance] = useState<Record<number, AIResultResponse>>({})
  const [loadingStudies, setLoadingStudies] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Guard against repeated auto-selection on remount (StrictMode dev double-invoke).
  const autoSelectedRef = useRef(false)
  // 記錄已嘗試自動載入 AI 結果的 instance，避免切回時對同一筆重複打 GET。
  const aiLoadAttemptedRef = useRef<Set<number>>(new Set())

  const fetchSeriesFor = useCallback(
    async (studyId: number): Promise<Series[]> => {
      const cached = seriesByStudy[studyId]
      if (cached) return cached
      const fetched = await listSeriesForStudy(studyId)
      setSeriesByStudy((prev) => ({ ...prev, [studyId]: fetched }))
      return fetched
    },
    [seriesByStudy],
  )

  const fetchInstancesFor = useCallback(
    async (seriesId: number): Promise<Instance[]> => {
      const cached = instancesBySeries[seriesId]
      if (cached) return cached
      const fetched = await listInstancesForSeries(seriesId)
      setInstancesBySeries((prev) => ({ ...prev, [seriesId]: fetched }))
      return fetched
    },
    [instancesBySeries],
  )

  const selectInstance = useCallback((instanceId: number) => {
    setCurrentInstanceId(instanceId)
    // 不清 AI 結果：依 instanceId 快取，aiResult 會跟著 currentInstanceId 推導。
  }, [])

  const selectSeries = useCallback(
    async (seriesId: number) => {
      setCurrentSeriesId(seriesId)
      setCurrentInstanceId(null)
      try {
        const instances = await fetchInstancesFor(seriesId)
        if (instances[0]) setCurrentInstanceId(instances[0].id)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      }
    },
    [fetchInstancesFor],
  )

  const selectStudy = useCallback(
    async (studyId: number) => {
      setCurrentStudyId(studyId)
      setCurrentSeriesId(null)
      setCurrentInstanceId(null)
      try {
        const series = await fetchSeriesFor(studyId)
        if (series[0]) await selectSeries(series[0].id)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      }
    },
    [fetchSeriesFor, selectSeries],
  )

  const runAi = useCallback(async () => {
    if (currentInstanceId === null) return
    // 抓當下 targetId：即使推論期間使用者切到別筆，結果也落到正確的那筆快取，
    // 不會汙染當下顯示。錯誤往上拋給呼叫端（AIPanel）做狀態碼分支提示。
    const targetId = currentInstanceId
    await triggerSegmentation(targetId)
    const result = await getResult(targetId)
    setAiResultByInstance((prev) => ({ ...prev, [targetId]: result }))
  }, [currentInstanceId])

  // 選到 instance 時自動載入既有 AI 結果（唯讀 GET /ai/result）：
  //   - DB 已跑過 → 填快取顯示；未跑過(404) → 忽略（正常情況）
  //   - 繞過 backend 重跑推論的問題、並讓持久化結果在切回/重開頁面時自動還原
  //   - 用 ref 記「已嘗試」確保每筆只自動打一次；想刷新走 Run AI（會重跑 segment）
  useEffect(() => {
    if (currentInstanceId === null) return
    if (aiLoadAttemptedRef.current.has(currentInstanceId)) return
    aiLoadAttemptedRef.current.add(currentInstanceId)
    const targetId = currentInstanceId
    let cancelled = false
    getResult(targetId)
      .then((r) => {
        if (!cancelled) setAiResultByInstance((prev) => ({ ...prev, [targetId]: r }))
      })
      .catch(() => {
        // 404 = 此 instance 尚未跑過 AI；其他錯誤亦靜默，不擋主 UI。
      })
    return () => {
      cancelled = true
    }
  }, [currentInstanceId])

  // Initial load: fetch studies, auto-select first one (cascades to series + instance).
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const fetched = await listStudies()
        if (cancelled) return
        setStudies(fetched)
        if (!autoSelectedRef.current && fetched[0]) {
          autoSelectedRef.current = true
          await selectStudy(fetched[0].id)
        }
      } catch (e) {
        if (cancelled) return
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        if (!cancelled) setLoadingStudies(false)
      }
    })()
    return () => {
      cancelled = true
    }
    // selectStudy intentionally omitted: we only want to run this on mount,
    // and selectStudy's identity churns when its dep maps grow.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 當前 instance 的 AI 結果（從快取推導；無則 null）。
  const aiResult =
    currentInstanceId !== null ? aiResultByInstance[currentInstanceId] ?? null : null

  const value = useMemo<AppContextValue>(
    () => ({
      studies,
      currentStudyId,
      currentSeriesId,
      currentInstanceId,
      aiResult,
      seriesByStudy,
      instancesBySeries,
      selectStudy,
      selectSeries,
      selectInstance,
      runAi,
      loadingStudies,
      error,
    }),
    [
      studies,
      currentStudyId,
      currentSeriesId,
      currentInstanceId,
      aiResult,
      seriesByStudy,
      instancesBySeries,
      selectStudy,
      selectSeries,
      selectInstance,
      runAi,
      loadingStudies,
      error,
    ],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used inside <AppContextProvider>')
  return ctx
}
