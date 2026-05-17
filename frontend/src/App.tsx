import { AppContextProvider } from './context/AppContext'
import Layout from './components/Layout/Layout'
import TopBar from './components/TopBar/TopBar'
import StudyList from './components/StudyList/StudyList'
import DicomViewer from './components/DicomViewer/DicomViewer'
import MetadataPanel from './components/MetadataPanel/MetadataPanel'
import AIPanel from './components/AIPanel/AIPanel'

function App() {
  return (
    <AppContextProvider>
      <Layout
        topbar={<TopBar />}
        studyList={<StudyList />}
        viewer={<DicomViewer />}
        rightPanel={
          <>
            <MetadataPanel />
            <AIPanel />
          </>
        }
      />
    </AppContextProvider>
  )
}

export default App
