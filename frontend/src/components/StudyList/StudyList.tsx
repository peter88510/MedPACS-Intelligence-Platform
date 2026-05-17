import { useEffect, useState } from 'react'
import { useAppContext } from '../../context/AppContext'
import styles from './StudyList.module.css'

export default function StudyList() {
  const {
    studies,
    currentStudyId,
    currentSeriesId,
    currentInstanceId,
    seriesByStudy,
    instancesBySeries,
    selectStudy,
    selectSeries,
    selectInstance,
    loadingStudies,
  } = useAppContext()

  const [expandedStudies, setExpandedStudies] = useState<Set<number>>(() => new Set())
  const [expandedSeries, setExpandedSeries] = useState<Set<number>>(() => new Set())

  // Auto-expand whatever AppContext just selected (initial cascade + user-triggered).
  useEffect(() => {
    if (currentStudyId === null) return
    setExpandedStudies((prev) =>
      prev.has(currentStudyId) ? prev : new Set(prev).add(currentStudyId),
    )
  }, [currentStudyId])

  useEffect(() => {
    if (currentSeriesId === null) return
    setExpandedSeries((prev) =>
      prev.has(currentSeriesId) ? prev : new Set(prev).add(currentSeriesId),
    )
  }, [currentSeriesId])

  const toggleStudy = (id: number) => {
    if (expandedStudies.has(id)) {
      setExpandedStudies((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    } else {
      setExpandedStudies((prev) => new Set(prev).add(id))
      void selectStudy(id)
    }
  }

  const toggleSeries = (id: number) => {
    if (expandedSeries.has(id)) {
      setExpandedSeries((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    } else {
      setExpandedSeries((prev) => new Set(prev).add(id))
      void selectSeries(id)
    }
  }

  if (loadingStudies) return <div className={styles.placeholder}>Loading studies…</div>
  if (studies.length === 0) return <div className={styles.placeholder}>No studies.</div>

  return (
    <ul className={styles.tree}>
      {studies.map((study) => {
        const isExpanded = expandedStudies.has(study.id)
        const isCurrentStudy = study.id === currentStudyId
        const series = seriesByStudy[study.id]
        return (
          <li key={study.id}>
            <button
              type="button"
              className={`${styles.row} ${styles.study} ${isCurrentStudy ? styles.active : ''}`}
              onClick={() => toggleStudy(study.id)}
              title={study.study_instance_uid}
            >
              <span className={styles.icon}>{isExpanded ? '▼' : '▶'}</span>
              Study {study.id} <span className={styles.muted}>({study.modality ?? '?'})</span>
            </button>

            {isExpanded && series && (
              <ul className={styles.sub}>
                {series.length === 0 && (
                  <li className={styles.empty}>(no series — legacy upload)</li>
                )}
                {series.map((s) => {
                  const isSeriesExpanded = expandedSeries.has(s.id)
                  const isCurrentSeries = s.id === currentSeriesId
                  const instances = instancesBySeries[s.id]
                  return (
                    <li key={s.id}>
                      <button
                        type="button"
                        className={`${styles.row} ${styles.series} ${isCurrentSeries ? styles.active : ''}`}
                        onClick={() => toggleSeries(s.id)}
                        title={s.series_instance_uid ?? ''}
                      >
                        <span className={styles.icon}>{isSeriesExpanded ? '▼' : '▶'}</span>
                        Series {s.id}
                      </button>

                      {isSeriesExpanded && instances && (
                        <ul className={styles.sub}>
                          {instances.length === 0 && (
                            <li className={styles.empty}>(no instances)</li>
                          )}
                          {instances.map((inst) => {
                            const isCurrentInst = inst.id === currentInstanceId
                            return (
                              <li key={inst.id}>
                                <button
                                  type="button"
                                  className={`${styles.row} ${styles.instance} ${isCurrentInst ? styles.active : ''}`}
                                  onClick={() => selectInstance(inst.id)}
                                  title={inst.sop_instance_uid ?? ''}
                                >
                                  Instance {inst.id}
                                </button>
                              </li>
                            )
                          })}
                        </ul>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </li>
        )
      })}
    </ul>
  )
}
