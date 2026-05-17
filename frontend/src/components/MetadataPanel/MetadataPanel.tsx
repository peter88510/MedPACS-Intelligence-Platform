import { useEffect, useState } from 'react'
import { getInstanceMetadata } from '../../api/instances'
import { useAppContext } from '../../context/AppContext'
import type { InstanceMetadata } from '../../api/types'
import styles from './MetadataPanel.module.css'

type State =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ok'; data: InstanceMetadata }
  | { kind: 'error'; message: string }

function stringify(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

export default function MetadataPanel() {
  const { currentInstanceId } = useAppContext()
  const [state, setState] = useState<State>({ kind: 'idle' })

  useEffect(() => {
    if (currentInstanceId === null) {
      setState({ kind: 'idle' })
      return
    }
    let cancelled = false
    setState({ kind: 'loading' })
    getInstanceMetadata(currentInstanceId)
      .then((data) => {
        if (!cancelled) setState({ kind: 'ok', data })
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setState({ kind: 'error', message: e instanceof Error ? e.message : String(e) })
        }
      })
    return () => {
      cancelled = true
    }
  }, [currentInstanceId])

  return (
    <section className={styles.panel}>
      <h2 className={styles.title}>Metadata</h2>
      {state.kind === 'idle' && (
        <div className={styles.placeholder}>Select an instance to view metadata.</div>
      )}
      {state.kind === 'loading' && <div className={styles.placeholder}>Loading…</div>}
      {state.kind === 'error' && (
        <div className={styles.error}>Failed: {state.message}</div>
      )}
      {state.kind === 'ok' && (
        <dl className={styles.list}>
          {Object.entries(state.data).map(([key, value]) => (
            <div key={key} className={styles.entry}>
              <dt className={styles.key}>{key}</dt>
              <dd className={styles.value}>{stringify(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  )
}
