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
  const [aiResult, setAiResult] = useState<AIResultResponse | null>(null)
  const [loadingStudies, setLoadingStudies] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Guard against repeated auto-selection on remount (StrictMode dev double-invoke).
  const autoSelectedRef = useRef(false)

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
    setAiResult(null)
  }, [])

  const selectSeries = useCallback(
    async (seriesId: number) => {
      setCurrentSeriesId(seriesId)
      setCurrentInstanceId(null)
      setAiResult(null)
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
      setAiResult(null)
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
    try {
      await triggerSegmentation(currentInstanceId)
      const result = await getResult(currentInstanceId)
      setAiResult(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
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
