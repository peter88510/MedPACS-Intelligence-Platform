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

  if (loadingStudies) return <div className={styles.placeholder}>Loading studies…</div>
  if (studies.length === 0) return <div className={styles.placeholder}>No studies.</div>

  return (
    <ul className={styles.tree}>
      {studies.map((study) => {
        const isCurrentStudy = study.id === currentStudyId
        const series = seriesByStudy[study.id]
        return (
          <li key={study.id}>
            <button
              type="button"
              className={`${styles.row} ${styles.study} ${isCurrentStudy ? styles.active : ''}`}
              onClick={() => selectStudy(study.id)}
              title={study.study_instance_uid}
            >
              Study {study.id} <span className={styles.muted}>({study.modality ?? '?'})</span>
            </button>

            {isCurrentStudy && series && (
              <ul className={styles.sub}>
                {series.length === 0 && (
                  <li className={styles.empty}>(no series — legacy upload)</li>
                )}
                {series.map((s) => {
                  const isCurrentSeries = s.id === currentSeriesId
                  const instances = instancesBySeries[s.id]
                  return (
                    <li key={s.id}>
                      <button
                        type="button"
                        className={`${styles.row} ${styles.series} ${isCurrentSeries ? styles.active : ''}`}
                        onClick={() => selectSeries(s.id)}
                        title={s.series_instance_uid ?? ''}
                      >
                        Series {s.id}
                      </button>

                      {isCurrentSeries && instances && (
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
