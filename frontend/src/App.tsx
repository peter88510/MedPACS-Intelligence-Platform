import DicomViewer from './components/DicomViewer/DicomViewer'

// TODO 工程師驗收時替換為 `POST /upload` 回傳的實際 instance_id。
// Stage C 用 hardcoded 常數撐住；下個 dispatch 接通 AppContext + StudyList 後移除。
const INSTANCE_ID = 1

function App() {
  return <DicomViewer instanceId={INSTANCE_ID} />
}

export default App
