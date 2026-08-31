import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import PublicGrade from './pages/PublicGrade'
import Report from './pages/Report'
import ScanProgress from './pages/ScanProgress'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__inner">
          <Link className="app-brand" to="/" aria-label="안심코드 홈">
            <span>안심코드</span>
          </Link>
          <span className="app-tagline">소스코드 안전 자가진단</span>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">인증이 아닌 자가점검 보조 도구입니다.</footer>
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
          <Route path="/report/:id" element={<Report />} />
          <Route path="/g/:slug" element={<PublicGrade />} />
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
