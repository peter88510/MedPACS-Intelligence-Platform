import { useAppContext } from '../../context/AppContext'
import styles from './TopBar.module.css'

export default function TopBar() {
  const { currentStudyId, currentSeriesId, currentInstanceId } = useAppContext()

  return (
    <div className={styles.topbar}>
      <h1 className={styles.title}>MedPACS</h1>
      <div className={styles.selection}>
        <span>study: {currentStudyId ?? '—'}</span>
        <span>series: {currentSeriesId ?? '—'}</span>
        <span>instance: {currentInstanceId ?? '—'}</span>
      </div>
    </div>
  )
}
