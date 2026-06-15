import { useState } from 'react'
import { useAppContext } from '../../context/AppContext'
import { ApiError } from '../../api/client'
import styles from './AIPanel.module.css'

// 把後端狀態碼轉成可讀提示（對齊 HANDOFF.md §3.3 的語義）。
function aiErrorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    switch (e.status) {
      case 422:
        return '無法判定量測類型：此機型未在對照表中（device model 未知）'
      case 501:
        return '此量測（thickness）尚未支援'
      case 503:
        return 'AI 引擎尚未安裝（dev 環境缺 paddle / weights）；非永久錯誤'
      case 404:
        return '尚未對此 instance 跑過 AI，或 instance 不存在'
      case 500:
        return '推論失敗（後端已留一筆 error 結果供查）'
      default:
        return e.message || `AI 請求失敗（HTTP ${e.status}）`
    }
  }
  return e instanceof Error ? e.message : String(e)
}

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
      setError(aiErrorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const measurements = aiResult?.result?.measurements ?? []

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
      {error && <div className={styles.error}>{error}</div>}
      {aiResult && (
        <div className={styles.result}>
          <div className={styles.headline}>
            <span className={styles.measurementType}>{aiResult.measurement_type}</span>
            <span className={styles.primaryValue}>
              {aiResult.primary_value ?? '—'}
              {aiResult.primary_unit ? ` ${aiResult.primary_unit}` : ''}
            </span>
          </div>
          <div className={styles.resultMeta}>
            <span>status: {aiResult.status}</span>
            <span>count: {measurements.length}</span>
          </div>
          {aiResult.status === 'error' && aiResult.error_message && (
            <div className={styles.error}>{aiResult.error_message}</div>
          )}
          {measurements.length > 0 && (
            <details className={styles.measurements}>
              <summary className={styles.summary}>
                {measurements.length} 筆量測（展開檢視）
              </summary>
              <div className={styles.measurementList}>
                {measurements.map((m) => (
                  <div key={m.batch_index} className={styles.measurementRow}>
                    <span>#{m.batch_index}</span>
                    <span>{m.excursion_cm ?? '—'} cm</span>
                    <span>
                      crest {m.crest[0]},{m.crest[1]}
                    </span>
                    <span>
                      trough {m.trough[0]},{m.trough[1]}
                    </span>
                  </div>
                ))}
              </div>
            </details>
          )}
          <details className={styles.rawJson}>
            <summary className={styles.summary}>raw JSON（debug）</summary>
            <pre className={styles.json}>{JSON.stringify(aiResult, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  )
}
