import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import ScanProgress from './pages/ScanProgress'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="container">
      <header className="topbar">
        <Link to="/">
          <span className="brand">안심코드</span>
        </Link>
        <span className="tagline">소스코드 안전 자가진단 — 인증이 아닌 자가점검 보조</span>
      </header>
      {children}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/scan/:id" element={<ScanProgress />} />
          <Route
            path="*"
            element={
              <div className="card">
                페이지를 찾을 수 없습니다. <Link to="/">처음으로</Link>
              </div>
            }
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
