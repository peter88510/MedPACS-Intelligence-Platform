import type { ReactNode } from 'react'
import styles from './Layout.module.css'

interface LayoutProps {
  topbar: ReactNode
  studyList: ReactNode
  viewer: ReactNode
  rightPanel: ReactNode
}

export default function Layout({ topbar, studyList, viewer, rightPanel }: LayoutProps) {
  return (
    <div className={styles.layout}>
      <header className={styles.topbar}>{topbar}</header>
      <aside className={styles.studyList}>{studyList}</aside>
      <main className={styles.viewer}>{viewer}</main>
      <aside className={styles.rightPanel}>{rightPanel}</aside>
    </div>
  )
}
