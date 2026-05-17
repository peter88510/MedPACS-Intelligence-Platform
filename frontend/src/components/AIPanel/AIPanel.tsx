import { useState } from 'react'
import { useAppContext } from '../../context/AppContext'
import styles from './AIPanel.module.css'

export default function AIPanel() {
  const { currentInstanceId, aiResult, runAi } = useAppContext()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onClick = async () => {
    if (currentInstanceId === null) return
    setBusy(true)
    setError(null)
    try {
      await runAi()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className={styles.panel}>
      <h2 className={styles.title}>AI Segmentation</h2>
      <button
        type="button"
        className={styles.runButton}
        onClick={onClick}
        disabled={currentInstanceId === null || busy}
      >
        {busy ? 'Running…' : 'Run AI'}
      </button>
      {error && <div className={styles.error}>Failed: {error}</div>}
      {aiResult && (
        <div className={styles.result}>
          <div className={styles.resultMeta}>
            <span>status: {aiResult.status}</span>
            <span>confidence: {aiResult.result.confidence}</span>
          </div>
          <pre className={styles.json}>{JSON.stringify(aiResult, null, 2)}</pre>
          <div className={styles.note}>
            Mask overlay 渲染待 Phase 3（真實 PNG mask endpoint 尚未實作；backend 目前回 stub
            字串）
          </div>
        </div>
      )}
    </section>
  )
}
